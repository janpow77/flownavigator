"""Vendor API endpoints for Layer 0."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # noqa: F401

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.vendor import Vendor, VendorUser, VendorRole
from app.schemas.vendor import (
    VendorUpdate,
    VendorResponse,
    VendorUserCreate,
    VendorUserUpdate,
    VendorUserResponse,
    VendorUserListResponse,
)
from app.schemas.auth import Token

router = APIRouter()

vendor_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/vendor/login")


# Dependency: Get current vendor user
async def get_current_vendor_user(
    token: str = Depends(vendor_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> VendorUser:
    """Get current authenticated vendor user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Anmeldedaten",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    user_type = payload.get("type")

    if user_id is None or user_type != "vendor":
        raise credentials_exception

    result = await db.execute(select(VendorUser).where(VendorUser.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


# Dependency: Require vendor admin role
async def require_vendor_admin(
    current_user: VendorUser = Depends(get_current_vendor_user),
) -> VendorUser:
    """Require vendor_admin role."""
    if current_user.role != VendorRole.vendor_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur für Vendor-Administratoren",
        )
    return current_user


# Dependency: Require vendor_developer or above
async def require_vendor_developer(
    current_user: VendorUser = Depends(get_current_vendor_user),
) -> VendorUser:
    """Require vendor_developer or higher role."""
    allowed_roles = [
        VendorRole.vendor_admin,
        VendorRole.vendor_developer,
        VendorRole.vendor_qa,
    ]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur für Entwickler und QA",
        )
    return current_user


# Dependency: Require vendor_qa or admin
async def require_vendor_qa(
    current_user: VendorUser = Depends(get_current_vendor_user),
) -> VendorUser:
    """Require vendor_qa or admin role."""
    allowed_roles = [VendorRole.vendor_admin, VendorRole.vendor_qa]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur für QA und Administratoren",
        )
    return current_user


# Authentication
@router.post("/login", response_model=Token)
async def vendor_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate vendor user and return JWT token."""
    result = await db.execute(
        select(VendorUser).where(VendorUser.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige E-Mail oder Passwort",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Benutzer ist deaktiviert",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(
        data={"sub": user.id, "type": "vendor", "role": user.role.value}
    )

    return Token(
        access_token=access_token,
        user=VendorUserResponse.model_validate(user),  # type: ignore
    )


# Vendor CRUD
@router.get("", response_model=VendorResponse)
async def get_vendor(
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    """Get vendor information."""
    result = await db.execute(select(Vendor).where(Vendor.id == current_user.vendor_id))
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor nicht gefunden",
        )

    return VendorResponse.model_validate(vendor)


@router.put("", response_model=VendorResponse)
async def update_vendor(
    data: VendorUpdate,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    """Update vendor information (vendor_admin only)."""
    result = await db.execute(select(Vendor).where(Vendor.id == current_user.vendor_id))
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor nicht gefunden",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)

    await db.commit()
    await db.refresh(vendor)

    return VendorResponse.model_validate(vendor)


# Vendor Users CRUD
@router.get("/users", response_model=VendorUserListResponse)
async def list_vendor_users(
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> VendorUserListResponse:
    """List all vendor users."""
    result = await db.execute(
        select(VendorUser).where(VendorUser.vendor_id == current_user.vendor_id)
    )
    users = result.scalars().all()

    return VendorUserListResponse(
        users=[VendorUserResponse.model_validate(u) for u in users],
        total=len(users),
    )


@router.post(
    "/users", response_model=VendorUserResponse, status_code=status.HTTP_201_CREATED
)
async def create_vendor_user(
    data: VendorUserCreate,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> VendorUserResponse:
    """Create a new vendor user (vendor_admin only)."""
    # Check if email already exists
    result = await db.execute(select(VendorUser).where(VendorUser.email == data.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail ist bereits registriert",
        )

    user = VendorUser(
        id=str(uuid4()),
        vendor_id=current_user.vendor_id,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        first_name=data.first_name,
        last_name=data.last_name,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return VendorUserResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=VendorUserResponse)
async def get_vendor_user(
    user_id: str,
    current_user: VendorUser = Depends(get_current_vendor_user),
    db: AsyncSession = Depends(get_db),
) -> VendorUserResponse:
    """Get vendor user details."""
    result = await db.execute(
        select(VendorUser).where(
            VendorUser.id == user_id,
            VendorUser.vendor_id == current_user.vendor_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    return VendorUserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=VendorUserResponse)
async def update_vendor_user(
    user_id: str,
    data: VendorUserUpdate,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> VendorUserResponse:
    """Update vendor user (vendor_admin only)."""
    result = await db.execute(
        select(VendorUser).where(
            VendorUser.id == user_id,
            VendorUser.vendor_id == current_user.vendor_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return VendorUserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_vendor_user(
    user_id: str,
    current_user: VendorUser = Depends(require_vendor_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deactivate vendor user (vendor_admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eigener Benutzer kann nicht deaktiviert werden",
        )

    result = await db.execute(
        select(VendorUser).where(
            VendorUser.id == user_id,
            VendorUser.vendor_id == current_user.vendor_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    user.is_active = False
    await db.commit()
