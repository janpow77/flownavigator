"""Profile API endpoints for Layer 1 and Layer 2."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.profile import CoordinationBodyProfile, AuthorityProfile
from app.api.auth import get_current_user
from app.api.vendor import get_current_vendor_user
from app.models.vendor import VendorUser
from app.schemas.profile import (
    CBProfileCreate,
    CBProfileUpdate,
    CBProfileResponse,
    AuthorityProfileCreate,
    AuthorityProfileUpdate,
    AuthorityProfileResponse,
    AuthorityProfileWithBranding,
)

router = APIRouter()


# Helper: Check user access to tenant
async def check_tenant_access(
    tenant_id: str,
    user: User,
    db: AsyncSession,
    require_admin: bool = False,
) -> Tenant:
    """Check if user has access to the tenant."""
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant nicht gefunden",
        )

    # Check if user belongs to this tenant or is system_admin
    if user.role != "system_admin" and user.tenant_id != tenant_id:
        # Check if user's tenant is parent
        if tenant.parent_id != user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kein Zugriff auf diesen Tenant",
            )

    # Check admin role if required
    if require_admin and user.role not in ["system_admin", "group_admin", "authority_head"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administratorrechte erforderlich",
        )

    return tenant


# Coordination Body Profile Endpoints
@router.get("/tenants/{tenant_id}/profile", response_model=CBProfileResponse)
async def get_cb_profile(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CBProfileResponse:
    """Get Coordination Body profile."""
    await check_tenant_access(tenant_id, current_user, db)

    result = await db.execute(
        select(CoordinationBodyProfile).where(
            CoordinationBodyProfile.tenant_id == tenant_id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil nicht gefunden",
        )

    return CBProfileResponse.model_validate(profile)


@router.put("/tenants/{tenant_id}/profile", response_model=CBProfileResponse)
async def update_cb_profile(
    tenant_id: str,
    data: CBProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CBProfileResponse:
    """Update Coordination Body profile (group_admin only)."""
    await check_tenant_access(tenant_id, current_user, db, require_admin=True)

    result = await db.execute(
        select(CoordinationBodyProfile).where(
            CoordinationBodyProfile.tenant_id == tenant_id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil nicht gefunden",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return CBProfileResponse.model_validate(profile)


@router.post("/tenants/{tenant_id}/profile", response_model=CBProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_cb_profile(
    tenant_id: str,
    data: CBProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CBProfileResponse:
    """Create Coordination Body profile (group_admin only)."""
    await check_tenant_access(tenant_id, current_user, db, require_admin=True)

    # Check if profile already exists
    result = await db.execute(
        select(CoordinationBodyProfile).where(
            CoordinationBodyProfile.tenant_id == tenant_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profil existiert bereits",
        )

    profile = CoordinationBodyProfile(
        id=str(uuid4()),
        tenant_id=tenant_id,
        **data.model_dump(),
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return CBProfileResponse.model_validate(profile)


@router.post("/tenants/{tenant_id}/profile/logo")
async def upload_cb_logo(
    tenant_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload logo for Coordination Body profile."""
    await check_tenant_access(tenant_id, current_user, db, require_admin=True)

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/svg+xml", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nur Bilder (JPEG, PNG, SVG, WebP) erlaubt",
        )

    # For now, just return a placeholder URL
    # In production, this would upload to S3/GCS/etc.
    logo_url = f"/uploads/logos/{tenant_id}/{file.filename}"

    result = await db.execute(
        select(CoordinationBodyProfile).where(
            CoordinationBodyProfile.tenant_id == tenant_id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil nicht gefunden",
        )

    profile.logo_url = logo_url
    await db.commit()

    return {"logo_url": logo_url}


# Authority Profile Endpoints
@router.get("/authorities/{tenant_id}/profile", response_model=AuthorityProfileWithBranding)
async def get_authority_profile(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthorityProfileWithBranding:
    """Get Authority profile with effective branding."""
    await check_tenant_access(tenant_id, current_user, db)

    result = await db.execute(
        select(AuthorityProfile)
        .options(selectinload(AuthorityProfile.tenant).selectinload(Tenant.parent))
        .where(AuthorityProfile.tenant_id == tenant_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil nicht gefunden",
        )

    response_data = AuthorityProfileResponse.model_validate(profile).model_dump()
    response_data["effective_branding"] = profile.get_effective_branding()

    return AuthorityProfileWithBranding(**response_data)


@router.put("/authorities/{tenant_id}/profile", response_model=AuthorityProfileResponse)
async def update_authority_profile(
    tenant_id: str,
    data: AuthorityProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthorityProfileResponse:
    """Update Authority profile (authority_head only)."""
    await check_tenant_access(tenant_id, current_user, db, require_admin=True)

    result = await db.execute(
        select(AuthorityProfile).where(AuthorityProfile.tenant_id == tenant_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil nicht gefunden",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return AuthorityProfileResponse.model_validate(profile)


@router.post("/authorities/{tenant_id}/profile", response_model=AuthorityProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_authority_profile(
    tenant_id: str,
    data: AuthorityProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthorityProfileResponse:
    """Create Authority profile."""
    await check_tenant_access(tenant_id, current_user, db, require_admin=True)

    # Check if profile already exists
    result = await db.execute(
        select(AuthorityProfile).where(AuthorityProfile.tenant_id == tenant_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profil existiert bereits",
        )

    profile = AuthorityProfile(
        id=str(uuid4()),
        tenant_id=tenant_id,
        **data.model_dump(),
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return AuthorityProfileResponse.model_validate(profile)


# Vendor Admin: Manage all profiles
@router.get("/admin/profiles/cb", response_model=list[CBProfileResponse])
async def list_all_cb_profiles(
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> list[CBProfileResponse]:
    """List all Coordination Body profiles (vendor only)."""
    result = await db.execute(select(CoordinationBodyProfile))
    profiles = result.scalars().all()

    return [CBProfileResponse.model_validate(p) for p in profiles]


@router.put("/admin/profiles/cb/{profile_id}", response_model=CBProfileResponse)
async def admin_update_cb_profile(
    profile_id: str,
    data: CBProfileUpdate,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> CBProfileResponse:
    """Update any CB profile (vendor_admin only)."""
    from app.api.vendor import require_vendor_admin
    await require_vendor_admin(current_user)

    result = await db.execute(
        select(CoordinationBodyProfile).where(CoordinationBodyProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil nicht gefunden",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return CBProfileResponse.model_validate(profile)
