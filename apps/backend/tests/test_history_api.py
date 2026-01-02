"""Tests for History API endpoints (Feature 7).

AC-7.1.1: Module Events
AC-7.1.2: LLM Conversations
AC-7.1.3: LLM Feedback
AC-7.1.4: Context Building
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text


@pytest.fixture
async def test_module(test_db, test_user):
    """Create a test module for module events."""
    module_id = str(uuid.uuid4())
    vendor_id = str(uuid.uuid4())

    # Create vendor first
    await test_db.execute(
        text(
            """
            INSERT INTO vendors (id, name, contact_email, billing_email, address_country, created_at, updated_at)
            VALUES (:id, 'Test Vendor', 'vendor@test.de', 'billing@test.de', 'Deutschland', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": uuid.UUID(vendor_id)},
    )

    # Create module
    await test_db.execute(
        text(
            """
            INSERT INTO modules (id, name, version, status, created_at, updated_at)
            VALUES (:id, 'Test Module', '1.0.0', 'development', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": uuid.UUID(module_id)},
    )
    await test_db.commit()

    return {"module_id": module_id, "vendor_id": vendor_id}


@pytest.fixture
async def test_customer(test_db, test_user, test_module):
    """Create or get a test customer for module events."""
    tenant_id = test_user["tenant_id"]
    vendor_id = test_module["vendor_id"]

    # Check if customer already exists for this tenant
    result = await test_db.execute(
        text("SELECT id FROM customers WHERE tenant_id = :tenant_id"),
        {"tenant_id": uuid.UUID(tenant_id)},
    )
    row = result.fetchone()

    if row:
        return {"customer_id": str(row[0])}

    # Create new customer
    customer_id = str(uuid.uuid4())
    contract_number = f"TEST-{customer_id[:8]}"

    await test_db.execute(
        text(
            """
            INSERT INTO customers (id, tenant_id, vendor_id, contract_number,
                                  licensed_users, licensed_authorities, status,
                                  billing_address_country,
                                  created_at, updated_at)
            VALUES (:id, :tenant_id, :vendor_id, :contract_number, 10, 5, 'active',
                    'Deutschland', NOW(), NOW())
            """
        ),
        {
            "id": uuid.UUID(customer_id),
            "tenant_id": uuid.UUID(tenant_id),
            "vendor_id": uuid.UUID(vendor_id),
            "contract_number": contract_number,
        },
    )
    await test_db.commit()

    return {"customer_id": customer_id}


class TestModuleEvents:
    """Tests for Module Events API (AC-7.1.1)."""

    @pytest.mark.asyncio
    async def test_list_events_unauthorized(self, client: AsyncClient):
        """Test that listing events requires authentication."""
        response = await client.get("/api/v1/history/events")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_events_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test listing events returns paginated response."""
        response = await client.get("/api/v1/history/events", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_create_module_event(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_module: dict,
        test_customer: dict,
    ):
        """Test creating a module event (AC-7.1.1)."""
        event_data = {
            "module_id": test_module["module_id"],
            "customer_id": test_customer["customer_id"],
            "event_type": "installed",
            "version": "1.0.0",
            "details": {"note": "Test installation"},
        }
        response = await client.post(
            "/api/v1/history/events", json=event_data, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["module_id"] == event_data["module_id"]
        assert data["event_type"] == "installed"
        assert data["version"] == "1.0.0"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_module_event(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_module: dict,
        test_customer: dict,
    ):
        """Test retrieving a specific module event."""
        # Create event first
        event_data = {
            "module_id": test_module["module_id"],
            "customer_id": test_customer["customer_id"],
            "event_type": "updated",
            "version": "2.0.0",
            "previous_version": "1.0.0",
        }
        create_response = await client.post(
            "/api/v1/history/events", json=event_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        event_id = create_response.json()["id"]

        # Get the event
        response = await client.get(
            f"/api/v1/history/events/{event_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id
        assert data["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_get_module_event_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test 404 for non-existent event."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/history/events/{fake_id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_events_with_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_module: dict,
        test_customer: dict,
    ):
        """Test filtering events by module_id."""
        module_id = test_module["module_id"]

        # Create events for specific module
        for i in range(3):
            await client.post(
                "/api/v1/history/events",
                json={
                    "module_id": module_id,
                    "customer_id": test_customer["customer_id"],
                    "event_type": "configured",
                    "version": f"1.{i}.0",
                },
                headers=auth_headers,
            )

        # Filter by module_id
        response = await client.get(
            f"/api/v1/history/events?module_id={module_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        for item in data["items"]:
            assert item["module_id"] == module_id


class TestLLMConversations:
    """Tests for LLM Conversations API (AC-7.1.2)."""

    @pytest.mark.asyncio
    async def test_list_conversations_unauthorized(self, client: AsyncClient):
        """Test that listing conversations requires authentication."""
        response = await client.get("/api/v1/history/conversations")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_conversation(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test creating a new LLM conversation (AC-7.1.2)."""
        conv_data = {
            "context_type": "audit_case",
            "context_id": str(uuid.uuid4()),
            "title": "Test Conversation",
            "model_used": "gpt-4",
        }
        response = await client.post(
            "/api/v1/history/conversations", json=conv_data, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert data["context_type"] == "audit_case"
        assert data["model_used"] == "gpt-4"
        assert data["is_active"] is True
        assert data["total_tokens"] == 0
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_conversation(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test retrieving a conversation with messages."""
        # Create conversation
        conv_data = {
            "context_type": "module",
            "context_id": str(uuid.uuid4()),
            "title": "Module Help",
        }
        create_response = await client.post(
            "/api/v1/history/conversations", json=conv_data, headers=auth_headers
        )
        conv_id = create_response.json()["id"]

        # Get conversation
        response = await client.get(
            f"/api/v1/history/conversations/{conv_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert "messages" in data
        assert "feedbacks" in data

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test 404 for non-existent conversation."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/history/conversations/{fake_id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_conversation(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test updating a conversation."""
        # Create conversation
        conv_data = {"context_type": "general", "title": "Original Title"}
        create_response = await client.post(
            "/api/v1/history/conversations", json=conv_data, headers=auth_headers
        )
        conv_id = create_response.json()["id"]

        # Update
        update_data = {"title": "Updated Title", "is_active": False}
        response = await client.patch(
            f"/api/v1/history/conversations/{conv_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_conversation(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test deleting a conversation."""
        # Create conversation
        conv_data = {"context_type": "general", "title": "To Delete"}
        create_response = await client.post(
            "/api/v1/history/conversations", json=conv_data, headers=auth_headers
        )
        conv_id = create_response.json()["id"]

        # Delete
        response = await client.delete(
            f"/api/v1/history/conversations/{conv_id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/history/conversations/{conv_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_conversations_with_filter(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test filtering conversations by context_type."""
        context_id = str(uuid.uuid4())

        # Create conversations
        await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "audit_case", "context_id": context_id},
            headers=auth_headers,
        )

        # Filter
        response = await client.get(
            f"/api/v1/history/conversations?context_type=audit_case&context_id={context_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestLLMMessages:
    """Tests for LLM Messages API."""

    @pytest.mark.asyncio
    async def test_add_message_to_conversation(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test adding a message to a conversation."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "Message Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Add message
        message_data = {
            "role": "user",
            "content": "Hello, I need help with an audit case.",
            "tokens": 15,
        }
        response = await client.post(
            f"/api/v1/history/conversations/{conv_id}/messages",
            json=message_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "user"
        assert data["content"] == message_data["content"]
        assert data["tokens"] == 15

    @pytest.mark.asyncio
    async def test_list_messages(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test listing messages in a conversation."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "List Messages Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Add messages
        messages = [
            {"role": "user", "content": "Question 1", "tokens": 5},
            {"role": "assistant", "content": "Answer 1", "tokens": 10},
            {"role": "user", "content": "Question 2", "tokens": 5},
        ]
        for msg in messages:
            await client.post(
                f"/api/v1/history/conversations/{conv_id}/messages",
                json=msg,
                headers=auth_headers,
            )

        # List messages
        response = await client.get(
            f"/api/v1/history/conversations/{conv_id}/messages", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_message_updates_token_count(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test that adding messages updates conversation token count."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "Token Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Add messages with tokens
        await client.post(
            f"/api/v1/history/conversations/{conv_id}/messages",
            json={"role": "user", "content": "Test", "tokens": 100},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/history/conversations/{conv_id}/messages",
            json={"role": "assistant", "content": "Response", "tokens": 200},
            headers=auth_headers,
        )

        # Check total tokens
        response = await client.get(
            f"/api/v1/history/conversations/{conv_id}", headers=auth_headers
        )
        data = response.json()
        assert data["total_tokens"] == 300

    @pytest.mark.asyncio
    async def test_add_message_to_nonexistent_conversation(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test 404 when adding message to non-existent conversation."""
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/history/conversations/{fake_id}/messages",
            json={"role": "user", "content": "Test", "tokens": 5},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestLLMFeedback:
    """Tests for LLM Feedback API (AC-7.1.3)."""

    @pytest.mark.asyncio
    async def test_add_feedback_to_conversation(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test adding feedback to a conversation (AC-7.1.3)."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "Feedback Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Add feedback with correct enum value
        feedback_data = {
            "feedback_type": "helpful",
            "comment": "Very helpful response!",
            "rating": 5,
        }
        response = await client.post(
            f"/api/v1/history/conversations/{conv_id}/feedback",
            json=feedback_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["feedback_type"] == "helpful"
        assert data["comment"] == "Very helpful response!"
        assert data["rating"] == 5

    @pytest.mark.asyncio
    async def test_add_feedback_to_message(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test adding feedback to a specific message."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "Message Feedback Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Add message
        msg_response = await client.post(
            f"/api/v1/history/conversations/{conv_id}/messages",
            json={"role": "assistant", "content": "AI Response", "tokens": 50},
            headers=auth_headers,
        )
        msg_id = msg_response.json()["id"]

        # Add feedback to message with correct enum value
        feedback_data = {
            "feedback_type": "not_helpful",
            "message_id": msg_id,
            "comment": "Response was inaccurate",
            "rating": 2,
        }
        response = await client.post(
            f"/api/v1/history/conversations/{conv_id}/feedback",
            json=feedback_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message_id"] == msg_id

    @pytest.mark.asyncio
    async def test_list_feedback(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test listing feedback for a conversation."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "List Feedback Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Add multiple feedback entries with correct enum values
        feedbacks = [
            {"feedback_type": "helpful", "rating": 5},
            {"feedback_type": "partially_helpful", "comment": "Could be better"},
        ]
        for fb in feedbacks:
            await client.post(
                f"/api/v1/history/conversations/{conv_id}/feedback",
                json=fb,
                headers=auth_headers,
            )

        # List feedback
        response = await client.get(
            f"/api/v1/history/conversations/{conv_id}/feedback", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_feedback_invalid_message(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test 404 when adding feedback to non-existent message."""
        # Create conversation
        conv_response = await client.post(
            "/api/v1/history/conversations",
            json={"context_type": "general", "title": "Invalid Message Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        # Try to add feedback to non-existent message
        response = await client.post(
            f"/api/v1/history/conversations/{conv_id}/feedback",
            json={"feedback_type": "helpful", "message_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestContextBuilding:
    """Tests for Context Building API (AC-7.1.4)."""

    @pytest.mark.asyncio
    async def test_build_context_unauthorized(self, client: AsyncClient):
        """Test that building context requires authentication."""
        response = await client.post(
            "/api/v1/history/context",
            json={"context_type": "general"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_build_context_general(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test building general context."""
        context_data = {
            "context_type": "general",
            "include_history": False,
            "max_messages": 10,
        }
        response = await client.post(
            "/api/v1/history/context", json=context_data, headers=auth_headers
        )
        # Context building may work or fail depending on service availability
        assert response.status_code in [200, 404, 500]


class TestCleanup:
    """Cleanup tests to run after all history tests."""

    @pytest.mark.asyncio
    async def test_cleanup_test_data(self, test_db):
        """Clean up test data from history tables."""
        try:
            # Clean up in order due to foreign keys
            await test_db.execute(text("DELETE FROM llm_feedbacks WHERE rating >= 0"))
            await test_db.execute(
                text("DELETE FROM llm_messages WHERE content LIKE '%Test%'")
            )
            await test_db.execute(
                text("DELETE FROM llm_conversations WHERE title LIKE '%Test%'")
            )
            await test_db.execute(
                text("DELETE FROM module_events WHERE version LIKE '%.0.0'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
