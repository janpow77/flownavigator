"""Tests for Document Box API endpoints.

Tests for document upload, download, verification and management
within audit cases.
"""

import io
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest_asyncio.fixture
async def doc_audit_case(test_db, test_user) -> dict:
    """Create an audit case for document tests."""
    case_id = str(uuid.uuid4())
    tenant_id = test_user["tenant_id"]
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO audit_cases (id, tenant_id, case_number, project_name,
                beneficiary_name, status, audit_type, is_sample, requires_follow_up,
                custom_data, created_at, updated_at)
            VALUES (:id, :tenant_id, 'DOC-2024-001', 'Document Test Project',
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
async def document_box(test_db, doc_audit_case, test_user) -> dict:
    """Create a document box for the audit case."""
    box_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO document_boxes (id, tenant_id, audit_case_id,
                ai_verification_enabled, ai_config, created_at, updated_at)
            VALUES (:id, :tenant_id, :audit_case_id, false, '{}',
                :created_at, :updated_at)
            """
        ),
        {
            "id": box_id,
            "tenant_id": uuid.UUID(doc_audit_case["tenant_id"]),
            "audit_case_id": doc_audit_case["id"],
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {"id": box_id, "audit_case_id": doc_audit_case["id"]}


@pytest_asyncio.fixture
async def test_document(test_db, document_box, test_user) -> dict:
    """Create a test document."""
    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    await test_db.execute(
        text(
            """
            INSERT INTO box_documents (id, tenant_id, box_id, file_name, file_size,
                mime_type, storage_path, category, uploaded_by, uploaded_at,
                created_at, updated_at)
            VALUES (:id, :tenant_id, :box_id, 'test_document.pdf', 1024,
                'application/pdf', '/tmp/test/doc.pdf', 'belege', :uploaded_by,
                :uploaded_at, :created_at, :updated_at)
            """
        ),
        {
            "id": doc_id,
            "tenant_id": uuid.UUID(test_user["tenant_id"]),
            "box_id": document_box["id"],
            "uploaded_by": test_user["id"],
            "uploaded_at": now,
            "created_at": now,
            "updated_at": now,
        },
    )
    await test_db.commit()

    return {
        "id": doc_id,
        "box_id": document_box["id"],
        "file_name": "test_document.pdf",
    }


# ==============================================================================
# Authentication Tests
# ==============================================================================


class TestDocumentBoxAuthentication:
    """Tests for document box authentication."""

    @pytest.mark.asyncio
    async def test_list_documents_unauthorized(
        self, client: AsyncClient, doc_audit_case: dict
    ):
        """Test that listing documents requires authentication."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_document_unauthorized(
        self, client: AsyncClient, doc_audit_case: dict
    ):
        """Test that uploading documents requires authentication."""
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        response = await client.post(
            f"/api/audit-cases/{doc_audit_case['id']}/documents",
            files=files,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_document_unauthorized(
        self, client: AsyncClient, doc_audit_case: dict
    ):
        """Test that getting document requires authentication."""
        fake_doc_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{fake_doc_id}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_document_unauthorized(
        self, client: AsyncClient, doc_audit_case: dict
    ):
        """Test that deleting document requires authentication."""
        fake_doc_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{fake_doc_id}"
        )
        assert response.status_code == 401


# ==============================================================================
# List Documents Tests
# ==============================================================================


class TestListDocuments:
    """Tests for listing documents."""

    @pytest.mark.asyncio
    async def test_list_documents_empty(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test listing documents when none exist."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_documents_with_items(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test listing documents with existing items."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test filtering documents by category."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents?category=belege",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "belege"

    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        document_box: dict,
        test_db,
        test_user,
    ):
        """Test document pagination."""
        # Create multiple documents
        now = datetime.now(timezone.utc)
        for i in range(5):
            doc_id = str(uuid.uuid4())
            await test_db.execute(
                text(
                    """
                    INSERT INTO box_documents (id, tenant_id, box_id, file_name,
                        file_size, mime_type, storage_path, category, uploaded_by,
                        uploaded_at, created_at, updated_at)
                    VALUES (:id, :tenant_id, :box_id, :file_name, 1024,
                        'application/pdf', '/tmp/test/doc.pdf', 'sonstige',
                        :uploaded_by, :uploaded_at, :created_at, :updated_at)
                    """
                ),
                {
                    "id": doc_id,
                    "tenant_id": uuid.UUID(test_user["tenant_id"]),
                    "box_id": document_box["id"],
                    "file_name": f"doc_{i}.pdf",
                    "uploaded_by": test_user["id"],
                    "uploaded_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        await test_db.commit()

        # Test pagination
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents?page=1&page_size=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["pages"] >= 1

    @pytest.mark.asyncio
    async def test_list_documents_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing documents for non-existent case."""
        fake_case_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{fake_case_id}/documents",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ==============================================================================
# Upload Document Tests
# ==============================================================================


class TestUploadDocument:
    """Tests for uploading documents."""

    @pytest.mark.asyncio
    async def test_upload_document_success(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test successful document upload."""
        file_content = b"Test PDF content for upload"
        files = {"file": ("test_upload.pdf", file_content, "application/pdf")}
        data = {"category": "belege"}

        response = await client.post(
            f"/api/audit-cases/{doc_audit_case['id']}/documents",
            files=files,
            data=data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        result = response.json()
        assert result["file_name"] == "test_upload.pdf"
        assert result["category"] == "belege"
        assert result["file_size"] == len(file_content)
        assert result["mime_type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_upload_document_default_category(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test upload uses default category when not specified."""
        files = {"file": ("default_cat.pdf", b"content", "application/pdf")}

        response = await client.post(
            f"/api/audit-cases/{doc_audit_case['id']}/documents",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 201
        result = response.json()
        assert result["category"] == "sonstige"

    @pytest.mark.asyncio
    async def test_upload_document_all_categories(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test upload with all valid categories."""
        categories = [
            "belege",
            "bescheide",
            "korrespondenz",
            "vertraege",
            "nachweise",
            "sonstige",
        ]

        for category in categories:
            files = {"file": (f"{category}.pdf", b"content", "application/pdf")}
            data = {"category": category}

            response = await client.post(
                f"/api/audit-cases/{doc_audit_case['id']}/documents",
                files=files,
                data=data,
                headers=auth_headers,
            )

            assert response.status_code == 201
            assert response.json()["category"] == category

    @pytest.mark.asyncio
    async def test_upload_document_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test upload to non-existent case."""
        fake_case_id = str(uuid.uuid4())
        files = {"file": ("test.pdf", b"content", "application/pdf")}

        response = await client.post(
            f"/api/audit-cases/{fake_case_id}/documents",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_document_no_file(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test upload without file raises error."""
        response = await client.post(
            f"/api/audit-cases/{doc_audit_case['id']}/documents",
            headers=auth_headers,
        )

        assert response.status_code == 422


# ==============================================================================
# Get Document Tests
# ==============================================================================


class TestGetDocument:
    """Tests for getting document details."""

    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test getting document details."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{test_document['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_document["id"]
        assert data["file_name"] == test_document["file_name"]

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test getting non-existent document."""
        fake_doc_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{fake_doc_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_wrong_case(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_document: dict,
        test_db,
        test_user,
    ):
        """Test getting document from wrong case returns 404."""
        # Create another case
        other_case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await test_db.execute(
            text(
                """
                INSERT INTO audit_cases (id, tenant_id, case_number, project_name,
                    beneficiary_name, status, audit_type, is_sample, requires_follow_up,
                    custom_data, created_at, updated_at)
                VALUES (:id, :tenant_id, 'OTHER-001', 'Other Project',
                    'Other Beneficiary', 'in_progress', 'operation', false, false,
                    '{}', :created_at, :updated_at)
                """
            ),
            {
                "id": other_case_id,
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        # Try to get document from wrong case
        response = await client.get(
            f"/api/audit-cases/{other_case_id}/documents/{test_document['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Update Document Tests
# ==============================================================================


class TestUpdateDocument:
    """Tests for updating documents."""

    @pytest.mark.asyncio
    async def test_update_document_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test updating document category."""
        response = await client.patch(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{test_document['id']}",
            json={"category": "vertraege"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "vertraege"

    @pytest.mark.asyncio
    async def test_update_document_manual_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test updating document verification status."""
        response = await client.patch(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{test_document['id']}",
            json={"manual_status": "verified"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["manual_status"] == "verified"
        assert data["manual_verified_by"] is not None
        assert data["manual_verified_at"] is not None

    @pytest.mark.asyncio
    async def test_update_document_all_statuses(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        document_box: dict,
        test_db,
        test_user,
    ):
        """Test all valid verification statuses."""
        statuses = ["pending", "verified", "rejected", "unclear"]

        for status in statuses:
            # Create fresh document for each status
            doc_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            await test_db.execute(
                text(
                    """
                    INSERT INTO box_documents (id, tenant_id, box_id, file_name,
                        file_size, mime_type, storage_path, category, uploaded_by,
                        uploaded_at, created_at, updated_at)
                    VALUES (:id, :tenant_id, :box_id, :file_name, 1024,
                        'application/pdf', '/tmp/test/doc.pdf', 'sonstige',
                        :uploaded_by, :uploaded_at, :created_at, :updated_at)
                    """
                ),
                {
                    "id": doc_id,
                    "tenant_id": uuid.UUID(test_user["tenant_id"]),
                    "box_id": document_box["id"],
                    "file_name": f"status_{status}.pdf",
                    "uploaded_by": test_user["id"],
                    "uploaded_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await test_db.commit()

            response = await client.patch(
                f"/api/audit-cases/{doc_audit_case['id']}/documents/{doc_id}",
                json={"manual_status": status},
                headers=auth_headers,
            )

            assert response.status_code == 200
            assert response.json()["manual_status"] == status

    @pytest.mark.asyncio
    async def test_update_document_remarks(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test updating document remarks."""
        response = await client.patch(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{test_document['id']}",
            json={"manual_remarks": "This document needs review"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["manual_remarks"] == "This document needs review"

    @pytest.mark.asyncio
    async def test_update_document_not_found(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test updating non-existent document."""
        fake_doc_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{fake_doc_id}",
            json={"category": "belege"},
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Delete Document Tests
# ==============================================================================


class TestDeleteDocument:
    """Tests for deleting documents."""

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        document_box: dict,
        test_db,
        test_user,
    ):
        """Test successful document deletion."""
        # Create a document to delete
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await test_db.execute(
            text(
                """
                INSERT INTO box_documents (id, tenant_id, box_id, file_name,
                    file_size, mime_type, storage_path, category, uploaded_by,
                    uploaded_at, created_at, updated_at)
                VALUES (:id, :tenant_id, :box_id, 'to_delete.pdf', 1024,
                    'application/pdf', '/tmp/test/nonexistent.pdf', 'sonstige',
                    :uploaded_by, :uploaded_at, :created_at, :updated_at)
                """
            ),
            {
                "id": doc_id,
                "tenant_id": uuid.UUID(test_user["tenant_id"]),
                "box_id": document_box["id"],
                "uploaded_by": test_user["id"],
                "uploaded_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        await test_db.commit()

        response = await client.delete(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{doc_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify document is deleted
        get_response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{doc_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test deleting non-existent document."""
        fake_doc_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/{fake_doc_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Document Box Info Tests
# ==============================================================================


class TestDocumentBoxInfo:
    """Tests for document box information."""

    @pytest.mark.asyncio
    async def test_get_box_info_empty(
        self, client: AsyncClient, auth_headers: dict, doc_audit_case: dict
    ):
        """Test getting box info when no box exists."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/box/info",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["audit_case_id"] == doc_audit_case["id"]
        assert data["documents_count"] == 0
        assert data["ai_verification_enabled"] is False

    @pytest.mark.asyncio
    async def test_get_box_info_with_documents(
        self,
        client: AsyncClient,
        auth_headers: dict,
        doc_audit_case: dict,
        test_document: dict,
    ):
        """Test getting box info with documents."""
        response = await client.get(
            f"/api/audit-cases/{doc_audit_case['id']}/documents/box/info",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["documents_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_box_info_case_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting box info for non-existent case."""
        fake_case_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/audit-cases/{fake_case_id}/documents/box/info",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Access Control Tests
# ==============================================================================


class TestDocumentAccessControl:
    """Tests for document access control."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_documents(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_db,
    ):
        """Test that users cannot access documents from other tenants."""
        # Create case in different tenant
        other_tenant_id = str(uuid.uuid4())
        other_case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, 'Other Tenant', 'group', 'active', :now, :now)
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
                VALUES (:id, :tenant_id, 'OTHER-001', 'Other Tenant Case',
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

        # Try to access other tenant's case
        response = await client.get(
            f"/api/audit-cases/{other_case_id}/documents",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ==============================================================================
# Cleanup
# ==============================================================================


class TestDocumentBoxCleanup:
    """Cleanup test data after document box tests."""

    @pytest.mark.asyncio
    async def test_cleanup_document_data(self, test_db):
        """Clean up test document data."""
        try:
            # Clean up documents
            await test_db.execute(
                text(
                    "DELETE FROM box_documents WHERE file_name LIKE '%test%' "
                    "OR file_name LIKE '%doc_%' OR file_name LIKE '%status_%' "
                    "OR file_name LIKE '%upload%' OR file_name LIKE '%delete%'"
                )
            )
            # Clean up document boxes
            await test_db.execute(
                text(
                    "DELETE FROM document_boxes WHERE audit_case_id IN "
                    "(SELECT id FROM audit_cases WHERE case_number LIKE 'DOC-%' "
                    "OR case_number LIKE 'OTHER-%')"
                )
            )
            # Clean up audit cases
            await test_db.execute(
                text(
                    "DELETE FROM audit_cases WHERE case_number LIKE 'DOC-%' "
                    "OR case_number LIKE 'OTHER-%'"
                )
            )
            # Clean up tenants
            await test_db.execute(
                text("DELETE FROM tenants WHERE name = 'Other Tenant'")
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
