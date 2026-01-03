"""Tests for Checklists API endpoints.

Tests for checklist templates and audit case checklists.
"""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text


class TestChecklistTemplateEndpoints:
    """Tests for Checklist Template API."""

    @pytest.mark.asyncio
    async def test_list_templates_unauthorized(self, client: AsyncClient):
        """Test that listing templates requires authentication."""
        response = await client.get("/api/checklists/templates")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_templates_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test listing templates when none exist."""
        response = await client.get(
            "/api/checklists/templates", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_create_template(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test creating a new checklist template."""
        template_data = {
            "name": "Test Checklist Template",
            "description": "Template for testing",
            "checklist_type": "main",
            "structure": {
                "settings": {"allow_partial_save": True},
                "sections": [
                    {
                        "id": "section1",
                        "title": "Test Section",
                        "questions": [
                            {
                                "id": "q1",
                                "type": "yes_no",
                                "label": "Test Question?",
                                "required": True,
                            }
                        ],
                    }
                ],
            },
        }

        response = await client.post(
            "/api/checklists/templates",
            json=template_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["checklist_type"] == "main"
        assert data["status"] == "draft"
        assert data["version"] == 1
        assert data["is_current"] is True

    @pytest.mark.asyncio
    async def test_get_default_templates(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting default template structures."""
        response = await client.get(
            "/api/checklists/templates/defaults",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "main" in data
        assert "procurement" in data
        assert "sections" in data["main"]
        assert "sections" in data["procurement"]

    @pytest.mark.asyncio
    async def test_create_default_templates(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test creating default templates for tenant."""
        # Clean up existing templates first
        await test_db.execute(
            text(
                "DELETE FROM checklist_templates WHERE tenant_id = :tenant_id"
            ),
            {"tenant_id": uuid.UUID(test_user["tenant_id"])},
        )
        await test_db.commit()

        response = await client.post(
            "/api/checklists/templates/create-defaults",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least main template
        types = [t["checklist_type"] for t in data]
        assert "main" in types or "procurement" in types

    @pytest.mark.asyncio
    async def test_get_template_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent template."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/checklists/templates/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_template_by_id(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test getting a specific template."""
        # Create template
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO checklist_templates
                    (id, tenant_id, name, description, checklist_type,
                     structure, status, version, is_current, created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'Get Test Template', 'Test', 'main',
                     :structure, 'draft', 1, true, :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(template_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "structure": '{"sections": []}',
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.get(
            f"/api/checklists/templates/{template_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Get Test Template"

    @pytest.mark.asyncio
    async def test_update_template(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test updating a template."""
        # Create template
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO checklist_templates
                    (id, tenant_id, name, description, checklist_type,
                     structure, status, version, is_current, created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'Update Test Template', 'Original', 'main',
                     :structure, 'draft', 1, true, :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(template_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "structure": '{"sections": []}',
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        # Update
        update_data = {
            "name": "Updated Template Name",
            "description": "Updated description",
            "status": "published",
        }

        response = await client.patch(
            f"/api/checklists/templates/{template_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["description"] == "Updated description"
        assert data["status"] == "published"

    @pytest.mark.asyncio
    async def test_delete_template_not_in_use(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test deleting a template that is not in use."""
        # Create template
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO checklist_templates
                    (id, tenant_id, name, description, checklist_type,
                     structure, status, version, is_current, created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'Delete Test Template', 'To delete', 'main',
                     :structure, 'draft', 1, true, :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(template_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "structure": '{"sections": []}',
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/checklists/templates/{template_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_list_templates_with_filter(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test listing templates with type filter."""
        # Create templates of different types
        now = datetime.now(timezone.utc)

        for i, checklist_type in enumerate(["main", "procurement"]):
            template_id = str(uuid.uuid4())
            await test_db.execute(
                text(
                    """
                    INSERT INTO checklist_templates
                        (id, tenant_id, name, description, checklist_type,
                         structure, status, version, is_current, created_at, updated_at)
                    VALUES
                        (:id, :tenant_id, :name, 'Filter test', :type,
                         :structure, 'published', 1, true, :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid.UUID(template_id),
                    "tenant_id": uuid.UUID(test_user["tenant_id"]),
                    "name": f"Filter Test {checklist_type}",
                    "type": checklist_type,
                    "structure": '{"sections": []}',
                    "created_at": now,
                    "updated_at": now,
                },
            )
        await test_db.commit()

        # Filter by type
        response = await client.get(
            "/api/checklists/templates?checklist_type=main",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["checklist_type"] == "main"


class TestAuditCaseChecklistEndpoints:
    """Tests for Audit Case Checklist API."""

    @pytest_asyncio.fixture
    async def test_audit_case(self, test_db, test_user) -> dict:
        """Create an audit case for testing."""
        case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO audit_cases
                    (id, tenant_id, case_number, project_name, beneficiary_name,
                     status, audit_type, custom_data, is_sample, requires_follow_up,
                     created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'TEST-2024-001', 'Test Project',
                     'Test Beneficiary', 'draft', 'operation', '{}', false, false,
                     :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(case_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        return {"id": case_id, "case_number": "TEST-2024-001"}

    @pytest_asyncio.fixture
    async def test_template(self, test_db, test_user) -> dict:
        """Create a checklist template for testing."""
        import json

        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        structure = {
            "settings": {"allow_partial_save": True},
            "sections": [
                {
                    "id": "section1",
                    "title": "Test Section",
                    "questions": [
                        {
                            "id": "q1",
                            "type": "yes_no",
                            "label": "Test Question 1?",
                        },
                        {
                            "id": "q2",
                            "type": "text",
                            "label": "Test Question 2",
                        },
                    ],
                }
            ],
        }

        await test_db.execute(
            text(
                """
                INSERT INTO checklist_templates
                    (id, tenant_id, name, description, checklist_type,
                     structure, status, version, is_current, created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'Case Test Template', 'For case tests', 'main',
                     :structure, 'published', 1, true, :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(template_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "structure": json.dumps(structure),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        return {"id": template_id, "name": "Case Test Template"}

    @pytest.mark.asyncio
    async def test_list_case_checklists_unauthorized(self, client: AsyncClient):
        """Test that listing case checklists requires auth."""
        case_id = str(uuid.uuid4())
        response = await client.get(f"/api/checklists/audit-case/{case_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_case_checklists_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing checklists for non-existent case."""
        fake_case_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/checklists/audit-case/{fake_case_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_case_checklists_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
    ):
        """Test listing checklists when none attached."""
        response = await client.get(
            f"/api/checklists/audit-case/{test_audit_case['id']}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_add_checklist_to_case(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
        test_template: dict,
    ):
        """Test adding a checklist to an audit case."""
        response = await client.post(
            f"/api/checklists/audit-case/{test_audit_case['id']}",
            json={"template_id": test_template["id"]},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["audit_case_id"] == test_audit_case["id"]
        assert data["checklist_template_id"] == test_template["id"]
        assert data["status"] == "not_started"
        assert data["progress"] == 0

    @pytest.mark.asyncio
    async def test_add_checklist_template_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
    ):
        """Test adding checklist with non-existent template."""
        fake_template_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/checklists/audit-case/{test_audit_case['id']}",
            json={"template_id": fake_template_id},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_case_checklist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
        test_template: dict,
        test_db,
    ):
        """Test getting a specific case checklist."""
        # Create checklist instance
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_template_id, checklist_type,
                     status, progress, total_questions, answered_questions,
                     responses, created_at, updated_at)
                VALUES
                    (:id, :case_id, :template_id, 'main',
                     'not_started', 0, 2, 0, '{}', :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(test_audit_case["id"]),
                "template_id": uuid.UUID(test_template["id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.get(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{checklist_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == checklist_id
        assert data["status"] == "not_started"

    @pytest.mark.asyncio
    async def test_get_case_checklist_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
    ):
        """Test getting non-existent checklist."""
        fake_checklist_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{fake_checklist_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_checklist_responses(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
        test_template: dict,
        test_db,
    ):
        """Test updating checklist responses."""
        # Create checklist instance
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_template_id, checklist_type,
                     status, progress, total_questions, answered_questions,
                     responses, created_at, updated_at)
                VALUES
                    (:id, :case_id, :template_id, 'main',
                     'not_started', 0, 2, 0, '{}', :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(test_audit_case["id"]),
                "template_id": uuid.UUID(test_template["id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        # Update responses
        update_data = {
            "responses": {"q1": "yes", "q2": "Test answer"},
        }

        response = await client.patch(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{checklist_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["answered_questions"] == 2
        assert data["progress"] == 100  # 2/2 questions

    @pytest.mark.asyncio
    async def test_update_checklist_with_notes(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
        test_template: dict,
        test_db,
    ):
        """Test updating checklist with notes."""
        # Create checklist
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_template_id, checklist_type,
                     status, progress, total_questions, answered_questions,
                     responses, created_at, updated_at)
                VALUES
                    (:id, :case_id, :template_id, 'main',
                     'in_progress', 50, 2, 1, '{"q1": {"value": "yes"}}',
                     :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(test_audit_case["id"]),
                "template_id": uuid.UUID(test_template["id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        # Add notes
        update_data = {
            "responses": {},
            "notes": {"q1": "Additional note for question 1"},
        }

        response = await client.patch(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{checklist_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_complete_checklist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
        test_template: dict,
        test_db,
    ):
        """Test completing a checklist."""
        # Create checklist
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_template_id, checklist_type,
                     status, progress, total_questions, answered_questions,
                     responses, created_at, updated_at)
                VALUES
                    (:id, :case_id, :template_id, 'main',
                     'in_progress', 100, 2, 2,
                     '{"q1": {"value": "yes"}, "q2": {"value": "answer"}}',
                     :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(test_audit_case["id"]),
                "template_id": uuid.UUID(test_template["id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        # Complete checklist
        update_data = {
            "responses": {},
            "status": "completed",
        }

        response = await client.patch(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{checklist_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_delete_case_checklist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
        test_template: dict,
        test_db,
    ):
        """Test deleting a case checklist."""
        # Create checklist
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_template_id, checklist_type,
                     status, progress, total_questions, answered_questions,
                     responses, created_at, updated_at)
                VALUES
                    (:id, :case_id, :template_id, 'main',
                     'not_started', 0, 2, 0, '{}', :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(test_audit_case["id"]),
                "template_id": uuid.UUID(test_template["id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{checklist_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_case_checklist_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_audit_case: dict,
    ):
        """Test deleting non-existent checklist."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/checklists/audit-case/{test_audit_case['id']}/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestChecklistTemplateArchival:
    """Tests for template archival when in use."""

    @pytest_asyncio.fixture
    async def template_in_use(self, test_db, test_user) -> dict:
        """Create a template that is in use by a checklist."""
        template_id = str(uuid.uuid4())
        case_id = str(uuid.uuid4())
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Create template
        await test_db.execute(
            text(
                """
                INSERT INTO checklist_templates
                    (id, tenant_id, name, description, checklist_type,
                     structure, status, version, is_current, created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'In Use Template', 'Being used', 'main',
                     :structure, 'published', 1, true, :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(template_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "structure": '{"sections": []}',
                "created_at": now,
                "updated_at": now,
            },
        )

        # Create audit case
        await test_db.execute(
            text(
                """
                INSERT INTO audit_cases
                    (id, tenant_id, case_number, project_name, beneficiary_name,
                     status, audit_type, custom_data, is_sample, requires_follow_up,
                     created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'ARCH-2024-001', 'Archival Test',
                     'Test', 'draft', 'operation', '{}', false, false,
                     :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(case_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "created_at": now,
                "updated_at": now,
            },
        )

        # Create checklist using template
        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_template_id, checklist_type,
                     status, progress, total_questions, answered_questions,
                     responses, created_at, updated_at)
                VALUES
                    (:id, :case_id, :template_id, 'main',
                     'in_progress', 50, 2, 1, '{}', :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(case_id),
                "template_id": uuid.UUID(template_id),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        return {
            "template_id": template_id,
            "case_id": case_id,
            "checklist_id": checklist_id,
        }

    @pytest.mark.asyncio
    async def test_delete_template_in_use_archives(
        self,
        client: AsyncClient,
        auth_headers: dict,
        template_in_use: dict,
        test_db,
    ):
        """Test that deleting a template in use archives it instead."""
        template_id = template_in_use["template_id"]

        response = await client.delete(
            f"/api/checklists/templates/{template_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it was archived, not deleted
        result = await test_db.execute(
            text("SELECT status, is_current FROM checklist_templates WHERE id = :id"),
            {"id": uuid.UUID(template_id)},
        )
        row = result.first()
        assert row is not None
        assert row[0] == "archived"
        assert row[1] is False


class TestChecklistCleanup:
    """Cleanup test data after checklist tests."""

    @pytest.mark.asyncio
    async def test_cleanup_checklist_data(self, test_db):
        """Clean up test checklist data."""
        try:
            # Clean up checklists
            await test_db.execute(
                text(
                    "DELETE FROM audit_case_checklists "
                    "WHERE audit_case_id IN "
                    "(SELECT id FROM audit_cases WHERE case_number LIKE 'TEST-%' "
                    "OR case_number LIKE 'ARCH-%')"
                )
            )
            # Clean up audit cases
            await test_db.execute(
                text(
                    "DELETE FROM audit_cases "
                    "WHERE case_number LIKE 'TEST-%' OR case_number LIKE 'ARCH-%'"
                )
            )
            # Clean up templates
            await test_db.execute(
                text(
                    "DELETE FROM checklist_templates "
                    "WHERE name LIKE '%Test%' OR name LIKE '%Filter%' "
                    "OR name LIKE '%In Use%'"
                )
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
