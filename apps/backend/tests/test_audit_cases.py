"""Tests for audit cases endpoints."""

import pytest
from httpx import AsyncClient
from uuid import uuid4
import time


def unique_case_number():
    """Generate unique case number for tests."""
    return f"TEST-{int(time.time() * 1000)}"


@pytest.mark.asyncio
async def test_list_audit_cases_unauthorized(client: AsyncClient):
    """Test listing audit cases without authentication."""
    response = await client.get("/api/audit-cases")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_audit_cases(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing audit cases."""
    response = await client.get("/api/audit-cases", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_audit_case(
    client: AsyncClient,
    auth_headers: dict,
    cleanup_test_cases,
):
    """Test creating a new audit case."""
    case_num = unique_case_number()
    payload = {
        "case_number": case_num,
        "project_name": "Test Projekt",
        "beneficiary_name": "Test GmbH",
        "audit_type": "operation",
        "approved_amount": 100000.00,
    }
    response = await client.post(
        "/api/audit-cases",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["case_number"] == case_num
    assert data["project_name"] == "Test Projekt"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_audit_case_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting non-existent audit case."""
    fake_id = str(uuid4())
    response = await client.get(
        f"/api/audit-cases/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_and_get_audit_case(
    client: AsyncClient,
    auth_headers: dict,
    cleanup_test_cases,
):
    """Test creating and then retrieving an audit case."""
    case_num = unique_case_number()
    # Create
    payload = {
        "case_number": case_num,
        "project_name": "Get Test Projekt",
        "beneficiary_name": "Get Test GmbH",
        "audit_type": "system",
        "approved_amount": 50000.00,
    }
    create_response = await client.post(
        "/api/audit-cases",
        json=payload,
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    # Get
    get_response = await client.get(
        f"/api/audit-cases/{created['id']}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["case_number"] == case_num


@pytest.mark.asyncio
async def test_update_audit_case(
    client: AsyncClient,
    auth_headers: dict,
    cleanup_test_cases,
):
    """Test updating an audit case."""
    case_num = unique_case_number()
    # Create
    payload = {
        "case_number": case_num,
        "project_name": "Update Test",
        "beneficiary_name": "Update GmbH",
        "audit_type": "operation",
        "approved_amount": 75000.00,
    }
    create_response = await client.post(
        "/api/audit-cases",
        json=payload,
        headers=auth_headers,
    )
    created = create_response.json()

    # Update
    update_payload = {
        "status": "in_progress",
        "project_name": "Updated Project Name",
    }
    update_response = await client.patch(
        f"/api/audit-cases/{created['id']}",
        json=update_payload,
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "in_progress"
    assert data["project_name"] == "Updated Project Name"


@pytest.mark.asyncio
async def test_get_audit_statistics(
    client: AsyncClient,
    auth_headers: dict,
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
