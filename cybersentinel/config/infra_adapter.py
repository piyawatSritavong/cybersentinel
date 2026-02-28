"""
Infrastructure Adapter — Sovereign Dependency Injection Layer

This module provides a unified interface for all infrastructure operations
(database, file storage, configuration). The core CyberSentinel system calls
Infra.db_execute(), Infra.save_file(), etc. instead of direct library calls.

To switch providers (Replit -> AWS -> self-hosted), change INFRA_PROVIDER
in the environment or config. The adapter auto-selects the correct backend.

Supported Providers:
  - REPLIT  : Replit Managed PostgreSQL + local filesystem
  - AWS     : Amazon RDS + S3 (requires boto3, AWS credentials)
  - LOCAL   : SQLite + local filesystem (development fallback)
"""

import os
import logging
from typing import Optional, Any, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

INFRA_PROVIDER = os.environ.get("INFRA_PROVIDER", "REPLIT").upper()


class BaseInfraAdapter:
    provider_name: str = "base"

    def get_database_url(self) -> str:
        raise NotImplementedError

    def db_execute(self, query: str, params: dict = None) -> Any:
        raise NotImplementedError

    def save_file(self, path: str, content: bytes, bucket: str = "default") -> str:
        raise NotImplementedError

    def read_file(self, path: str, bucket: str = "default") -> Optional[bytes]:
        raise NotImplementedError

    def delete_file(self, path: str, bucket: str = "default") -> bool:
        raise NotImplementedError

    def list_files(self, prefix: str = "", bucket: str = "default") -> List[str]:
        raise NotImplementedError

    def get_config(self) -> Dict[str, Any]:
        raise NotImplementedError


class ReplitAdapter(BaseInfraAdapter):
    """Replit-native infrastructure: Managed PostgreSQL + local filesystem."""

    provider_name = "REPLIT"

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL", "")
        self._storage_root = Path(os.environ.get("REPLIT_STORAGE_PATH", "data"))
        self._storage_root.mkdir(parents=True, exist_ok=True)

    def get_database_url(self) -> str:
        if not self._db_url:
            logger.warning("[INFRA:REPLIT] DATABASE_URL not set")
        return self._db_url

    def db_execute(self, query: str, params: dict = None) -> Any:
        from sqlalchemy import create_engine, text
        engine = create_engine(self.get_database_url())
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result

    def save_file(self, path: str, content: bytes, bucket: str = "default") -> str:
        target = self._storage_root / bucket / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        logger.info(f"[INFRA:REPLIT] Saved file: {target}")
        return str(target)

    def read_file(self, path: str, bucket: str = "default") -> Optional[bytes]:
        target = self._storage_root / bucket / path
        if target.exists():
            return target.read_bytes()
        return None

    def delete_file(self, path: str, bucket: str = "default") -> bool:
        target = self._storage_root / bucket / path
        if target.exists():
            target.unlink()
            return True
        return False

    def list_files(self, prefix: str = "", bucket: str = "default") -> List[str]:
        base = self._storage_root / bucket
        if not base.exists():
            return []
        return [str(p.relative_to(base)) for p in base.rglob(f"{prefix}*") if p.is_file()]

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "database": "Replit Managed PostgreSQL",
            "storage": str(self._storage_root),
            "db_connected": bool(self._db_url),
        }


class AWSAdapter(BaseInfraAdapter):
    """AWS infrastructure: RDS PostgreSQL + S3. Requires boto3 + AWS credentials."""

    provider_name = "AWS"

    def __init__(self):
        self._db_url = os.environ.get("AWS_RDS_URL", os.environ.get("DATABASE_URL", ""))
        self._s3_bucket = os.environ.get("AWS_S3_BUCKET", "cybersentinel-storage")
        self._s3_region = os.environ.get("AWS_REGION", "us-east-1")

    def get_database_url(self) -> str:
        return self._db_url

    def db_execute(self, query: str, params: dict = None) -> Any:
        from sqlalchemy import create_engine, text
        engine = create_engine(self.get_database_url())
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result

    def save_file(self, path: str, content: bytes, bucket: str = "default") -> str:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=self._s3_region)
            key = f"{bucket}/{path}"
            s3.put_object(Bucket=self._s3_bucket, Key=key, Body=content)
            logger.info(f"[INFRA:AWS] Uploaded to S3: s3://{self._s3_bucket}/{key}")
            return f"s3://{self._s3_bucket}/{key}"
        except ImportError:
            logger.error("[INFRA:AWS] boto3 not installed. Falling back to local storage.")
            return ReplitAdapter().save_file(path, content, bucket)

    def read_file(self, path: str, bucket: str = "default") -> Optional[bytes]:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=self._s3_region)
            key = f"{bucket}/{path}"
            obj = s3.get_object(Bucket=self._s3_bucket, Key=key)
            return obj["Body"].read()
        except Exception:
            return None

    def delete_file(self, path: str, bucket: str = "default") -> bool:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=self._s3_region)
            key = f"{bucket}/{path}"
            s3.delete_object(Bucket=self._s3_bucket, Key=key)
            return True
        except Exception:
            return False

    def list_files(self, prefix: str = "", bucket: str = "default") -> List[str]:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=self._s3_region)
            response = s3.list_objects_v2(Bucket=self._s3_bucket, Prefix=f"{bucket}/{prefix}")
            return [obj["Key"] for obj in response.get("Contents", [])]
        except Exception:
            return []

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "database": "Amazon RDS PostgreSQL",
            "storage": f"s3://{self._s3_bucket}",
            "region": self._s3_region,
            "db_connected": bool(self._db_url),
        }


class LocalAdapter(BaseInfraAdapter):
    """Local development: SQLite + local filesystem."""

    provider_name = "LOCAL"

    def __init__(self):
        self._db_path = Path("data/local.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_root = Path("data")

    def get_database_url(self) -> str:
        return f"sqlite:///{self._db_path}"

    def db_execute(self, query: str, params: dict = None) -> Any:
        from sqlalchemy import create_engine, text
        engine = create_engine(self.get_database_url())
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result

    def save_file(self, path: str, content: bytes, bucket: str = "default") -> str:
        target = self._storage_root / bucket / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)

    def read_file(self, path: str, bucket: str = "default") -> Optional[bytes]:
        target = self._storage_root / bucket / path
        return target.read_bytes() if target.exists() else None

    def delete_file(self, path: str, bucket: str = "default") -> bool:
        target = self._storage_root / bucket / path
        if target.exists():
            target.unlink()
            return True
        return False

    def list_files(self, prefix: str = "", bucket: str = "default") -> List[str]:
        base = self._storage_root / bucket
        if not base.exists():
            return []
        return [str(p.relative_to(base)) for p in base.rglob(f"{prefix}*") if p.is_file()]

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "database": f"SQLite ({self._db_path})",
            "storage": str(self._storage_root),
            "db_connected": True,
        }


_ADAPTERS = {
    "REPLIT": ReplitAdapter,
    "AWS": AWSAdapter,
    "LOCAL": LocalAdapter,
}


def _create_adapter() -> BaseInfraAdapter:
    adapter_cls = _ADAPTERS.get(INFRA_PROVIDER, ReplitAdapter)
    adapter = adapter_cls()
    logger.info(f"[INFRA] Initialized provider: {adapter.provider_name}")
    return adapter


Infra: BaseInfraAdapter = _create_adapter()
