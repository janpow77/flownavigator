"""Module schemas for Layer 0."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.module import ModuleStatus, DeploymentStatus


# Module Schemas
class ModuleBase(BaseModel):
    """Base module schema."""

    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=20, pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""

    dependencies: list[str] = []
    min_system_version: Optional[str] = None
    feature_flags: dict = {}


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = Field(
        None, min_length=1, max_length=20, pattern=r"^\d+\.\d+\.\d+$"
    )
    description: Optional[str] = None
    status: Optional[ModuleStatus] = None
    dependencies: Optional[list[str]] = None
    min_system_version: Optional[str] = None
    feature_flags: Optional[dict] = None


class ModuleResponse(BaseModel):
    """Schema for module response."""

    id: str
    name: str
    version: str
    description: Optional[str]
    status: ModuleStatus
    developed_by: Optional[str]
    released_at: Optional[datetime]
    dependencies: Optional[list[str]]
    min_system_version: Optional[str]
    feature_flags: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModuleListResponse(BaseModel):
    """Schema for listing modules."""

    modules: list[ModuleResponse]
    total: int


# Module Deployment Schemas
class ModuleDeploymentCreate(BaseModel):
    """Schema for creating a module deployment."""

    customer_id: str
    deployed_version: str = Field(..., min_length=1, max_length=20)


class ModuleDeploymentResponse(BaseModel):
    """Schema for module deployment response."""

    id: str
    module_id: str
    customer_id: str
    status: DeploymentStatus
    deployed_at: Optional[datetime]
    deployed_by: Optional[str]
    deployed_version: str
    previous_version: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ModuleDeploymentListResponse(BaseModel):
    """Schema for listing module deployments."""

    deployments: list[ModuleDeploymentResponse]
    total: int


# Release Note Schemas
class ReleaseNoteCreate(BaseModel):
    """Schema for creating a release note."""

    version: str = Field(..., min_length=1, max_length=20, pattern=r"^\d+\.\d+\.\d+$")
    title: str = Field(..., min_length=1, max_length=255)
    changes: list[str] = []
    breaking_changes: list[str] = []


class ReleaseNoteResponse(BaseModel):
    """Schema for release note response."""

    id: str
    module_id: str
    version: str
    title: str
    changes: Optional[list[str]]
    breaking_changes: Optional[list[str]]
    published_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ReleaseNoteListResponse(BaseModel):
    """Schema for listing release notes."""

    release_notes: list[ReleaseNoteResponse]
    total: int


# Module with deployments
class ModuleWithDeploymentsResponse(ModuleResponse):
    """Module response with deployment information."""

    deployments: list[ModuleDeploymentResponse] = []
    release_notes: list[ReleaseNoteResponse] = []
