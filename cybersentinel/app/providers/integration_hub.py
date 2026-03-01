import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class BaseIntegration(ABC):
    """Abstract base class for all external integrations."""

    name: str = "base"
    display_name: str = "Base Integration"
    category: str = "general"

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        pass

    def get_name(self) -> str:
        return self.name

    def get_category(self) -> str:
        return self.category

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "category": self.category,
            "configured": self.is_configured(),
        }


class SplunkIntegration(BaseIntegration):
    """Splunk SIEM integration wrapping existing splunk_client."""

    name = "splunk"
    display_name = "Splunk SIEM"
    category = "siem"

    def __init__(self):
        try:
            from app.core.config import settings
            self._url = settings.splunk_url
            self._token = settings.splunk_token
        except Exception:
            self._url = ""
            self._token = ""

    def is_configured(self) -> bool:
        return bool(
            self._url
            and self._token
            and self._token != "mock"
            and not self._url.startswith("https://mock-")
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "message": "Splunk not configured"}
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self._url}/services/server/info",
                headers={"Authorization": f"Bearer {self._token}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5):
                return {"success": True, "message": "Splunk connection successful"}
        except Exception as e:
            return {"success": False, "message": f"Splunk connection failed: {str(e)}"}


class JiraIntegration(BaseIntegration):
    """Jira ticketing integration wrapping existing jira_plugin."""

    name = "jira"
    display_name = "Jira"
    category = "ticketing"

    def __init__(self):
        try:
            from app.core.config import settings
            self._url = settings.jira_url
            self._token = settings.jira_token
        except Exception:
            self._url = ""
            self._token = ""

    def is_configured(self) -> bool:
        return bool(
            self._url
            and self._token
            and self._token != "mock"
            and not self._url.startswith("https://mock-")
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "message": "Jira not configured"}
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self._url}/rest/api/2/serverInfo",
                headers={"Authorization": f"Bearer {self._token}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5):
                return {"success": True, "message": "Jira connection successful"}
        except Exception as e:
            return {"success": False, "message": f"Jira connection failed: {str(e)}"}


class VirusTotalIntegration(BaseIntegration):
    """VirusTotal threat intel integration wrapping existing vt_client."""

    name = "virustotal"
    display_name = "VirusTotal"
    category = "threat_intel"

    def __init__(self):
        try:
            from app.core.config import settings
            self._api_key = settings.vt_api_key
        except Exception:
            self._api_key = ""

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key != "mock" and len(self._api_key) > 5)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "message": "VirusTotal not configured"}
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8",
                headers={"x-apikey": self._api_key},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10):
                return {"success": True, "message": "VirusTotal connection successful"}
        except Exception as e:
            return {"success": False, "message": f"VirusTotal connection failed: {str(e)}"}


class ClickUpIntegration(BaseIntegration):
    """ClickUp project management stub."""

    name = "clickup"
    display_name = "ClickUp"
    category = "ticketing"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 5)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "message": "ClickUp not configured"}
        return {"success": False, "message": "ClickUp integration not yet implemented"}


class NotionIntegration(BaseIntegration):
    """Notion workspace integration stub."""

    name = "notion"
    display_name = "Notion"
    category = "documentation"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 5)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "message": "Notion not configured"}
        return {"success": False, "message": "Notion integration not yet implemented"}


class HybridAnalysisIntegration(BaseIntegration):
    """Hybrid Analysis sandbox integration stub."""

    name = "hybrid_analysis"
    display_name = "Hybrid Analysis"
    category = "threat_intel"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 5)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "message": "Hybrid Analysis not configured"}
        return {"success": False, "message": "Hybrid Analysis integration not yet implemented"}


class IntegrationHub:
    """Registry that lists all integrations, their status, and allows testing."""

    def __init__(self):
        self._integrations: Dict[str, BaseIntegration] = {}
        self._register_defaults()

    def _register_defaults(self):
        for cls in [
            SplunkIntegration,
            JiraIntegration,
            VirusTotalIntegration,
            ClickUpIntegration,
            NotionIntegration,
            HybridAnalysisIntegration,
        ]:
            try:
                instance = cls()
                self._integrations[instance.name] = instance
            except Exception as e:
                logger.error(f"[HUB] Failed to register {cls.__name__}: {e}")

    def register(self, integration: BaseIntegration) -> None:
        self._integrations[integration.name] = integration
        logger.info(f"[HUB] Registered integration: {integration.display_name}")

    def get(self, name: str) -> BaseIntegration:
        integration = self._integrations.get(name)
        if not integration:
            raise ValueError(f"Unknown integration: {name}")
        return integration

    def list_all(self) -> List[Dict[str, Any]]:
        return [integ.get_status() for integ in self._integrations.values()]

    def test_integration(self, name: str) -> Dict[str, Any]:
        try:
            integration = self.get(name)
            result = integration.test_connection()
            result["integration"] = name
            return result
        except ValueError as e:
            return {"success": False, "message": str(e), "integration": name}
        except Exception as e:
            return {"success": False, "message": f"Test failed: {str(e)}", "integration": name}

    def get_status(self) -> Dict[str, Any]:
        all_integrations = self.list_all()
        configured_count = sum(1 for i in all_integrations if i.get("configured"))
        return {
            "total": len(all_integrations),
            "configured": configured_count,
            "integrations": all_integrations,
        }
