from typing import Optional
from pydantic import BaseModel


class TenantContext(BaseModel):
    """
    Multi-tenant context scoping.
    Every database operation and agent invocation is scoped by tenant.
    For single-user deployments, a default tenant is used.
    """
    user_id: str = "default_user"
    org_id: str = "default_org"
    session_id: Optional[str] = None

    def scope_key(self) -> str:
        return f"{self.org_id}:{self.user_id}"


DEFAULT_TENANT = TenantContext()
