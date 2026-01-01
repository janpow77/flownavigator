"""API router configuration."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.preferences import router as preferences_router
from app.api.audit_cases import router as audit_cases_router
from app.api.checklists import router as checklists_router
from app.api.document_box import router as document_box_router
from app.api.findings import router as findings_router
from app.api.audit_logs import router as audit_logs_router
from app.api.modules import router as modules_router
# Layer 0: Vendor & Development
from app.api.vendor import router as vendor_router
from app.api.customers import router as customers_router
from app.api.vendor_modules import router as vendor_modules_router
# Layer 1 & 2: Profiles
from app.api.profiles import router as profiles_router
# Layer Dashboard
from app.api.dashboard import router as dashboard_router
# History (Feature 7)
from app.api.history import router as history_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(preferences_router, tags=["Preferences"])
router.include_router(audit_cases_router, tags=["Audit Cases"])
router.include_router(checklists_router, tags=["Checklists"])
router.include_router(document_box_router, tags=["Document Box"])
router.include_router(findings_router, tags=["Findings"])
router.include_router(audit_logs_router, tags=["Audit History"])
router.include_router(modules_router, prefix="/modules", tags=["Module Converter"])
# Layer 0: Vendor APIs
router.include_router(vendor_router, prefix="/v1/vendor", tags=["Vendor"])
router.include_router(customers_router, prefix="/v1/customers", tags=["Customers"])
router.include_router(vendor_modules_router, prefix="/v1/modules", tags=["Vendor Modules"])
# Layer 1 & 2: Profiles
router.include_router(profiles_router, prefix="/v1", tags=["Profiles"])
# Layer Dashboard
router.include_router(dashboard_router, prefix="/v1/dashboard", tags=["Layer Dashboard"])
# History (Feature 7)
router.include_router(history_router, prefix="/v1/history", tags=["History"])
