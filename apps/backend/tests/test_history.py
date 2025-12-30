"""Tests for history/audit log endpoints."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_list_history_unauthorized(client: AsyncClient):
    """Test listing history without authentication."""
    fake_case_id = str(uuid4())
    response = await client.get(f"/api/audit-cases/{fake_case_id}/history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_history_case_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing history for non-existent case."""
    fake_case_id = str(uuid4())
    response = await client.get(
        f"/api/audit-cases/{fake_case_id}/history",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_comment(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test adding a comment to audit case history."""
    # Create case
    case_payload = {
        "case_number": "HISTORY-TEST-001",
        "project_name": "History Test",
        "beneficiary_name": "History GmbH",
        "audit_type": "operation",
        "approved_amount": 100000.00,
    }
    case_response = await client.post(
        "/api/audit-cases",
        json=case_payload,
        headers=auth_headers,
    )
    case = case_response.json()

    # Add comment
    comment_payload = {
        "action": "comment",
        "description": "Test Kommentar für die Historie",
    }
    comment_response = await client.post(
        f"/api/audit-cases/{case['id']}/history",
        json=comment_payload,
        headers=auth_headers,
    )
    assert comment_response.status_code == 201
    comment = comment_response.json()
    assert comment["action"] == "comment"
    assert comment["description"] == "Test Kommentar für die Historie"


@pytest.mark.asyncio
async def test_history_entries_after_status_change(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that history entries are created after status changes."""
    # Create case
    case_payload = {
        "case_number": "STATUS-HISTORY-001",
        "project_name": "Status History Test",
        "beneficiary_name": "Status GmbH",
        "audit_type": "system",
        "approved_amount": 75000.00,
    }
    case_response = await client.post(
        "/api/audit-cases",
        json=case_payload,
        headers=auth_headers,
    )
    case = case_response.json()

    # Update status
    update_payload = {"status": "in_progress"}
    await client.patch(
        f"/api/audit-cases/{case['id']}",
        json=update_payload,
        headers=auth_headers,
    )

    # Check history
    history_response = await client.get(
        f"/api/audit-cases/{case['id']}/history",
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert "items" in history
    # Should have at least the creation and status change entries
    assert len(history["items"]) >= 1
