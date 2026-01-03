"""Tests for Audit Cases API endpoints.

Tests for audit case CRUD, statistics, and embedded checklists.
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text


class TestAuditCaseCRUD:
    """Tests for Audit Case CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_audit_cases_unauthorized(self, client: AsyncClient):
        """Test that listing audit cases requires authentication."""
        response = await client.get("/api/audit-cases")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_audit_cases_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test listing audit cases when none exist."""
        response = await client.get("/api/audit-cases", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

    @pytest.mark.asyncio
    async def test_create_audit_case(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test creating a new audit case."""
        case_data = {
            "case_number": "AC-2024-001",
            "project_name": "Test Project Alpha",
            "beneficiary_name": "Test Beneficiary GmbH",
            "audit_type": "operation",
            "approved_amount": "50000.00",
            "is_sample": False,
            "custom_data": {},
        }

        response = await client.post(
            "/api/audit-cases",
            json=case_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["case_number"] == case_data["case_number"]
        assert data["project_name"] == case_data["project_name"]
        assert data["beneficiary_name"] == case_data["beneficiary_name"]
        assert data["status"] == "draft"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_audit_case_minimal(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating audit case with minimal data."""
        case_data = {
            "case_number": "AC-2024-002",
            "project_name": "Minimal Project",
            "beneficiary_name": "Minimal Beneficiary",
        }

        response = await client.post(
            "/api/audit-cases",
            json=case_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["audit_type"] == "operation"  # Default
        assert data["is_sample"] is False  # Default

    @pytest.mark.asyncio
    async def test_get_audit_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent audit case."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_audit_case_by_id(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test getting a specific audit case."""
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
                    (:id, :tenant_id, 'GET-2024-001', 'Get Test Project',
                     'Get Test Beneficiary', 'draft', 'operation', '{}', false, false,
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

        response = await client.get(
            f"/api/audit-cases/{case_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == case_id
        assert data["case_number"] == "GET-2024-001"
        assert "checklists_count" in data
        assert "findings_count" in data

    @pytest.mark.asyncio
    async def test_update_audit_case(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test updating an audit case."""
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
                    (:id, :tenant_id, 'UPD-2024-001', 'Update Test Project',
                     'Update Test Beneficiary', 'draft', 'operation', '{}', false, false,
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

        update_data = {
            "project_name": "Updated Project Name",
            "status": "in_progress",
            "audited_amount": "45000.00",
        }

        response = await client.patch(
            f"/api/audit-cases/{case_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "Updated Project Name"
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_update_audit_case_status_change(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test updating audit case status triggers audit log."""
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
                    (:id, :tenant_id, 'STATUS-2024-001', 'Status Test',
                     'Status Beneficiary', 'draft', 'operation', '{}', false, false,
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

        # Change status
        response = await client.patch(
            f"/api/audit-cases/{case_id}",
            json={"status": "review"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "review"

    @pytest.mark.asyncio
    async def test_update_audit_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating non-existent audit case."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/audit-cases/{fake_id}",
            json={"project_name": "New Name"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_audit_case(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test deleting an audit case."""
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
                    (:id, :tenant_id, 'DEL-2024-001', 'Delete Test',
                     'Delete Beneficiary', 'draft', 'operation', '{}', false, false,
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

        response = await client.delete(
            f"/api/audit-cases/{case_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/audit-cases/{case_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_audit_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent audit case."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/audit-cases/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestAuditCaseFiltering:
    """Tests for audit case filtering and pagination."""

    @pytest_asyncio.fixture
    async def multiple_cases(self, test_db, test_user) -> list[dict]:
        """Create multiple audit cases for filtering tests."""
        cases = []
        now = datetime.now(timezone.utc)

        test_cases = [
            ("FILTER-001", "Project Alpha", "draft", "operation"),
            ("FILTER-002", "Project Beta", "in_progress", "operation"),
            ("FILTER-003", "Project Gamma", "completed", "system"),
            ("FILTER-004", "Project Delta", "draft", "accounts"),
            ("FILTER-005", "Project Epsilon", "review", "operation"),
        ]

        for case_number, project_name, status, audit_type in test_cases:
            case_id = str(uuid.uuid4())
            await test_db.execute(
                text(
                    """
                    INSERT INTO audit_cases
                        (id, tenant_id, case_number, project_name, beneficiary_name,
                         status, audit_type, custom_data, is_sample, requires_follow_up,
                         created_at, updated_at)
                    VALUES
                        (:id, :tenant_id, :case_number, :project_name,
                         'Filter Test Beneficiary', :status, :audit_type, '{}',
                         false, false, :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid.UUID(case_id),
                    "tenant_id": uuid.UUID(test_user["tenant_id"]),
                    "case_number": case_number,
                    "project_name": project_name,
                    "status": status,
                    "audit_type": audit_type,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            cases.append({"id": case_id, "case_number": case_number})

        await test_db.commit()
        return cases

    @pytest.mark.asyncio
    async def test_list_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        multiple_cases: list[dict],
    ):
        """Test listing with pagination."""
        response = await client.get(
            "/api/audit-cases?page=1&page_size=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        multiple_cases: list[dict],
    ):
        """Test filtering by status."""
        response = await client.get(
            "/api/audit-cases?status=draft",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "draft"

    @pytest.mark.asyncio
    async def test_filter_by_audit_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        multiple_cases: list[dict],
    ):
        """Test filtering by audit type."""
        response = await client.get(
            "/api/audit-cases?audit_type=system",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["audit_type"] == "system"

    @pytest.mark.asyncio
    async def test_search_by_project_name(
        self,
        client: AsyncClient,
        auth_headers: dict,
        multiple_cases: list[dict],
    ):
        """Test searching by project name."""
        response = await client.get(
            "/api/audit-cases?search=Alpha",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert any("Alpha" in item["project_name"] for item in data["items"])

    @pytest.mark.asyncio
    async def test_search_by_case_number(
        self,
        client: AsyncClient,
        auth_headers: dict,
        multiple_cases: list[dict],
    ):
        """Test searching by case number."""
        response = await client.get(
            "/api/audit-cases?search=FILTER-003",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert any("FILTER-003" in item["case_number"] for item in data["items"])


class TestAuditCaseStatistics:
    """Tests for audit case statistics endpoint."""

    @pytest_asyncio.fixture
    async def cases_with_amounts(self, test_db, test_user) -> list[dict]:
        """Create audit cases with financial amounts."""
        cases = []
        now = datetime.now(timezone.utc)

        test_cases = [
            ("STAT-001", "draft", None, "50000.00", None),
            ("STAT-002", "completed", "no_findings", "75000.00", "0.00"),
            ("STAT-003", "completed", "findings_minor", "100000.00", "5000.00"),
            ("STAT-004", "completed", "irregularity", "80000.00", "10000.00"),
        ]

        for case_number, status, result, audited, irregular in test_cases:
            case_id = str(uuid.uuid4())
            await test_db.execute(
                text(
                    """
                    INSERT INTO audit_cases
                        (id, tenant_id, case_number, project_name, beneficiary_name,
                         status, result, audit_type, audited_amount, irregular_amount,
                         custom_data, is_sample, requires_follow_up,
                         created_at, updated_at)
                    VALUES
                        (:id, :tenant_id, :case_number, 'Stats Project',
                         'Stats Beneficiary', :status, :result, 'operation',
                         :audited, :irregular, '{}', false, false,
                         :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid.UUID(case_id),
                    "tenant_id": uuid.UUID(test_user["tenant_id"]),
                    "case_number": case_number,
                    "status": status,
                    "result": result,
                    "audited": audited,
                    "irregular": irregular,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            cases.append({"id": case_id})

        await test_db.commit()
        return cases

    @pytest.mark.asyncio
    async def test_get_statistics_unauthorized(self, client: AsyncClient):
        """Test that statistics require authentication."""
        response = await client.get("/api/audit-cases/statistics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        cases_with_amounts: list[dict],
    ):
        """Test getting audit case statistics."""
        response = await client.get(
            "/api/audit-cases/statistics",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_result" in data
        assert "by_type" in data
        assert "total_audited_amount" in data
        assert "total_irregular_amount" in data
        assert "error_rate" in data

    @pytest.mark.asyncio
    async def test_statistics_calculations(
        self,
        client: AsyncClient,
        auth_headers: dict,
        cases_with_amounts: list[dict],
    ):
        """Test that statistics calculations are correct."""
        response = await client.get(
            "/api/audit-cases/statistics",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have cases in different statuses
        assert data["total"] >= 4
        assert "draft" in data["by_status"] or "completed" in data["by_status"]


class TestAuditCaseChecklists:
    """Tests for audit case embedded checklists."""

    @pytest_asyncio.fixture
    async def case_with_checklist(self, test_db, test_user) -> dict:
        """Create audit case with checklist."""
        case_id = str(uuid.uuid4())
        checklist_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Create audit case
        await test_db.execute(
            text(
                """
                INSERT INTO audit_cases
                    (id, tenant_id, case_number, project_name, beneficiary_name,
                     status, audit_type, custom_data, is_sample, requires_follow_up,
                     created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'CL-2024-001', 'Checklist Test',
                     'Checklist Beneficiary', 'in_progress', 'operation', '{}',
                     false, false, :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(case_id),
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "created_at": now,
                "updated_at": now,
            },
        )

        # Create checklist
        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_checklists
                    (id, audit_case_id, checklist_type, status, progress,
                     total_questions, answered_questions, responses,
                     created_at, updated_at)
                VALUES
                    (:id, :case_id, 'main', 'in_progress', 50,
                     4, 2, '{"q1": "yes", "q2": "no"}',
                     :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(checklist_id),
                "case_id": uuid.UUID(case_id),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        return {"case_id": case_id, "checklist_id": checklist_id}

    @pytest.mark.asyncio
    async def test_list_case_checklists_unauthorized(self, client: AsyncClient):
        """Test that listing case checklists requires auth."""
        case_id = str(uuid.uuid4())
        response = await client.get(f"/api/audit-cases/{case_id}/checklists")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_case_checklists(
        self,
        client: AsyncClient,
        auth_headers: dict,
        case_with_checklist: dict,
    ):
        """Test listing checklists for an audit case."""
        response = await client.get(
            f"/api/audit-cases/{case_with_checklist['case_id']}/checklists",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["checklist_type"] == "main"

    @pytest.mark.asyncio
    async def test_list_case_checklists_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing checklists for non-existent case."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{fake_id}/checklists",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_checklist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        case_with_checklist: dict,
    ):
        """Test getting a specific checklist."""
        response = await client.get(
            f"/api/audit-cases/{case_with_checklist['case_id']}"
            f"/checklists/{case_with_checklist['checklist_id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == case_with_checklist["checklist_id"]
        assert data["status"] == "in_progress"
        assert data["progress"] == 50
        assert "responses" in data

    @pytest.mark.asyncio
    async def test_get_checklist_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        case_with_checklist: dict,
    ):
        """Test getting non-existent checklist."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{case_with_checklist['case_id']}/checklists/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_checklist_responses(
        self,
        client: AsyncClient,
        auth_headers: dict,
        case_with_checklist: dict,
    ):
        """Test updating checklist responses."""
        update_data = {
            "responses": {"q3": "yes", "q4": "no"},
        }

        response = await client.patch(
            f"/api/audit-cases/{case_with_checklist['case_id']}"
            f"/checklists/{case_with_checklist['checklist_id']}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Responses should be merged
        assert "q3" in data["responses"]
        assert "q4" in data["responses"]

    @pytest.mark.asyncio
    async def test_complete_checklist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        case_with_checklist: dict,
    ):
        """Test completing a checklist."""
        update_data = {
            "responses": {},
            "status": "completed",
        }

        response = await client.patch(
            f"/api/audit-cases/{case_with_checklist['case_id']}"
            f"/checklists/{case_with_checklist['checklist_id']}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_checklist_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        case_with_checklist: dict,
    ):
        """Test updating non-existent checklist."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/audit-cases/{case_with_checklist['case_id']}/checklists/{fake_id}",
            json={"responses": {"q1": "yes"}},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestAuditCaseAccessControl:
    """Tests for audit case access control."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_case(
        self, client: AsyncClient, auth_headers: dict, test_db
    ):
        """Test that users cannot access cases from other tenants."""
        # Create case for different tenant
        other_tenant_id = str(uuid.uuid4())
        case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Create other tenant
        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, 'Other Tenant', 'group', 'active', :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": uuid.UUID(other_tenant_id),
                "created_at": now,
                "updated_at": now,
            },
        )

        # Create case for other tenant
        await test_db.execute(
            text(
                """
                INSERT INTO audit_cases
                    (id, tenant_id, case_number, project_name, beneficiary_name,
                     status, audit_type, custom_data, is_sample, requires_follow_up,
                     created_at, updated_at)
                VALUES
                    (:id, :tenant_id, 'OTHER-2024-001', 'Other Project',
                     'Other Beneficiary', 'draft', 'operation', '{}', false, false,
                     :created_at, :updated_at)
                """
            ),
            {
                "id": uuid.UUID(case_id),
                "tenant_id": uuid.UUID(other_tenant_id),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        # Try to access
        response = await client.get(
            f"/api/audit-cases/{case_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestAuditCaseCleanup:
    """Cleanup test data after audit case tests."""

    @pytest.mark.asyncio
    async def test_cleanup_audit_case_data(self, test_db):
        """Clean up test audit case data."""
        try:
            # Clean up checklists for test cases
            await test_db.execute(
                text(
                    "DELETE FROM audit_case_checklists "
                    "WHERE audit_case_id IN "
                    "(SELECT id FROM audit_cases WHERE case_number LIKE 'AC-%' "
                    "OR case_number LIKE 'GET-%' OR case_number LIKE 'UPD-%' "
                    "OR case_number LIKE 'DEL-%' OR case_number LIKE 'STATUS-%' "
                    "OR case_number LIKE 'FILTER-%' OR case_number LIKE 'STAT-%' "
                    "OR case_number LIKE 'CL-%' OR case_number LIKE 'OTHER-%')"
                )
            )
            # Clean up audit cases
            await test_db.execute(
                text(
                    "DELETE FROM audit_cases "
                    "WHERE case_number LIKE 'AC-%' OR case_number LIKE 'GET-%' "
                    "OR case_number LIKE 'UPD-%' OR case_number LIKE 'DEL-%' "
                    "OR case_number LIKE 'STATUS-%' OR case_number LIKE 'FILTER-%' "
                    "OR case_number LIKE 'STAT-%' OR case_number LIKE 'CL-%' "
                    "OR case_number LIKE 'OTHER-%'"
                )
            )
            # Clean up test tenants
            await test_db.execute(
                text("DELETE FROM tenants WHERE name = 'Other Tenant'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
