import chromadb
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from pathlib import Path
from .config import settings
from .tenant import TenantContext, DEFAULT_TENANT
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Incident(Base):
    __tablename__ = 'incidents'
    id = Column(Integer, primary_key=True)
    alert_id = Column(String, unique=True, index=True, nullable=True)
    org_id = Column(String, index=True, default="default_org")
    user_id = Column(String, default="default_user")
    raw_log = Column(String)
    source_type = Column(String, nullable=True)
    risk_level = Column(String)
    category = Column(String)
    summary = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    alert_id = Column(String)
    org_id = Column(String, index=True, default="default_org")
    verdict = Column(String)
    is_correct = Column(Boolean)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class MemoryManager:

    def __init__(self):
        self.enabled = settings.enable_learning
        if not self.enabled:
            return

        from app.core.database import _embedding_fn

        self.vector_db_path = Path(
            __file__).parent.parent.parent / settings.vector_db_path
        os.makedirs(self.vector_db_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vector_db_path))

        self.cases_collection = self.chroma_client.get_or_create_collection(
            name="historical_cases", metadata={"hnsw:space": "cosine"},
            embedding_function=_embedding_fn)
        self.docs_collection = self.chroma_client.get_or_create_collection(
            name="playbooks_knowledge", metadata={"hnsw:space": "cosine"},
            embedding_function=_embedding_fn)

        db_url = settings.database_url or os.environ.get("DATABASE_URL", "")
        if db_url:
            self.engine = create_engine(db_url)
            try:
                with self.engine.connect() as conn:
                    logger.info("Connected to PostgreSQL (Replit Managed)")
                Base.metadata.create_all(self.engine)
                self.Session = sessionmaker(bind=self.engine)
                self._db_available = True
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                self._db_available = False
                self.Session = None
        else:
            logger.warning("DATABASE_URL not set. Running without SQL persistence.")
            self._db_available = False
            self.Session = None

    def log_incident(self, alert_id: str, raw_log: str, source_type: str,
                     tenant: TenantContext = DEFAULT_TENANT):
        if not self.enabled or not self._db_available:
            return
        session = self.Session()
        try:
            existing = session.query(Incident).filter(
                Incident.alert_id == alert_id).first()
            if not existing:
                incident = Incident(
                    alert_id=alert_id,
                    org_id=tenant.org_id,
                    user_id=tenant.user_id,
                    raw_log=raw_log,
                    source_type=source_type,
                    risk_level="Pending",
                    category="Uncategorized",
                    summary="Processing...")
                session.add(incident)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging incident: {e}")
        finally:
            session.close()

    def get_recent_incidents(self, limit: int = 5,
                             tenant: TenantContext = DEFAULT_TENANT):
        if not self.enabled or not self._db_available:
            return []
        session = self.Session()
        try:
            incidents = session.query(Incident).filter(
                Incident.org_id == tenant.org_id
            ).order_by(
                Incident.timestamp.desc()).limit(limit).all()
            return [{
                "alert_id": i.alert_id,
                "raw_log": i.raw_log,
                "source_type": i.source_type
            } for i in incidents]
        except Exception as e:
            logger.error(f"Error getting recent incidents: {e}")
            return []
        finally:
            session.close()

    def add_to_memory(self, alert_id: str, raw_log: str, verdict: str,
                      is_correct: bool, reason: str,
                      tenant: TenantContext = DEFAULT_TENANT):
        if not self.enabled:
            return

        if self._db_available:
            session = self.Session()
            try:
                new_feedback = Feedback(
                    alert_id=alert_id,
                    org_id=tenant.org_id,
                    verdict=verdict,
                    is_correct=is_correct,
                    reason=reason)
                session.add(new_feedback)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error adding feedback: {e}")
            finally:
                session.close()

        doc_content = f"Case: {raw_log}\nVerdict: {verdict}\nHuman Reason: {reason}"
        try:
            self.cases_collection.add(
                documents=[doc_content],
                metadatas=[{
                    "alert_id": alert_id,
                    "org_id": tenant.org_id,
                    "verdict": verdict,
                    "is_correct": is_correct
                }],
                ids=[f"{alert_id}_{datetime.datetime.utcnow().timestamp()}"])
        except Exception as e:
            logger.error(f"Error adding to vector memory: {e}")

    def get_similar_cases(self, log_query: str, n_results: int = 3,
                          tenant: TenantContext = DEFAULT_TENANT) -> list:
        if not self.enabled:
            return []
        try:
            where_filter = {"org_id": tenant.org_id} if tenant.org_id != "default_org" else None
            results = self.cases_collection.query(
                query_texts=[log_query],
                n_results=n_results,
                where=where_filter
            )
            similar_cases = []
            if results and results.get('documents'):
                for doc, dist in zip(results['documents'][0],
                                     results['distances'][0]):
                    if dist < 0.3:
                        similar_cases.append(doc)
            return similar_cases
        except Exception:
            return []

    def get_company_docs(self, log_query: str, n_results: int = 2,
                         tenant: TenantContext = DEFAULT_TENANT) -> list:
        if not self.enabled:
            return []
        try:
            results = self.docs_collection.query(query_texts=[log_query],
                                                 n_results=n_results)
            return results.get('documents', [[]])[0]
        except:
            return []

    def add_document(self, doc_id: str, text: str, metadata: dict):
        if not self.enabled:
            return
        self.docs_collection.add(documents=[text],
                                 metadatas=[metadata],
                                 ids=[doc_id])

    def save_incident(self, raw_log, analysis,
                      tenant: TenantContext = DEFAULT_TENANT):
        if not self.enabled or not self._db_available:
            return None
        session = self.Session()
        try:
            target_id = analysis.get('alert_id')
            existing_incident = session.query(Incident).filter(
                Incident.alert_id == target_id).first()

            if existing_incident:
                existing_incident.risk_level = analysis.get('risk_level', 'Pending')
                existing_incident.category = analysis.get('category', 'General')
                existing_incident.summary = analysis.get('summary', 'No summary')
                existing_incident.raw_log = raw_log
            else:
                new_incident = Incident(
                    alert_id=target_id,
                    org_id=tenant.org_id,
                    user_id=tenant.user_id,
                    raw_log=raw_log,
                    risk_level=analysis.get('risk_level', 'Pending'),
                    category=analysis.get('category', 'General'),
                    summary=analysis.get('summary', 'No summary'),
                    source_type=analysis.get('source_type', 'unknown'))
                session.add(new_incident)

            session.commit()
            return target_id
        except Exception as e:
            session.rollback()
            logger.error(f"Database Save Error: {e}")
            raise e
        finally:
            session.close()


memory = MemoryManager()
