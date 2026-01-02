"""Module Manager for Distribution System (Feature 6)."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module import Module, ModuleDeployment, ModuleStatus, DeploymentStatus
from app.models.customer import Customer


class ModuleManifest:
    """Module manifest (module.json) structure."""

    def __init__(self, data: dict):
        self.id = data.get("id")
        self.name = data.get("name", "")
        self.version = data.get("version", "0.0.0")
        self.description = data.get("description", "")
        self.author = data.get("author", "")
        self.license = data.get("license", "proprietary")
        self.dependencies = data.get("dependencies", [])
        self.min_system_version = data.get("minSystemVersion", "1.0.0")
        self.entry_point = data.get("entryPoint", "")
        self.hooks = data.get("hooks", {})
        self.permissions = data.get("permissions", [])
        self.config_schema = data.get("configSchema", {})

    @classmethod
    def from_file(cls, path: Path) -> "ModuleManifest":
        """Load manifest from module.json file."""
        with open(path) as f:
            data = json.load(f)
        return cls(data)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "dependencies": self.dependencies,
            "minSystemVersion": self.min_system_version,
            "entryPoint": self.entry_point,
            "hooks": self.hooks,
            "permissions": self.permissions,
            "configSchema": self.config_schema,
        }


class ModuleManager:
    """Module distribution manager.

    AC-6.1.1: Module können installiert werden
    AC-6.1.2: Module können aktualisiert werden
    AC-6.1.3: Module können deinstalliert werden
    AC-6.1.4: Abhängigkeiten werden geprüft
    """

    def __init__(self, db: AsyncSession, modules_dir: Path | None = None):
        self.db = db
        self.modules_dir = modules_dir or Path("modules")

    async def list_installed(self, customer_id: str) -> list[dict]:
        """List all installed modules for a customer."""
        result = await self.db.execute(
            select(ModuleDeployment).where(
                ModuleDeployment.customer_id == customer_id,
                ModuleDeployment.status == DeploymentStatus.deployed,
            )
        )
        deployments = result.scalars().all()

        installed = []
        for deployment in deployments:
            result = await self.db.execute(
                select(Module).where(Module.id == deployment.module_id)
            )
            module = result.scalar_one_or_none()
            if module:
                installed.append(
                    {
                        "id": module.id,
                        "name": module.name,
                        "version": deployment.deployed_version,
                        "deployed_at": (
                            deployment.deployed_at.isoformat()
                            if deployment.deployed_at
                            else None
                        ),
                        "status": deployment.status.value,
                    }
                )

        return installed

    async def get_available(self) -> list[dict]:
        """Get all available (released) modules."""
        result = await self.db.execute(
            select(Module).where(Module.status == ModuleStatus.released)
        )
        modules = result.scalars().all()

        return [
            {
                "id": m.id,
                "name": m.name,
                "version": m.version,
                "description": m.description,
                "dependencies": m.dependencies or [],
                "min_system_version": m.min_system_version,
            }
            for m in modules
        ]

    async def check_dependencies(
        self, module_id: str, customer_id: str
    ) -> tuple[bool, list[str]]:
        """Check if all dependencies are installed.

        AC-6.1.4: Abhängigkeiten werden geprüft
        """
        result = await self.db.execute(select(Module).where(Module.id == module_id))
        module = result.scalar_one_or_none()

        if not module:
            return False, ["Module not found"]

        dependencies = module.dependencies or []
        missing = []

        installed = await self.list_installed(customer_id)
        installed_ids = {m["id"] for m in installed}

        for dep_id in dependencies:
            if dep_id not in installed_ids:
                missing.append(dep_id)

        return len(missing) == 0, missing

    async def install_module(
        self,
        module_id: str,
        customer_id: str,
        version: Optional[str] = None,
        installed_by: Optional[str] = None,
    ) -> dict:
        """Install a module for a customer.

        AC-6.1.1: Module können installiert werden
        """
        # Check module exists
        result = await self.db.execute(select(Module).where(Module.id == module_id))
        module = result.scalar_one_or_none()

        if not module:
            raise ValueError(f"Module {module_id} not found")

        if module.status != ModuleStatus.released:
            raise ValueError(f"Module {module_id} is not released")

        # Check customer exists
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Check dependencies
        deps_ok, missing = await self.check_dependencies(module_id, customer_id)
        if not deps_ok:
            raise ValueError(f"Missing dependencies: {', '.join(missing)}")

        # Check if already installed
        result = await self.db.execute(
            select(ModuleDeployment).where(
                ModuleDeployment.module_id == module_id,
                ModuleDeployment.customer_id == customer_id,
                ModuleDeployment.status == DeploymentStatus.deployed,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Module {module_id} is already installed")

        # Create deployment
        deployment = ModuleDeployment(
            id=str(uuid4()),
            module_id=module_id,
            customer_id=customer_id,
            status=DeploymentStatus.deployed,
            deployed_at=datetime.now(timezone.utc),
            deployed_by=installed_by,
            deployed_version=version or module.version,
        )

        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)

        return {
            "id": deployment.id,
            "module_id": module_id,
            "version": deployment.deployed_version,
            "status": "deployed",
            "deployed_at": deployment.deployed_at.isoformat(),
        }

    async def update_module(
        self,
        module_id: str,
        customer_id: str,
        target_version: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> dict:
        """Update a module to a new version.

        AC-6.1.2: Module können aktualisiert werden
        """
        # Get current deployment
        result = await self.db.execute(
            select(ModuleDeployment).where(
                ModuleDeployment.module_id == module_id,
                ModuleDeployment.customer_id == customer_id,
                ModuleDeployment.status == DeploymentStatus.deployed,
            )
        )
        current = result.scalar_one_or_none()

        if not current:
            raise ValueError(f"Module {module_id} is not installed")

        # Get module
        result = await self.db.execute(select(Module).where(Module.id == module_id))
        module = result.scalar_one_or_none()

        if not module:
            raise ValueError(f"Module {module_id} not found")

        new_version = target_version or module.version

        if current.deployed_version == new_version:
            raise ValueError(f"Module is already at version {new_version}")

        # Mark current as rolled back
        current.status = DeploymentStatus.rolled_back

        # Create new deployment
        deployment = ModuleDeployment(
            id=str(uuid4()),
            module_id=module_id,
            customer_id=customer_id,
            status=DeploymentStatus.deployed,
            deployed_at=datetime.now(timezone.utc),
            deployed_by=updated_by,
            deployed_version=new_version,
            previous_version=current.deployed_version,
        )

        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)

        return {
            "id": deployment.id,
            "module_id": module_id,
            "version": deployment.deployed_version,
            "previous_version": deployment.previous_version,
            "status": "deployed",
            "deployed_at": deployment.deployed_at.isoformat(),
        }

    async def uninstall_module(
        self,
        module_id: str,
        customer_id: str,
    ) -> dict:
        """Uninstall a module from a customer.

        AC-6.1.3: Module können deinstalliert werden
        """
        # Get current deployment
        result = await self.db.execute(
            select(ModuleDeployment).where(
                ModuleDeployment.module_id == module_id,
                ModuleDeployment.customer_id == customer_id,
                ModuleDeployment.status == DeploymentStatus.deployed,
            )
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise ValueError(f"Module {module_id} is not installed")

        # Check if other modules depend on this one
        installed = await self.list_installed(customer_id)
        for mod in installed:
            if mod["id"] == module_id:
                continue

            result = await self.db.execute(select(Module).where(Module.id == mod["id"]))
            other_module = result.scalar_one_or_none()

            if other_module and module_id in (other_module.dependencies or []):
                raise ValueError(
                    f"Cannot uninstall: module {other_module.name} depends on this module"
                )

        # Mark as rolled back
        deployment.status = DeploymentStatus.rolled_back

        await self.db.commit()

        return {
            "module_id": module_id,
            "status": "uninstalled",
            "uninstalled_at": datetime.now(timezone.utc).isoformat(),
        }
