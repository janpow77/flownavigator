"""Customers API endpoints for Layer 0."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.vendor import VendorUser, VendorRole
from app.models.customer import Customer, CustomerStatus, LicenseUsage, LicenseAlert
from app.models.tenant import Tenant
from app.api.vendor import get_current_vendor_user, require_vendor_admin
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    LicenseHistoryResponse,
    LicenseUsageResponse,
    LicenseAdjustRequest,
    LicenseAlertResponse,
    CustomerWithLicensesResponse,
)

router = APIRouter()


# Customers CRUD
@router.get("", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[CustomerStatus] = Query(None, alias="status"),
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerListResponse:
    """List all customers (vendor users)."""
    query = select(Customer).where(Customer.vendor_id == current_user.vendor_id)

    if status_filter:
        query = query.where(Customer.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get customers with pagination
    query = query.offset(skip).limit(limit).order_by(Customer.created_at.desc())
    result = await db.execute(query)
    customers = result.scalars().all()

    return CustomerListResponse(
        customers=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    """Create a new customer with tenant (vendor_admin only)."""
    # Check if contract number already exists
    result = await db.execute(
        select(Customer).where(Customer.contract_number == data.contract_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vertragsnummer existiert bereits",
        )

    # Create tenant first
    tenant = Tenant(
        id=str(uuid4()),
        name=data.tenant_name,
        type=data.tenant_type,
        status="active",
    )
    db.add(tenant)
    await db.flush()

    # Create customer
    customer = Customer(
        id=str(uuid4()),
        vendor_id=current_user.vendor_id,
        tenant_id=tenant.id,
        contract_number=data.contract_number,
        contract_start=data.contract_start,
        contract_end=data.contract_end,
        licensed_users=data.licensed_users,
        licensed_authorities=data.licensed_authorities,
        billing_contact=data.billing_contact,
        billing_email=data.billing_email,
        billing_address_street=data.billing_address_street,
        billing_address_city=data.billing_address_city,
        billing_address_postal_code=data.billing_address_postal_code,
        billing_address_country=data.billing_address_country,
        payment_method=data.payment_method,
        status=data.status,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerWithLicensesResponse)
async def get_customer(
    customer_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerWithLicensesResponse:
    """Get customer details with license information."""
    result = await db.execute(
        select(Customer)
        .options(
            selectinload(Customer.license_usages), selectinload(Customer.license_alerts)
        )
        .where(
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

    # Calculate current usage
    today = date.today()
    current_usage = next((u for u in customer.license_usages if u.date == today), None)

    current_active_users = current_usage.active_users if current_usage else 0
    current_active_authorities = (
        current_usage.active_authorities if current_usage else 0
    )

    user_percent = (
        (current_active_users / customer.licensed_users * 100)
        if customer.licensed_users > 0
        else 0
    )
    authority_percent = (
        (current_active_authorities / customer.licensed_authorities * 100)
        if customer.licensed_authorities > 0
        else 0
    )

    return CustomerWithLicensesResponse(
        **CustomerResponse.model_validate(customer).model_dump(),
        license_usages=[
            LicenseUsageResponse.model_validate(u)
            for u in customer.license_usages[-30:]
        ],
        license_alerts=[
            LicenseAlertResponse.model_validate(a)
            for a in customer.license_alerts
            if not a.acknowledged
        ],
        current_active_users=current_active_users,
        current_active_authorities=current_active_authorities,
        user_license_percent=round(user_percent, 1),
        authority_license_percent=round(authority_percent, 1),
    )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    """Update customer (vendor_admin only)."""
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

    update_data = data.model_dump(exclude_unset=True)

    # Check contract number uniqueness if changed
    if (
        "contract_number" in update_data
        and update_data["contract_number"] != customer.contract_number
    ):
        result = await db.execute(
            select(Customer).where(
                Customer.contract_number == update_data["contract_number"]
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vertragsnummer existiert bereits",
            )

    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)

    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_customer(
    customer_id: str,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Terminate customer (set status to terminated, vendor_admin only)."""
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

    customer.status = CustomerStatus.terminated
    await db.commit()


# License Management
@router.get("/{customer_id}/licenses", response_model=LicenseHistoryResponse)
async def get_license_history(
    customer_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> LicenseHistoryResponse:
    """Get license usage history for a customer."""
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

    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(LicenseUsage)
        .where(
            LicenseUsage.customer_id == customer_id,
            LicenseUsage.date >= since,
        )
        .order_by(LicenseUsage.date.desc())
    )
    usages = result.scalars().all()

    # Calculate current percentage
    today_usage = next((u for u in usages if u.date == date.today()), None)
    current_users = today_usage.active_users if today_usage else 0
    current_authorities = today_usage.active_authorities if today_usage else 0

    user_percent = (
        (current_users / customer.licensed_users * 100)
        if customer.licensed_users > 0
        else 0
    )
    authority_percent = (
        (current_authorities / customer.licensed_authorities * 100)
        if customer.licensed_authorities > 0
        else 0
    )

    return LicenseHistoryResponse(
        history=[LicenseUsageResponse.model_validate(u) for u in usages],
        licensed_users=customer.licensed_users,
        licensed_authorities=customer.licensed_authorities,
        current_user_percent=round(user_percent, 1),
        current_authority_percent=round(authority_percent, 1),
    )


@router.post("/{customer_id}/licenses/adjust", response_model=CustomerResponse)
async def adjust_licenses(
    customer_id: str,
    data: LicenseAdjustRequest,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    """Adjust customer license limits (vendor_admin only)."""
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

    if data.licensed_users is not None:
        customer.licensed_users = data.licensed_users

    if data.licensed_authorities is not None:
        customer.licensed_authorities = data.licensed_authorities

    await db.commit()
    await db.refresh(customer)

    return CustomerResponse.model_validate(customer)


# Authorities for customer
@router.get("/{customer_id}/authorities")
async def get_customer_authorities(
    customer_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all authorities (sub-tenants) for a customer."""
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

    # Get child tenants (authorities)
    result = await db.execute(
        select(Tenant).where(
            Tenant.parent_id == customer.tenant_id,
            Tenant.type == "authority",
        )
    )
    authorities = result.scalars().all()

    return {
        "authorities": [
            {
                "id": a.id,
                "name": a.name,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in authorities
        ],
        "total": len(authorities),
    }


# License Alerts
@router.get("/{customer_id}/alerts", response_model=list[LicenseAlertResponse])
async def get_license_alerts(
    customer_id: str,
    include_acknowledged: bool = Query(False),
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> list[LicenseAlertResponse]:
    """Get license alerts for a customer."""
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

    query = select(LicenseAlert).where(LicenseAlert.customer_id == customer_id)
    if not include_acknowledged:
        query = query.where(LicenseAlert.acknowledged == False)

    result = await db.execute(query.order_by(LicenseAlert.created_at.desc()))
    alerts = result.scalars().all()

    return [LicenseAlertResponse.model_validate(a) for a in alerts]


@router.post(
    "/{customer_id}/alerts/{alert_id}/acknowledge", response_model=LicenseAlertResponse
)
async def acknowledge_alert(
    customer_id: str,
    alert_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> LicenseAlertResponse:
    """Acknowledge a license alert."""
    result = await db.execute(
        select(LicenseAlert).where(
            LicenseAlert.id == alert_id,
            LicenseAlert.customer_id == customer_id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert nicht gefunden",
        )

    # Verify customer belongs to vendor
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.vendor_id == current_user.vendor_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kunde nicht gefunden",
        )

    alert.acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = current_user.id

    await db.commit()
    await db.refresh(alert)

    return LicenseAlertResponse.model_validate(alert)
