"""Tests for findings endpoints."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_list_findings_unauthorized(client: AsyncClient):
    """Test listing findings without authentication."""
    fake_case_id = str(uuid4())
    response = await client.get(f"/api/audit-cases/{fake_case_id}/findings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_findings_case_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing findings for non-existent case."""
    fake_case_id = str(uuid4())
    response = await client.get(
        f"/api/audit-cases/{fake_case_id}/findings",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_and_list_findings(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test creating and listing findings."""
    # First create an audit case
    case_payload = {
        "case_number": "FINDING-TEST-001",
        "project_name": "Finding Test",
        "beneficiary_name": "Finding GmbH",
        "audit_type": "operation",
        "approved_amount": 100000.00,
    }
    case_response = await client.post(
        "/api/audit-cases",
        json=case_payload,
        headers=auth_headers,
    )
    assert case_response.status_code == 201
    case = case_response.json()

    # Create a finding
    finding_payload = {
        "finding_type": "irregularity",
        "title": "Test Feststellung",
        "description": "Beschreibung der Feststellung",
        "financial_impact": 5000.00,
    }
    finding_response = await client.post(
        f"/api/audit-cases/{case['id']}/findings",
        json=finding_payload,
        headers=auth_headers,
    )
    assert finding_response.status_code == 201
    finding = finding_response.json()
    assert finding["title"] == "Test Feststellung"
    assert finding["finding_type"] == "irregularity"

    # List findings
    list_response = await client.get(
        f"/api/audit-cases/{case['id']}/findings",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    findings = list_response.json()
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_confirm_finding(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test confirming a finding."""
    # Create case
    case_payload = {
        "case_number": "CONFIRM-TEST-001",
        "project_name": "Confirm Test",
        "beneficiary_name": "Confirm GmbH",
        "audit_type": "operation",
        "approved_amount": 50000.00,
    }
    case_response = await client.post(
        "/api/audit-cases",
        json=case_payload,
        headers=auth_headers,
    )
    case = case_response.json()

    # Create finding
    finding_payload = {
        "finding_type": "deficiency",
        "title": "Zu bestätigende Feststellung",
        "description": "Test",
    }
    finding_response = await client.post(
        f"/api/audit-cases/{case['id']}/findings",
        json=finding_payload,
        headers=auth_headers,
    )
    finding = finding_response.json()

    # Confirm finding
    confirm_response = await client.post(
        f"/api/audit-cases/{case['id']}/findings/{finding['id']}/confirm",
        headers=auth_headers,
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()
    assert confirmed["status"] == "confirmed"
