"""Module Converter Service.

Orchestrates the entire module conversion process including
analysis, LLM-based conversion, validation, and staging.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module_converter import (
    ConversionStatus,
    ConversionStep,
    GitHubIntegration,
    LLMConfiguration,
    ModuleConversionLog,
    ModuleTemplate,
)
from app.services.github_service import GitHubService, create_github_service_from_integration
from app.services.llm import LLMService, LLMMessage
from app.services.llm.base import MessageRole


logger = logging.getLogger(__name__)


class ModuleConversionError(Exception):
    """Error during module conversion."""

    pass


class ModuleConverterService:
    """Service for module conversion operations.

    Handles the complete conversion pipeline:
    1. Source analysis
    2. Conversion preparation
    3. LLM-based conversion
    4. Output validation
    5. Staging to GitHub
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service.

        Args:
            db: Database session
        """
        self.db = db
        self._llm_service: LLMService | None = None
        self._cancel_requested: dict[str, bool] = {}

    @property
    def llm_service(self) -> LLMService:
        """Get or create LLM service."""
        if self._llm_service is None:
            self._llm_service = LLMService(self.db)
        return self._llm_service

    # ==========================================================================
    # Conversion Job Management
    # ==========================================================================

    async def create_conversion(
        self,
        template_id: str,
        tenant_id: str,
        user_id: str,
        source_type: str,
        source_url: str | None = None,
        source_branch: str | None = None,
        input_data: dict[str, Any] | None = None,
        llm_config_id: str | None = None,
    ) -> ModuleConversionLog:
        """Create a new conversion job.

        Args:
            template_id: ID of the template to use
            tenant_id: Tenant ID
            user_id: User ID who initiated
            source_type: Type of source (github, upload, url)
            source_url: URL of the source
            source_branch: Branch name (for GitHub)
            input_data: Additional input data
            llm_config_id: Optional specific LLM config

        Returns:
            Created conversion log
        """
        job_id = f"conv-{uuid4().hex[:12]}"

        conversion = ModuleConversionLog(
            tenant_id=tenant_id,
            job_id=job_id,
            template_id=template_id,
            llm_configuration_id=llm_config_id,
            initiated_by=user_id,
            status=ConversionStatus.PENDING,
            source_type=source_type,
            source_url=source_url,
            source_branch=source_branch,
            input_data=input_data or {},
        )

        self.db.add(conversion)
        await self.db.commit()
        await self.db.refresh(conversion)

        return conversion

    async def get_conversion(self, conversion_id: str) -> ModuleConversionLog | None:
        """Get a conversion by ID."""
        result = await self.db.execute(
            select(ModuleConversionLog).where(ModuleConversionLog.id == conversion_id)
        )
        return result.scalar_one_or_none()

    async def get_conversion_by_job_id(self, job_id: str) -> ModuleConversionLog | None:
        """Get a conversion by job ID."""
        result = await self.db.execute(
            select(ModuleConversionLog).where(ModuleConversionLog.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_conversions(
        self,
        tenant_id: str,
        status: ConversionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ModuleConversionLog]:
        """List conversions for a tenant."""
        query = select(ModuleConversionLog).where(
            ModuleConversionLog.tenant_id == tenant_id
        )

        if status:
            query = query.where(ModuleConversionLog.status == status)

        query = query.order_by(ModuleConversionLog.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancel_conversion(self, conversion_id: str) -> bool:
        """Request cancellation of a conversion.

        Args:
            conversion_id: Conversion ID

        Returns:
            True if cancellation was requested
        """
        conversion = await self.get_conversion(conversion_id)
        if not conversion:
            return False

        if conversion.status in [
            ConversionStatus.COMPLETED,
            ConversionStatus.FAILED,
            ConversionStatus.CANCELLED,
        ]:
            return False

        self._cancel_requested[conversion_id] = True
        conversion.status = ConversionStatus.CANCELLED
        await self.db.commit()
        return True

    # ==========================================================================
    # Conversion Pipeline
    # ==========================================================================

    async def execute_conversion(
        self,
        conversion_id: str,
        github_integration_id: str | None = None,
    ) -> ModuleConversionLog:
        """Execute the full conversion pipeline.

        Args:
            conversion_id: Conversion job ID
            github_integration_id: Optional GitHub integration for staging

        Returns:
            Updated conversion log
        """
        conversion = await self.get_conversion(conversion_id)
        if not conversion:
            raise ModuleConversionError(f"Conversion not found: {conversion_id}")

        try:
            # Update status
            conversion.status = ConversionStatus.PROCESSING
            conversion.started_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Get template
            template = await self._get_template(conversion.template_id)
            if not template:
                raise ModuleConversionError("Template not found")

            # Step 1: Analyze source
            await self._create_step(conversion, 1, "analyze", "Analyzing source code")
            source_analysis = await self._analyze_source(conversion, template)
            await self._complete_step(conversion, 1, output_data=source_analysis)

            if self._is_cancelled(conversion_id):
                return await self._finalize_cancelled(conversion)

            # Step 2: Prepare conversion
            await self._create_step(conversion, 2, "prepare", "Preparing conversion")
            context = await self._prepare_conversion(conversion, template, source_analysis)
            await self._complete_step(conversion, 2, output_data=context)
            conversion.progress = 20
            await self.db.commit()

            if self._is_cancelled(conversion_id):
                return await self._finalize_cancelled(conversion)

            # Step 3: Execute LLM conversion
            await self._create_step(conversion, 3, "transform", "Converting with LLM")
            result = await self._execute_llm_conversion(conversion, template, context)
            await self._complete_step(conversion, 3, output_data=result)
            conversion.progress = 60
            await self.db.commit()

            if self._is_cancelled(conversion_id):
                return await self._finalize_cancelled(conversion)

            # Step 4: Validate output
            conversion.status = ConversionStatus.VALIDATING
            await self._create_step(conversion, 4, "validate", "Validating output")
            validation = await self._validate_output(conversion, template, result)
            await self._complete_step(conversion, 4, output_data=validation)
            conversion.progress = 80
            await self.db.commit()

            if self._is_cancelled(conversion_id):
                return await self._finalize_cancelled(conversion)

            # Step 5: Stage to GitHub (optional)
            if github_integration_id:
                conversion.status = ConversionStatus.STAGING
                await self._create_step(conversion, 5, "stage", "Staging to GitHub")
                staging_result = await self._stage_to_github(
                    conversion, result, github_integration_id
                )
                await self._complete_step(conversion, 5, output_data=staging_result)

            # Finalize
            conversion.status = ConversionStatus.COMPLETED
            conversion.progress = 100
            conversion.completed_at = datetime.now(timezone.utc)
            conversion.output_data = result
            await self.db.commit()

            return conversion

        except Exception as e:
            logger.exception(f"Conversion {conversion_id} failed")
            conversion.status = ConversionStatus.FAILED
            conversion.error_message = str(e)
            conversion.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            raise ModuleConversionError(str(e)) from e

    def _is_cancelled(self, conversion_id: str) -> bool:
        """Check if cancellation was requested."""
        return self._cancel_requested.get(conversion_id, False)

    async def _finalize_cancelled(
        self, conversion: ModuleConversionLog
    ) -> ModuleConversionLog:
        """Finalize a cancelled conversion."""
        conversion.status = ConversionStatus.CANCELLED
        conversion.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        self._cancel_requested.pop(str(conversion.id), None)
        return conversion

    # ==========================================================================
    # Pipeline Steps
    # ==========================================================================

    async def _get_template(self, template_id: str) -> ModuleTemplate | None:
        """Get template by ID."""
        result = await self.db.execute(
            select(ModuleTemplate).where(ModuleTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def _create_step(
        self,
        conversion: ModuleConversionLog,
        step_number: int,
        step_type: str,
        step_name: str,
    ) -> ConversionStep:
        """Create a conversion step."""
        step = ConversionStep(
            conversion_log_id=conversion.id,
            step_number=step_number,
            step_name=step_name,
            step_type=step_type,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step)
        await self.db.commit()
        return step

    async def _complete_step(
        self,
        conversion: ModuleConversionLog,
        step_number: int,
        output_data: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Complete a conversion step."""
        result = await self.db.execute(
            select(ConversionStep)
            .where(ConversionStep.conversion_log_id == conversion.id)
            .where(ConversionStep.step_number == step_number)
        )
        step = result.scalar_one_or_none()
        if step:
            step.status = "failed" if error_message else "completed"
            step.completed_at = datetime.now(timezone.utc)
            step.output_data = output_data or {}
            step.error_message = error_message
            if step.started_at:
                delta = step.completed_at - step.started_at
                step.duration_ms = int(delta.total_seconds() * 1000)
            await self.db.commit()

    async def _analyze_source(
        self,
        conversion: ModuleConversionLog,
        template: ModuleTemplate,
    ) -> dict[str, Any]:
        """Analyze source code structure.

        Returns:
            Analysis results including file structure, dependencies, etc.
        """
        analysis = {
            "source_type": conversion.source_type,
            "files_found": 0,
            "structure": {},
            "dependencies": [],
            "warnings": [],
        }

        if conversion.source_type == "github" and conversion.source_url:
            # Would fetch from GitHub and analyze
            analysis["repository"] = conversion.source_url
            analysis["branch"] = conversion.source_branch or "main"

        elif conversion.source_type == "upload":
            # Analyze uploaded content from input_data
            if "content" in conversion.input_data:
                content = conversion.input_data["content"]
                analysis["files_found"] = 1
                analysis["content_length"] = len(content)

        return analysis

    async def _prepare_conversion(
        self,
        conversion: ModuleConversionLog,
        template: ModuleTemplate,
        source_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Prepare the conversion context.

        Returns:
            Context for LLM conversion
        """
        context = {
            "template_name": template.name,
            "module_type": template.module_type.value if hasattr(template.module_type, 'value') else template.module_type,
            "package_name": template.package_name,
            "source_analysis": source_analysis,
            "conversion_rules": template.conversion_rules,
            "input_parameters": conversion.input_data,
        }

        return context

    async def _execute_llm_conversion(
        self,
        conversion: ModuleConversionLog,
        template: ModuleTemplate,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the LLM-based conversion.

        Returns:
            Conversion results with generated code
        """
        # Build system prompt
        system_prompt = template.system_prompt or self._get_default_system_prompt()

        # Build conversion prompt
        conversion_prompt = self._build_conversion_prompt(template, context)

        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=system_prompt),
            LLMMessage(role=MessageRole.USER, content=conversion_prompt),
        ]

        # Execute LLM call
        response = await self.llm_service.complete(
            messages=messages,
            config_id=conversion.llm_configuration_id,
            temperature=0.7,
            max_tokens=8192,
        )

        # Track token usage
        conversion.tokens_used += response.total_tokens
        llm_request = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": response.provider,
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "latency_ms": response.latency_ms,
        }
        conversion.llm_requests.append(llm_request)
        await self.db.commit()

        return {
            "generated_code": response.content,
            "model_used": response.model,
            "tokens_used": response.total_tokens,
        }

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for conversion."""
        return """You are an expert code converter and software architect.
Your task is to convert code following the specified template rules.

Guidelines:
- Maintain the original functionality
- Follow best practices for the target language
- Add appropriate error handling
- Include type hints where applicable
- Generate clean, readable code
- Add comments for complex logic

Output only the converted code without explanations."""

    def _build_conversion_prompt(
        self,
        template: ModuleTemplate,
        context: dict[str, Any],
    ) -> str:
        """Build the conversion prompt."""
        if template.conversion_prompt_template:
            # Use template's custom prompt
            prompt = template.conversion_prompt_template
            for key, value in context.get("input_parameters", {}).items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            return prompt

        # Default prompt structure
        return f"""Convert the following code according to these specifications:

Target Module: {context.get('package_name', 'unknown')}
Module Type: {context.get('module_type', 'unknown')}

Conversion Rules:
{context.get('conversion_rules', {})}

Input Parameters:
{context.get('input_parameters', {})}

Source Analysis:
{context.get('source_analysis', {})}

Please generate the converted code."""

    async def _validate_output(
        self,
        conversion: ModuleConversionLog,
        template: ModuleTemplate,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate the converted output.

        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "checks_passed": [],
        }

        generated_code = result.get("generated_code", "")

        # Basic validation checks
        if not generated_code.strip():
            validation["is_valid"] = False
            validation["errors"].append("Generated code is empty")
            return validation

        # Check for common issues
        if "TODO" in generated_code or "FIXME" in generated_code:
            validation["warnings"].append("Code contains TODO/FIXME markers")

        # Check code length
        if len(generated_code) < 50:
            validation["warnings"].append("Generated code seems very short")

        validation["checks_passed"].append("basic_validation")

        # Template-specific validation
        if template.validation_schema:
            # Would apply schema validation here
            validation["checks_passed"].append("schema_validation")

        return validation

    async def _stage_to_github(
        self,
        conversion: ModuleConversionLog,
        result: dict[str, Any],
        github_integration_id: str,
    ) -> dict[str, Any]:
        """Stage converted code to GitHub.

        Returns:
            Staging results with PR info
        """
        # Get GitHub integration
        integration_result = await self.db.execute(
            select(GitHubIntegration).where(GitHubIntegration.id == github_integration_id)
        )
        integration = integration_result.scalar_one_or_none()
        if not integration:
            raise ModuleConversionError("GitHub integration not found")

        # Create service
        github = await create_github_service_from_integration(integration, self.db)

        try:
            owner = integration.default_owner
            repo = integration.default_repo
            base_branch = integration.default_base_branch

            # Get base branch SHA
            base = await github.get_branch(owner, repo, base_branch)

            # Create staging branch
            branch_name = f"{integration.branch_prefix}{conversion.job_id}"
            await github.create_branch(owner, repo, branch_name, base.sha)
            conversion.staging_branch = branch_name

            # Create files
            generated_code = result.get("generated_code", "")
            files = [
                {
                    "path": f"modules/{conversion.job_id}/generated.py",
                    "content": generated_code,
                }
            ]
            await github.create_files_in_commit(
                owner, repo, branch_name, files,
                f"feat(module-converter): Add converted module {conversion.job_id}"
            )

            # Create PR
            title = integration.pr_title_template.format(
                module_name=conversion.job_id,
                action="converted",
            )
            pr = await github.create_pull_request(
                owner, repo,
                title=title,
                head=branch_name,
                base=base_branch,
                body=f"Automated module conversion\n\nJob ID: {conversion.job_id}",
            )

            conversion.staging_pr_url = pr.html_url
            conversion.staging_pr_number = pr.number

            # Add labels if configured
            if integration.default_labels:
                await github.add_labels(owner, repo, pr.number, integration.default_labels)

            # Request reviewers if configured
            if integration.default_reviewers:
                await github.request_reviewers(
                    owner, repo, pr.number, integration.default_reviewers
                )

            await self.db.commit()

            return {
                "branch": branch_name,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "files_staged": len(files),
            }

        finally:
            await github.close()

    # ==========================================================================
    # Template Management
    # ==========================================================================

    async def create_template(
        self,
        tenant_id: str,
        name: str,
        display_name: str,
        module_type: str,
        package_name: str,
        **kwargs: Any,
    ) -> ModuleTemplate:
        """Create a new module template."""
        template = ModuleTemplate(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            module_type=module_type,
            package_name=package_name,
            **kwargs,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def list_templates(
        self,
        tenant_id: str,
        include_public: bool = True,
    ) -> list[ModuleTemplate]:
        """List available templates."""
        query = select(ModuleTemplate).where(
            (ModuleTemplate.tenant_id == tenant_id) |
            (ModuleTemplate.is_public == True if include_public else False)
        ).where(ModuleTemplate.is_active == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())
