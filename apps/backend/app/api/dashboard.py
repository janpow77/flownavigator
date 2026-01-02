"""Dashboard API endpoints for Layer Dashboard."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.vendor import Vendor, VendorUser
from app.models.customer import Customer, LicenseUsage
from app.models.audit_case import AuditCase
from app.api.auth import get_current_user
from app.api.vendor import get_current_vendor_user
from app.schemas.dashboard import (
    VendorSummary,
    CustomerSummary,
    AuthoritySummary,
    LayerDashboardResponse,
    CustomerDetailResponse,
    AuthorityDetailResponse,
)

router = APIRouter()


async def get_customer_summary(customer: Customer, db: AsyncSession) -> CustomerSummary:
    """Build customer summary with calculated fields."""
    # Get tenant name
    result = await db.execute(select(Tenant).where(Tenant.id == customer.tenant_id))
    tenant = result.scalar_one_or_none()
    tenant_name = tenant.name if tenant else f"Tenant {customer.tenant_id[:8]}"

    # Count authorities (child tenants)
    result = await db.execute(
        select(func.count(Tenant.id)).where(
            Tenant.parent_id == customer.tenant_id,
            Tenant.type == "authority",
        )
    )
    authority_count = result.scalar() or 0

    # Get today's license usage
    today = date.today()
    result = await db.execute(
        select(LicenseUsage).where(
            LicenseUsage.customer_id == customer.id,
            LicenseUsage.date == today,
        )
    )
    usage = result.scalar_one_or_none()
    active_users = usage.active_users if usage else 0
    active_authorities = usage.active_authorities if usage else 0

    license_percent = (
        (active_users / customer.licensed_users * 100)
        if customer.licensed_users > 0
        else 0
    )
    authority_percent = (
        (active_authorities / customer.licensed_authorities * 100)
        if customer.licensed_authorities > 0
        else 0
    )

    return CustomerSummary(
        id=customer.id,
        name=tenant_name,
        tenant_id=customer.tenant_id,
        contract_number=customer.contract_number,
        licensed_users=customer.licensed_users,
        active_users=active_users,
        licensed_authorities=customer.licensed_authorities,
        active_authorities=active_authorities,
        license_percent=round(license_percent, 1),
        authority_percent=round(authority_percent, 1),
        authority_count=authority_count,
        status=customer.status,
    )


async def get_authority_summary(tenant: Tenant, db: AsyncSession) -> AuthoritySummary:
    """Build authority summary."""
    # Count users
    result = await db.execute(
        select(func.count(User.id)).where(
            User.tenant_id == tenant.id,
            User.is_active == True,
        )
    )
    user_count = result.scalar() or 0

    # Count active cases
    result = await db.execute(
        select(func.count(AuditCase.id)).where(
            AuditCase.tenant_id == tenant.id,
            AuditCase.status.in_(["draft", "in_progress", "review"]),
        )
    )
    active_cases = result.scalar() or 0

    # Get authority head
    result = await db.execute(
        select(User).where(
            User.tenant_id == tenant.id,
            User.role == "authority_head",
            User.is_active == True,
        )
    )
    head = result.scalar_one_or_none()
    authority_head = head.full_name if head else None

    return AuthoritySummary(
        id=tenant.id,
        name=tenant.name,
        user_count=user_count,
        active_cases=active_cases,
        authority_head=authority_head,
        status=tenant.status,
    )


# Vendor Layer Dashboard
@router.get("/layers", response_model=LayerDashboardResponse)
async def get_layer_dashboard(
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> LayerDashboardResponse:
    """Get layer dashboard for vendor (AC-4.1.1: vendor_admin sees all customers)."""
    # Get vendor info
    result = await db.execute(select(Vendor).where(Vendor.id == current_user.vendor_id))
    vendor = result.scalar_one_or_none()

    # Get all customers for this vendor
    result = await db.execute(
        select(Customer).where(Customer.vendor_id == current_user.vendor_id)
    )
    customers = result.scalars().all()

    # Build customer summaries
    customer_summaries = []
    total_licenses = 0
    total_users = 0

    for customer in customers:
        summary = await get_customer_summary(customer, db)
        customer_summaries.append(summary)
        total_licenses += customer.licensed_users
        total_users += summary.active_users

    # Count active modules
    from app.models.module import Module, ModuleStatus

    result = await db.execute(
        select(func.count(Module.id)).where(Module.status == ModuleStatus.released)
    )
    active_modules = result.scalar() or 0

    vendor_summary = None
    if vendor:
        vendor_summary = VendorSummary(
            id=vendor.id,
            name=vendor.name,
            total_customers=len(customers),
            total_licenses=total_licenses,
            total_users=total_users,
            active_modules=active_modules,
        )

    return LayerDashboardResponse(
        vendor=vendor_summary,
        total_customers=len(customers),
        total_licenses=total_licenses,
        total_users=total_users,
        customers=customer_summaries,
    )


# User Layer Dashboard (for group_admin and authority_head)
@router.get("/my-dashboard", response_model=LayerDashboardResponse)
async def get_my_layer_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LayerDashboardResponse:
    """Get layer dashboard based on user's role.

    AC-4.1.2: group_admin sees only own customer
    AC-4.1.3: authority_head sees only own authority
    """
    # Get user's tenant
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant nicht gefunden",
        )

    customer_summaries = []

    if current_user.role in ["system_admin", "group_admin"]:
        # Get customer for this tenant
        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant.id)
        )
        customer = result.scalar_one_or_none()

        if customer:
            summary = await get_customer_summary(customer, db)
            customer_summaries.append(summary)

    elif current_user.role == "authority_head":
        # Get parent tenant's customer
        if tenant.parent_id:
            result = await db.execute(
                select(Customer).where(Customer.tenant_id == tenant.parent_id)
            )
            customer = result.scalar_one_or_none()

            if customer:
                summary = await get_customer_summary(customer, db)
                # Filter to only show this authority
                authority_summary = await get_authority_summary(tenant, db)
                summary.authorities = [authority_summary]
                customer_summaries.append(summary)

    total_licenses = sum(c.licensed_users for c in customer_summaries)
    total_users = sum(c.active_users for c in customer_summaries)

    return LayerDashboardResponse(
        total_customers=len(customer_summaries),
        total_licenses=total_licenses,
        total_users=total_users,
        customers=customer_summaries,
    )


# Customer Detail (Drill-down)
@router.get("/layers/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer_detail(
    customer_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerDetailResponse:
    """Get detailed customer view with authorities (AC-4.1.4: Drill-Down)."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.vendor_id == current_user.vendor_id,
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kunde nicht gefunden",
        )

    customer_summary = await get_customer_summary(customer, db)

    # Get authorities
    result = await db.execute(
        select(Tenant).where(
            Tenant.parent_id == customer.tenant_id,
            Tenant.type == "authority",
        )
    )
    authority_tenants = result.scalars().all()

    authority_summaries = []
    for auth_tenant in authority_tenants:
        summary = await get_authority_summary(auth_tenant, db)
        authority_summaries.append(summary)

    # Get license trend (last 30 days)
    since = date.today() - timedelta(days=30)
    result = await db.execute(
        select(LicenseUsage)
        .where(
            LicenseUsage.customer_id == customer_id,
            LicenseUsage.date >= since,
        )
        .order_by(LicenseUsage.date)
    )
    usages = result.scalars().all()

    license_trend = [
        {
            "date": u.date.isoformat(),
            "users": u.active_users,
            "authorities": u.active_authorities,
        }
        for u in usages
    ]

    return CustomerDetailResponse(
        customer=customer_summary,
        authorities=authority_summaries,
        license_trend=license_trend,
    )


# Authority Detail
@router.get(
    "/layers/{customer_id}/authorities/{authority_id}",
    response_model=AuthorityDetailResponse,
)
async def get_authority_detail(
    customer_id: str,
    authority_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> AuthorityDetailResponse:
    """Get detailed authority view."""
    # Verify customer access
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.vendor_id == current_user.vendor_id,
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kunde nicht gefunden",
        )

    # Get authority tenant
    result = await db.execute(
        select(Tenant).where(
            Tenant.id == authority_id,
            Tenant.parent_id == customer.tenant_id,
        )
    )
    authority_tenant = result.scalar_one_or_none()

    if not authority_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Behörde nicht gefunden",
        )

    authority_summary = await get_authority_summary(authority_tenant, db)

    # Get users
    result = await db.execute(
        select(User).where(
            User.tenant_id == authority_id,
            User.is_active == True,
        )
    )
    users = result.scalars().all()

    user_list = [
        {
            "id": u.id,
            "name": u.full_name,
            "email": u.email,
            "role": u.role,
            "last_login": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]

    # Get recent cases
    result = await db.execute(
        select(AuditCase)
        .where(AuditCase.tenant_id == authority_id)
        .order_by(AuditCase.updated_at.desc())
        .limit(10)
    )
    cases = result.scalars().all()

    recent_cases = [
        {
            "id": c.id,
            "case_number": c.case_number,
            "project_name": c.project_name,
            "status": c.status,
            "updated_at": c.updated_at.isoformat(),
        }
        for c in cases
    ]

    # Count active checklists and pending findings
    from app.models.audit_case import AuditCaseChecklist, AuditCaseFinding

    result = await db.execute(
        select(func.count(AuditCaseChecklist.id))
        .join(AuditCase, AuditCase.id == AuditCaseChecklist.audit_case_id)
        .where(
            AuditCase.tenant_id == authority_id,
            AuditCaseChecklist.status == "in_progress",
        )
    )
    active_checklists = result.scalar() or 0

    result = await db.execute(
        select(func.count(AuditCaseFinding.id))
        .join(AuditCase, AuditCase.id == AuditCaseFinding.audit_case_id)
        .where(
            AuditCase.tenant_id == authority_id,
            AuditCaseFinding.status == "draft",
        )
    )
    pending_findings = result.scalar() or 0

    return AuthorityDetailResponse(
        authority=authority_summary,
        users=user_list,
        recent_cases=recent_cases,
        active_checklists=active_checklists,
        pending_findings=pending_findings,
    )
