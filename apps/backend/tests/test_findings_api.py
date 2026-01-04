"""Tests for Findings API endpoints.

Tests for audit case findings (Feststellungen) management.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest_asyncio.fixture
async def findings_audit_case(test_db, test_user) -> dict:
    """Create an audit case for findings tests."""
    case_id = str(uuid.uuid4())
    tenant_id = test_user["tenant_id"]
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO audit_cases (id, tenant_id, case_number, project_name,
                beneficiary_name, status, audit_type, is_sample, requires_follow_up,
                custom_data, created_at, updated_at)
            VALUES (:id, :tenant_id, 'FIND-2024-001', 'Findings Test Project',
                'Test Beneficiary', 'in_progress', 'operation', false, false,
                '{}', :created_at, :updated_at)
            """
        ),
        {
            "id": case_id,
            "tenant_id": uuid.UUID(tenant_id),
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": case_id, "tenant_id": tenant_id}


@pytest_asyncio.fixture
async def test_finding(test_db, findings_audit_case) -> dict:
    """Create a test finding."""
    finding_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO audit_case_findings (id, audit_case_id, finding_number,
                finding_type, title, description, status, is_systemic,
                response_requested, created_at, updated_at)
            VALUES (:id, :audit_case_id, 1, 'irregularity',
                'Test Finding', 'Test finding description', 'draft', false,
                false, :created_at, :updated_at)
            """
        ),
        {
            "id": finding_id,
            "audit_case_id": findings_audit_case["id"],
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": finding_id,
        "audit_case_id": findings_audit_case["id"],
        "finding_number": 1,
    }


@pytest_asyncio.fixture
async def confirmed_finding(test_db, findings_audit_case) -> dict:
    """Create a confirmed finding."""
    finding_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO audit_case_findings (id, audit_case_id, finding_number,
                finding_type, title, description, status, is_systemic,
                response_requested, created_at, updated_at)
            VALUES (:id, :audit_case_id, 2, 'deficiency',
                'Confirmed Finding', 'This is a confirmed finding', 'confirmed', false,
                false, :created_at, :updated_at)
            """
        ),
        {
            "id": finding_id,
            "audit_case_id": findings_audit_case["id"],
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": finding_id,
        "audit_case_id": findings_audit_case["id"],
        "finding_number": 2,
    }


# ==============================================================================
# Authentication Tests
# ==============================================================================


class TestFindingsAuthentication:
    """Tests for findings authentication."""

    @pytest.mark.asyncio
    async def test_list_findings_unauthorized(
        self, client: AsyncClient, findings_audit_case: dict
    ):
        """Test that listing findings requires authentication."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_finding_unauthorized(
        self, client: AsyncClient, findings_audit_case: dict
    ):
        """Test that creating findings requires authentication."""
        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings",
            json={
                "finding_type": "irregularity",
                "title": "Unauthorized Finding",
                "description": "Should fail",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_finding_unauthorized(
        self, client: AsyncClient, findings_audit_case: dict, test_finding: dict
    ):
        """Test that getting finding requires authentication."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_finding_unauthorized(
        self, client: AsyncClient, findings_audit_case: dict, test_finding: dict
    ):
        """Test that deleting finding requires authentication."""
        response = await client.delete(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}"
        )
        assert response.status_code == 401


# ==============================================================================
# List Findings Tests
# ==============================================================================


class TestListFindings:
    """Tests for listing findings."""

    @pytest.mark.asyncio
    async def test_list_findings_empty(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test listing findings when none exist."""
        # Create fresh case without findings
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        # May have findings from fixture
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_findings_with_items(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test listing findings with existing items."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(f["id"] == test_finding["id"] for f in data)

    @pytest.mark.asyncio
    async def test_list_findings_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test filtering findings by status."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings?status=draft",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for finding in data:
            assert finding["status"] == "draft"

    @pytest.mark.asyncio
    async def test_list_findings_filter_by_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test filtering findings by type."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings?finding_type=irregularity",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for finding in data:
            assert finding["finding_type"] == "irregularity"

    @pytest.mark.asyncio
    async def test_list_findings_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing findings for non-existent case."""
        fake_case_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{fake_case_id}/findings",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ==============================================================================
# Create Finding Tests
# ==============================================================================


class TestCreateFinding:
    """Tests for creating findings."""

    @pytest.mark.asyncio
    async def test_create_finding_success(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test successful finding creation."""
        finding_data = {
            "finding_type": "irregularity",
            "title": "New Test Finding",
            "description": "Description of the finding",
            "financial_impact": "1000.00",
        }

        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings",
            json=finding_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == finding_data["title"]
        assert data["finding_type"] == finding_data["finding_type"]
        assert data["status"] == "draft"
        assert data["finding_number"] >= 1

    @pytest.mark.asyncio
    async def test_create_finding_all_types(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test creating findings with all types."""
        finding_types = ["irregularity", "deficiency", "recommendation", "observation"]

        for finding_type in finding_types:
            finding_data = {
                "finding_type": finding_type,
                "title": f"Test {finding_type}",
                "description": f"Description for {finding_type}",
            }

            response = await client.post(
                f"/api/audit-cases/{findings_audit_case['id']}/findings",
                json=finding_data,
                headers=auth_headers,
            )

            assert response.status_code == 201
            assert response.json()["finding_type"] == finding_type

    @pytest.mark.asyncio
    async def test_create_finding_with_error_category(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test creating finding with error category."""
        finding_data = {
            "finding_type": "irregularity",
            "error_category": "ineligible_expenditure",
            "title": "Ineligible Expenditure Finding",
            "description": "This expenditure is not eligible",
            "financial_impact": "5000.00",
        }

        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings",
            json=finding_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["error_category"] == "ineligible_expenditure"

    @pytest.mark.asyncio
    async def test_create_finding_systemic(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test creating systemic finding."""
        finding_data = {
            "finding_type": "deficiency",
            "title": "Systemic Issue",
            "description": "This is a systemic problem",
            "is_systemic": True,
        }

        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings",
            json=finding_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert response.json()["is_systemic"] is True

    @pytest.mark.asyncio
    async def test_create_finding_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating finding for non-existent case."""
        fake_case_id = str(uuid.uuid4())
        finding_data = {
            "finding_type": "irregularity",
            "title": "Should Fail",
            "description": "Case does not exist",
        }

        response = await client.post(
            f"/api/audit-cases/{fake_case_id}/findings",
            json=finding_data,
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Get Finding Tests
# ==============================================================================


class TestGetFinding:
    """Tests for getting finding details."""

    @pytest.mark.asyncio
    async def test_get_finding_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test getting finding details."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_finding["id"]
        assert data["finding_number"] == test_finding["finding_number"]

    @pytest.mark.asyncio
    async def test_get_finding_not_found(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test getting non-existent finding."""
        fake_finding_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{fake_finding_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Update Finding Tests
# ==============================================================================


class TestUpdateFinding:
    """Tests for updating findings."""

    @pytest.mark.asyncio
    async def test_update_finding_title(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test updating finding title."""
        response = await client.patch(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_finding_financial_impact(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test updating financial impact."""
        response = await client.patch(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}",
            json={"financial_impact": "2500.50"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert float(response.json()["financial_impact"]) == 2500.50

    @pytest.mark.asyncio
    async def test_update_finding_corrective_action(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test updating corrective action."""
        response = await client.patch(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}",
            json={"corrective_action": "Refund the amount"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["corrective_action"] == "Refund the amount"

    @pytest.mark.asyncio
    async def test_update_finding_not_found(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test updating non-existent finding."""
        fake_finding_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{fake_finding_id}",
            json={"title": "Should Fail"},
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Delete Finding Tests
# ==============================================================================


class TestDeleteFinding:
    """Tests for deleting findings."""

    @pytest.mark.asyncio
    async def test_delete_draft_finding_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_db,
    ):
        """Test successful deletion of draft finding."""
        # Create a finding to delete
        finding_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_findings (id, audit_case_id, finding_number,
                    finding_type, title, description, status, is_systemic,
                    response_requested, created_at, updated_at)
                VALUES (:id, :audit_case_id, 99, 'observation',
                    'To Delete', 'Will be deleted', 'draft', false,
                    false, :created_at, :updated_at)
                """
            ),
            {
                "id": finding_id,
                "audit_case_id": findings_audit_case["id"],
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{finding_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{finding_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_confirmed_finding_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        confirmed_finding: dict,
    ):
        """Test that confirmed findings cannot be deleted."""
        response = await client.delete(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{confirmed_finding['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_finding_not_found(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test deleting non-existent finding."""
        fake_finding_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{fake_finding_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Confirm Finding Tests
# ==============================================================================


class TestConfirmFinding:
    """Tests for confirming findings."""

    @pytest.mark.asyncio
    async def test_confirm_draft_finding(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test confirming a draft finding."""
        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}/confirm",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_confirm_already_confirmed_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        confirmed_finding: dict,
    ):
        """Test that already confirmed findings cannot be confirmed again."""
        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{confirmed_finding['id']}/confirm",
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_confirm_finding_not_found(
        self, client: AsyncClient, auth_headers: dict, findings_audit_case: dict
    ):
        """Test confirming non-existent finding."""
        fake_finding_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{fake_finding_id}/confirm",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Resolve Finding Tests
# ==============================================================================


class TestResolveFinding:
    """Tests for resolving findings."""

    @pytest.mark.asyncio
    async def test_resolve_confirmed_finding(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        confirmed_finding: dict,
    ):
        """Test resolving a confirmed finding."""
        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{confirmed_finding['id']}/resolve",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_resolve_with_corrective_action(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_db,
    ):
        """Test resolving with corrective action."""
        # Create confirmed finding
        finding_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await test_db.execute(
            text(
                """
                INSERT INTO audit_case_findings (id, audit_case_id, finding_number,
                    finding_type, title, description, status, is_systemic,
                    response_requested, created_at, updated_at)
                VALUES (:id, :audit_case_id, 98, 'deficiency',
                    'To Resolve', 'Will be resolved', 'confirmed', false,
                    false, :created_at, :updated_at)
                """
            ),
            {
                "id": finding_id,
                "audit_case_id": findings_audit_case["id"],
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{finding_id}/resolve?corrective_action=Amount%20refunded",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["corrective_action"] == "Amount refunded"

    @pytest.mark.asyncio
    async def test_resolve_draft_finding_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test that draft findings cannot be resolved."""
        response = await client.post(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/{test_finding['id']}/resolve",
            headers=auth_headers,
        )

        assert response.status_code == 400


# ==============================================================================
# Statistics Tests
# ==============================================================================


class TestFindingsStatistics:
    """Tests for findings statistics."""

    @pytest.mark.asyncio
    async def test_get_findings_summary(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_finding: dict,
    ):
        """Test getting findings summary."""
        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/stats/summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_type" in data
        assert "total_financial_impact" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_summary_with_financial_impact(
        self,
        client: AsyncClient,
        auth_headers: dict,
        findings_audit_case: dict,
        test_db,
    ):
        """Test summary includes financial impact."""
        # Create findings with financial impact
        now = datetime.now(timezone.utc)
        for i, amount in enumerate([1000, 2000, 3000]):
            finding_id = str(uuid.uuid4())
            await test_db.execute(
                text(
                    """
                    INSERT INTO audit_case_findings (id, audit_case_id, finding_number,
                        finding_type, title, description, status, is_systemic,
                        response_requested, financial_impact, created_at, updated_at)
                    VALUES (:id, :audit_case_id, :num, 'irregularity',
                        :title, 'Description', 'draft', false, false, :amount,
                        :created_at, :updated_at)
                    """
                ),
                {
                    "id": finding_id,
                    "audit_case_id": findings_audit_case["id"],
                    "num": 100 + i,
                    "title": f"Finding {i}",
                    "amount": amount,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        await test_db.commit()

        response = await client.get(
            f"/api/audit-cases/{findings_audit_case['id']}/findings/stats/summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_financial_impact"] >= 6000.0

    @pytest.mark.asyncio
    async def test_get_summary_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting summary for non-existent case."""
        fake_case_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{fake_case_id}/findings/stats/summary",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Access Control Tests
# ==============================================================================


class TestFindingsAccessControl:
    """Tests for findings access control."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_findings(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_db,
    ):
        """Test that users cannot access findings from other tenants."""
        # Create case in different tenant
        other_tenant_id = str(uuid.uuid4())
        other_case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, 'Other Findings Tenant', 'group', 'active', :now, :now)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": uuid.UUID(other_tenant_id), "now": now},
        )

        await test_db.execute(
            text(
                """
                INSERT INTO audit_cases (id, tenant_id, case_number, project_name,
                    beneficiary_name, status, audit_type, is_sample, requires_follow_up,
                    custom_data, created_at, updated_at)
                VALUES (:id, :tenant_id, 'OTHER-FIND-001', 'Other Tenant Case',
                    'Other Beneficiary', 'in_progress', 'operation', false, false,
                    '{}', :now, :now)
                """
            ),
            {
                "id": other_case_id,
                "tenant_id": uuid.UUID(other_tenant_id),
                "now": now,
            },
        )
        await test_db.commit()

        # Try to access other tenant's findings
        response = await client.get(
            f"/api/audit-cases/{other_case_id}/findings",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Cleanup
# ==============================================================================


class TestFindingsCleanup:
    """Cleanup test data after findings tests."""

    @pytest.mark.asyncio
    async def test_cleanup_findings_data(self, test_db):
        """Clean up test findings data."""
        try:
            # Clean up findings
            await test_db.execute(
                text(
                    "DELETE FROM audit_case_findings WHERE title LIKE '%Test%' "
                    "OR title LIKE '%Finding%' OR title LIKE '%Delete%' "
                    "OR title LIKE '%Resolve%'"
                )
            )
            # Clean up audit cases
            await test_db.execute(
                text(
                    "DELETE FROM audit_cases WHERE case_number LIKE 'FIND-%' "
                    "OR case_number LIKE 'OTHER-FIND-%'"
                )
            )
            # Clean up tenants
            await test_db.execute(
                text("DELETE FROM tenants WHERE name = 'Other Findings Tenant'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
