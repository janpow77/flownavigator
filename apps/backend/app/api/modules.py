"""Module Converter API Endpoints.

Provides REST API for:
- LLM Configuration management
- Module Template management
- Conversion job management
- GitHub Integration management
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.module_converter import (
    ConversionStatus,
    ConversionStep,
    GitHubIntegration,
    LLMConfiguration,
    ModuleConversionLog,
    ModuleTemplate,
)
from app.models.user import User
from app.services.module_service import ModuleConverterService
from app.services.llm import LLMService
from app.services.github_service import GitHubService


router = APIRouter()


# ==============================================================================
# LLM Configuration Endpoints
# ==============================================================================


@router.get("/llm-config", tags=["LLM Configuration"])
async def list_llm_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    is_active: bool | None = None,
) -> dict[str, Any]:
    """List all LLM configurations."""
    query = select(LLMConfiguration)
    if is_active is not None:
        query = query.where(LLMConfiguration.is_active == is_active)
    query = query.order_by(LLMConfiguration.priority.asc())

    result = await db.execute(query)
    configs = result.scalars().all()

    # Mask API keys
    items = []
    for config in configs:
        item = {
            "id": str(config.id),
            "name": config.name,
            "description": config.description,
            "provider": (
                config.provider.value
                if hasattr(config.provider, "value")
                else config.provider
            ),
            "model_name": config.model_name,
            "api_endpoint": config.api_endpoint,
            "api_key_preview": _mask_api_key(config.api_key_encrypted),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "priority": config.priority,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }
        items.append(item)

    return {"items": items, "total": len(items)}


@router.post("/llm-config", tags=["LLM Configuration"])
async def create_llm_config(
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new LLM configuration."""
    config = LLMConfiguration(
        name=data["name"],
        description=data.get("description"),
        provider=data["provider"],
        model_name=data["model_name"],
        api_endpoint=data.get("api_endpoint"),
        api_key_encrypted=data["api_key"],  # TODO: Encrypt
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 4096),
        top_p=data.get("top_p", 1.0),
        is_default=data.get("is_default", False),
        priority=data.get("priority", 100),
        requests_per_minute=data.get("requests_per_minute", 60),
        tokens_per_minute=data.get("tokens_per_minute", 100000),
        config=data.get("config", {}),
    )

    # If this is default, unset other defaults
    if config.is_default:
        await db.execute(
            select(LLMConfiguration).where(LLMConfiguration.is_default == True)
        )
        result = await db.execute(
            select(LLMConfiguration).where(LLMConfiguration.is_default == True)
        )
        for existing in result.scalars():
            existing.is_default = False

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return {"id": str(config.id), "message": "Configuration created"}


@router.get("/llm-config/{config_id}", tags=["LLM Configuration"])
async def get_llm_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get a specific LLM configuration."""
    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.id == str(config_id))
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return {
        "id": str(config.id),
        "name": config.name,
        "description": config.description,
        "provider": (
            config.provider.value
            if hasattr(config.provider, "value")
            else config.provider
        ),
        "model_name": config.model_name,
        "api_endpoint": config.api_endpoint,
        "api_key_preview": _mask_api_key(config.api_key_encrypted),
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "top_p": config.top_p,
        "is_active": config.is_active,
        "is_default": config.is_default,
        "priority": config.priority,
        "requests_per_minute": config.requests_per_minute,
        "tokens_per_minute": config.tokens_per_minute,
        "config": config.config,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }


@router.put("/llm-config/{config_id}", tags=["LLM Configuration"])
async def update_llm_config(
    config_id: UUID,
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update an LLM configuration."""
    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.id == str(config_id))
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Update fields
    for field in [
        "name",
        "description",
        "provider",
        "model_name",
        "api_endpoint",
        "temperature",
        "max_tokens",
        "top_p",
        "is_active",
        "is_default",
        "priority",
        "requests_per_minute",
        "tokens_per_minute",
        "config",
    ]:
        if field in data:
            setattr(config, field, data[field])

    if "api_key" in data and data["api_key"]:
        config.api_key_encrypted = data["api_key"]  # TODO: Encrypt

    await db.commit()
    return {"message": "Configuration updated"}


@router.delete("/llm-config/{config_id}", tags=["LLM Configuration"])
async def delete_llm_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete an LLM configuration."""
    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.id == str(config_id))
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    await db.delete(config)
    await db.commit()
    return {"message": "Configuration deleted"}


@router.post("/llm-config/{config_id}/test", tags=["LLM Configuration"])
async def test_llm_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Test an LLM configuration connection."""
    llm_service = LLMService(db)
    is_valid = await llm_service.test_connection(str(config_id))

    return {
        "is_valid": is_valid,
        "message": "Connection successful" if is_valid else "Connection failed",
    }


# ==============================================================================
# Module Template Endpoints
# ==============================================================================


@router.get("/module-templates", tags=["Module Templates"])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_public: bool = True,
    module_type: str | None = None,
    is_active: bool | None = True,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """List module templates."""
    query = select(ModuleTemplate)

    # Filter by tenant or public
    query = query.where(
        (ModuleTemplate.tenant_id == current_user.tenant_id)
        | (ModuleTemplate.is_public == True if include_public else False)
    )

    if module_type:
        query = query.where(ModuleTemplate.module_type == module_type)
    if is_active is not None:
        query = query.where(ModuleTemplate.is_active == is_active)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(ModuleTemplate.name).limit(limit).offset(offset)
    result = await db.execute(query)
    templates = result.scalars().all()

    items = [_template_to_dict(t) for t in templates]
    return {"items": items, "total": total}


@router.post("/module-templates", tags=["Module Templates"])
async def create_template(
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new module template."""
    template = ModuleTemplate(
        tenant_id=current_user.tenant_id,
        name=data["name"],
        display_name=data["display_name"],
        description=data.get("description"),
        version=data.get("version", "1.0.0"),
        module_type=data["module_type"],
        package_name=data["package_name"],
        source_spec=data.get("source_spec", {}),
        target_spec=data.get("target_spec", {}),
        conversion_rules=data.get("conversion_rules", {}),
        system_prompt=data.get("system_prompt"),
        conversion_prompt_template=data.get("conversion_prompt_template"),
        validation_schema=data.get("validation_schema", {}),
        include_patterns=data.get("include_patterns", []),
        exclude_patterns=data.get("exclude_patterns", ["node_modules", ".git"]),
        is_public=data.get("is_public", False),
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return {"id": str(template.id), "message": "Template created"}


@router.get("/module-templates/{template_id}", tags=["Module Templates"])
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get a specific module template."""
    result = await db.execute(
        select(ModuleTemplate).where(ModuleTemplate.id == str(template_id))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check access
    if template.tenant_id != current_user.tenant_id and not template.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return _template_to_dict(template, include_prompts=True)


@router.put("/module-templates/{template_id}", tags=["Module Templates"])
async def update_template(
    template_id: UUID,
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update a module template."""
    result = await db.execute(
        select(ModuleTemplate).where(ModuleTemplate.id == str(template_id))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    updatable = [
        "name",
        "display_name",
        "description",
        "version",
        "module_type",
        "package_name",
        "source_spec",
        "target_spec",
        "conversion_rules",
        "system_prompt",
        "conversion_prompt_template",
        "validation_schema",
        "include_patterns",
        "exclude_patterns",
        "is_active",
        "is_public",
    ]
    for field in updatable:
        if field in data:
            setattr(template, field, data[field])

    await db.commit()
    return {"message": "Template updated"}


@router.delete("/module-templates/{template_id}", tags=["Module Templates"])
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a module template."""
    result = await db.execute(
        select(ModuleTemplate).where(ModuleTemplate.id == str(template_id))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(template)
    await db.commit()
    return {"message": "Template deleted"}


# ==============================================================================
# Conversion Endpoints
# ==============================================================================


@router.post("/conversions", tags=["Conversions"])
async def start_conversion(
    data: dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Start a new module conversion."""
    service = ModuleConverterService(db)

    conversion = await service.create_conversion(
        template_id=data["template_id"],
        tenant_id=current_user.tenant_id,
        user_id=str(current_user.id),
        source_type=data.get("source_type", "upload"),
        source_url=data.get("source_url"),
        source_branch=data.get("source_branch"),
        input_data=data.get("input_data", {}),
        llm_config_id=data.get("llm_config_id"),
    )

    # Run conversion in background
    background_tasks.add_task(
        _run_conversion_background,
        str(conversion.id),
        data.get("github_integration_id"),
    )

    return {
        "id": str(conversion.id),
        "job_id": conversion.job_id,
        "status": conversion.status.value,
        "message": "Conversion started",
    }


async def _run_conversion_background(
    conversion_id: str,
    github_integration_id: str | None,
) -> None:
    """Run conversion in background."""
    from app.core.database import get_session_factory

    async with get_session_factory()() as db:
        service = ModuleConverterService(db)
        try:
            await service.execute_conversion(conversion_id, github_integration_id)
        except Exception as e:
            # Error is already logged and saved in the service
            pass


@router.get("/conversions", tags=["Conversions"])
async def list_conversions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: str | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """List conversion jobs."""
    query = select(ModuleConversionLog).where(
        ModuleConversionLog.tenant_id == current_user.tenant_id
    )

    if status:
        query = query.where(ModuleConversionLog.status == status)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(ModuleConversionLog.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    conversions = result.scalars().all()

    items = [_conversion_to_dict(c) for c in conversions]
    return {"items": items, "total": total}


@router.get("/conversions/{conversion_id}", tags=["Conversions"])
async def get_conversion(
    conversion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get conversion details."""
    result = await db.execute(
        select(ModuleConversionLog).where(ModuleConversionLog.id == str(conversion_id))
    )
    conversion = result.scalar_one_or_none()

    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")

    if conversion.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _conversion_to_dict(conversion, include_details=True)


@router.get("/conversions/{conversion_id}/steps", tags=["Conversions"])
async def get_conversion_steps(
    conversion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get conversion steps."""
    result = await db.execute(
        select(ConversionStep)
        .where(ConversionStep.conversion_log_id == str(conversion_id))
        .order_by(ConversionStep.step_number)
    )
    steps = result.scalars().all()

    items = []
    for step in steps:
        items.append(
            {
                "id": str(step.id),
                "step_number": step.step_number,
                "step_name": step.step_name,
                "step_type": step.step_type,
                "status": step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": (
                    step.completed_at.isoformat() if step.completed_at else None
                ),
                "duration_ms": step.duration_ms,
                "error_message": step.error_message,
                "llm_tokens": step.llm_tokens,
            }
        )

    return {"items": items}


@router.post("/conversions/{conversion_id}/cancel", tags=["Conversions"])
async def cancel_conversion(
    conversion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Cancel a running conversion."""
    service = ModuleConverterService(db)
    cancelled = await service.cancel_conversion(str(conversion_id))

    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Conversion cannot be cancelled",
        )

    return {"message": "Conversion cancelled"}


@router.post("/conversions/{conversion_id}/retry", tags=["Conversions"])
async def retry_conversion(
    conversion_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Retry a failed conversion."""
    result = await db.execute(
        select(ModuleConversionLog).where(ModuleConversionLog.id == str(conversion_id))
    )
    conversion = result.scalar_one_or_none()

    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")

    if conversion.status not in [ConversionStatus.FAILED, ConversionStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail="Only failed or cancelled conversions can be retried",
        )

    # Reset status
    conversion.status = ConversionStatus.PENDING
    conversion.error_message = None
    conversion.progress = 0
    await db.commit()

    # Run in background
    background_tasks.add_task(
        _run_conversion_background,
        str(conversion.id),
        None,
    )

    return {"message": "Conversion retry started"}


# ==============================================================================
# GitHub Integration Endpoints
# ==============================================================================


@router.get("/github-integrations", tags=["GitHub Integration"])
async def list_github_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List GitHub integrations."""
    query = select(GitHubIntegration).where(
        (GitHubIntegration.tenant_id == current_user.tenant_id)
        | (GitHubIntegration.tenant_id.is_(None))
    )
    query = query.where(GitHubIntegration.is_active == True)

    result = await db.execute(query)
    integrations = result.scalars().all()

    items = [_github_integration_to_dict(i) for i in integrations]
    return {"items": items, "total": len(items)}


@router.post("/github-integrations", tags=["GitHub Integration"])
async def create_github_integration(
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a GitHub integration."""
    integration = GitHubIntegration(
        tenant_id=current_user.tenant_id,
        name=data["name"],
        description=data.get("description"),
        access_token_encrypted=data["access_token"],  # TODO: Encrypt
        default_owner=data["default_owner"],
        default_repo=data["default_repo"],
        default_base_branch=data.get("default_base_branch", "main"),
        pr_title_template=data.get(
            "pr_title_template", "[Module Converter] {module_name} - {action}"
        ),
        pr_body_template=data.get("pr_body_template"),
        auto_merge=data.get("auto_merge", False),
        require_review=data.get("require_review", True),
        branch_prefix=data.get("branch_prefix", "module-converter/"),
        default_labels=data.get("default_labels", []),
        default_reviewers=data.get("default_reviewers", []),
        config=data.get("config", {}),
    )

    db.add(integration)
    await db.commit()
    await db.refresh(integration)

    return {"id": str(integration.id), "message": "Integration created"}


@router.get("/github-integrations/{integration_id}", tags=["GitHub Integration"])
async def get_github_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get a GitHub integration."""
    result = await db.execute(
        select(GitHubIntegration).where(GitHubIntegration.id == str(integration_id))
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return _github_integration_to_dict(integration, include_details=True)


@router.put("/github-integrations/{integration_id}", tags=["GitHub Integration"])
async def update_github_integration(
    integration_id: UUID,
    data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update a GitHub integration."""
    result = await db.execute(
        select(GitHubIntegration).where(GitHubIntegration.id == str(integration_id))
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if integration.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    updatable = [
        "name",
        "description",
        "default_owner",
        "default_repo",
        "default_base_branch",
        "pr_title_template",
        "pr_body_template",
        "auto_merge",
        "require_review",
        "branch_prefix",
        "default_labels",
        "default_reviewers",
        "is_active",
        "config",
    ]
    for field in updatable:
        if field in data:
            setattr(integration, field, data[field])

    if "access_token" in data and data["access_token"]:
        integration.access_token_encrypted = data["access_token"]

    await db.commit()
    return {"message": "Integration updated"}


@router.delete("/github-integrations/{integration_id}", tags=["GitHub Integration"])
async def delete_github_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a GitHub integration."""
    result = await db.execute(
        select(GitHubIntegration).where(GitHubIntegration.id == str(integration_id))
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if integration.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(integration)
    await db.commit()
    return {"message": "Integration deleted"}


@router.post(
    "/github-integrations/{integration_id}/validate", tags=["GitHub Integration"]
)
async def validate_github_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Validate a GitHub integration."""
    result = await db.execute(
        select(GitHubIntegration).where(GitHubIntegration.id == str(integration_id))
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Test connection
    github = GitHubService(
        access_token=integration.access_token_encrypted or "",
    )

    try:
        is_valid = await github.validate_token()
        integration.validation_status = "valid" if is_valid else "invalid"
        integration.last_validated_at = datetime.utcnow()
        await db.commit()

        return {
            "is_valid": is_valid,
            "message": "Connection successful" if is_valid else "Connection failed",
        }
    finally:
        await github.close()


@router.get("/github-integrations/{integration_id}/repos", tags=["GitHub Integration"])
async def list_github_repos(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List repositories for a GitHub integration."""
    result = await db.execute(
        select(GitHubIntegration).where(GitHubIntegration.id == str(integration_id))
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    github = GitHubService(
        access_token=integration.access_token_encrypted or "",
    )

    try:
        repos = await github.list_repositories()
        return {
            "items": [
                {
                    "name": r.name,
                    "full_name": r.full_name,
                    "default_branch": r.default_branch,
                    "private": r.private,
                    "url": r.url,
                }
                for r in repos
            ]
        }
    finally:
        await github.close()


# ==============================================================================
# Helper Functions
# ==============================================================================


def _mask_api_key(key: str | None) -> str:
    """Mask an API key for display."""
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def _template_to_dict(
    template: ModuleTemplate,
    include_prompts: bool = False,
) -> dict[str, Any]:
    """Convert template to dictionary."""
    result = {
        "id": str(template.id),
        "name": template.name,
        "display_name": template.display_name,
        "description": template.description,
        "version": template.version,
        "module_type": (
            template.module_type.value
            if hasattr(template.module_type, "value")
            else template.module_type
        ),
        "package_name": template.package_name,
        "is_active": template.is_active,
        "is_public": template.is_public,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }

    if include_prompts:
        result.update(
            {
                "source_spec": template.source_spec,
                "target_spec": template.target_spec,
                "conversion_rules": template.conversion_rules,
                "system_prompt": template.system_prompt,
                "conversion_prompt_template": template.conversion_prompt_template,
                "validation_schema": template.validation_schema,
                "include_patterns": template.include_patterns,
                "exclude_patterns": template.exclude_patterns,
            }
        )

    return result


def _conversion_to_dict(
    conversion: ModuleConversionLog,
    include_details: bool = False,
) -> dict[str, Any]:
    """Convert conversion log to dictionary."""
    result = {
        "id": str(conversion.id),
        "job_id": conversion.job_id,
        "template_id": str(conversion.template_id) if conversion.template_id else None,
        "status": (
            conversion.status.value
            if hasattr(conversion.status, "value")
            else conversion.status
        ),
        "progress": conversion.progress,
        "source_type": conversion.source_type,
        "source_url": conversion.source_url,
        "files_processed": conversion.files_processed,
        "files_converted": conversion.files_converted,
        "files_failed": conversion.files_failed,
        "tokens_used": conversion.tokens_used,
        "error_message": conversion.error_message,
        "staging_pr_url": conversion.staging_pr_url,
        "created_at": conversion.created_at.isoformat(),
        "started_at": (
            conversion.started_at.isoformat() if conversion.started_at else None
        ),
        "completed_at": (
            conversion.completed_at.isoformat() if conversion.completed_at else None
        ),
    }

    if include_details:
        result.update(
            {
                "input_data": conversion.input_data,
                "output_data": conversion.output_data,
                "llm_requests": conversion.llm_requests,
                "error_details": conversion.error_details,
                "result_artifacts": conversion.result_artifacts,
            }
        )

    return result


def _github_integration_to_dict(
    integration: GitHubIntegration,
    include_details: bool = False,
) -> dict[str, Any]:
    """Convert GitHub integration to dictionary."""
    result = {
        "id": str(integration.id),
        "name": integration.name,
        "description": integration.description,
        "default_owner": integration.default_owner,
        "default_repo": integration.default_repo,
        "default_base_branch": integration.default_base_branch,
        "token_preview": _mask_api_key(integration.access_token_encrypted),
        "is_active": integration.is_active,
        "validation_status": integration.validation_status,
        "last_validated_at": (
            integration.last_validated_at.isoformat()
            if integration.last_validated_at
            else None
        ),
        "created_at": integration.created_at.isoformat(),
    }

    if include_details:
        result.update(
            {
                "pr_title_template": integration.pr_title_template,
                "pr_body_template": integration.pr_body_template,
                "auto_merge": integration.auto_merge,
                "require_review": integration.require_review,
                "branch_prefix": integration.branch_prefix,
                "default_labels": integration.default_labels,
                "default_reviewers": integration.default_reviewers,
                "config": integration.config,
            }
        )

    return result
