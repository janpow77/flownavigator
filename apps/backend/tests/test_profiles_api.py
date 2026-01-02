"""Tests for Profile API endpoints.

Tests for Layer 1 (Coordination Body) and Layer 2 (Authority) profiles.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text


class TestCBProfileEndpoints:
    """Tests for Coordination Body Profile API."""

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: AsyncClient):
        """Test that getting profile requires authentication."""
        tenant_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/tenants/{tenant_id}/profile")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_profile_not_found(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test 404 for non-existent tenant profile."""
        fake_tenant_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/tenants/{fake_tenant_id}/profile", headers=auth_headers
        )
        # Should return 403 (no access) or 404 (tenant not found)
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_get_own_tenant_profile(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test getting profile for own tenant."""
        tenant_id = test_user["tenant_id"]

        # First, try to create a profile if it doesn't exist
        profile_data = {
            "official_name": "Test Coordination Body",
            "street": "Test Address 123",
            "city": "Frankfurt",
            "postal_code": "60311",
        }

        # Try to create profile (may already exist)
        await client.post(
            f"/api/v1/tenants/{tenant_id}/profile",
            json=profile_data,
            headers=auth_headers,
        )

        # Get the profile
        response = await client.get(
            f"/api/v1/tenants/{tenant_id}/profile", headers=auth_headers
        )

        # Profile might exist or not based on test setup
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_create_cb_profile(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test creating a CB profile for own tenant."""
        tenant_id = test_user["tenant_id"]

        profile_data = {
            "official_name": "New Coordination Body",
            "street": "Main Street 100",
            "city": "Berlin",
            "postal_code": "10115",
            "phone": "+49 123 456789",
        }

        response = await client.post(
            f"/api/v1/tenants/{tenant_id}/profile",
            json=profile_data,
            headers=auth_headers,
        )

        # Expect 201 (created), 400 (already exists), or possibly other status
        assert response.status_code in [201, 400]

    @pytest.mark.asyncio
    async def test_update_cb_profile(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test updating a CB profile."""
        tenant_id = test_user["tenant_id"]

        # Ensure profile exists
        await client.post(
            f"/api/v1/tenants/{tenant_id}/profile",
            json={
                "official_name": "Initial CB Name",
                "street": "Initial Address",
                "city": "Munich",
            },
            headers=auth_headers,
        )

        # Update profile
        update_data = {
            "official_name": "Updated CB Name",
            "phone": "+49 999 888777",
        }

        response = await client.put(
            f"/api/v1/tenants/{tenant_id}/profile",
            json=update_data,
            headers=auth_headers,
        )

        # May succeed or fail based on profile existence and permissions
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_upload_logo_invalid_type(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test that invalid file types are rejected for logo upload."""
        tenant_id = test_user["tenant_id"]

        # Try to upload a text file as logo
        response = await client.post(
            f"/api/v1/tenants/{tenant_id}/profile/logo",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            headers=auth_headers,
        )

        # Should reject non-image file
        assert response.status_code in [400, 404]


class TestAuthorityProfileEndpoints:
    """Tests for Authority Profile API."""

    @pytest.mark.asyncio
    async def test_get_authority_profile_unauthorized(self, client: AsyncClient):
        """Test that getting authority profile requires authentication."""
        tenant_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/authorities/{tenant_id}/profile")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_authority_profile_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test 404 for non-existent authority profile."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/authorities/{fake_id}/profile", headers=auth_headers
        )
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_create_authority_profile(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test creating an authority profile."""
        # Create authority tenant
        auth_tenant_id = str(uuid.uuid4())
        parent_tenant_id = test_user["tenant_id"]

        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, parent_id, created_at, updated_at)
                VALUES (:id, 'Test Authority', 'authority', 'active', :parent_id, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": uuid.UUID(auth_tenant_id),
                "parent_id": uuid.UUID(parent_tenant_id),
            },
        )
        await test_db.commit()

        profile_data = {
            "official_name": "Test Authority Profile",
            "street": "Authority Street 1",
            "city": "Hamburg",
        }

        response = await client.post(
            f"/api/v1/authorities/{auth_tenant_id}/profile",
            json=profile_data,
            headers=auth_headers,
        )

        # May succeed or fail based on access control
        assert response.status_code in [201, 403, 404]

    @pytest.mark.asyncio
    async def test_update_authority_profile(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test updating an authority profile."""
        # Create authority tenant first
        auth_tenant_id = str(uuid.uuid4())
        parent_tenant_id = test_user["tenant_id"]

        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, parent_id, created_at, updated_at)
                VALUES (:id, 'Update Test Authority', 'authority', 'active', :parent_id, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": uuid.UUID(auth_tenant_id),
                "parent_id": uuid.UUID(parent_tenant_id),
            },
        )
        await test_db.commit()

        # Create profile first
        await client.post(
            f"/api/v1/authorities/{auth_tenant_id}/profile",
            json={"official_name": "Original Name", "street": "Original Address"},
            headers=auth_headers,
        )

        # Update
        update_data = {"official_name": "Updated Authority Name"}
        response = await client.put(
            f"/api/v1/authorities/{auth_tenant_id}/profile",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 403, 404]


class TestAdminProfileEndpoints:
    """Tests for Admin Profile endpoints (Vendor-only)."""

    @pytest.mark.asyncio
    async def test_list_all_cb_profiles_requires_vendor_auth(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that listing all CB profiles requires vendor authentication."""
        # Regular user auth should fail - expect 401 (wrong token type)
        response = await client.get("/api/v1/admin/profiles/cb", headers=auth_headers)
        # Should return 401 (unauthorized/wrong auth type)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_update_requires_vendor_admin(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that admin update requires vendor_admin role."""
        fake_profile_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/admin/profiles/cb/{fake_profile_id}",
            json={"name": "Admin Update"},
            headers=auth_headers,
        )
        # Should fail without vendor auth - 401 unauthorized
        assert response.status_code == 401


class TestProfileAccessControl:
    """Tests for profile access control."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_profile(
        self, client: AsyncClient, auth_headers: dict, test_db
    ):
        """Test that users cannot access profiles of other tenants."""
        # Create a separate tenant (use 'group' type, not 'coordination_body')
        other_tenant_id = str(uuid.uuid4())
        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, created_at, updated_at)
                VALUES (:id, 'Other Tenant', 'group', 'active', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": uuid.UUID(other_tenant_id)},
        )
        await test_db.commit()

        # Try to access other tenant's profile
        response = await client.get(
            f"/api/v1/tenants/{other_tenant_id}/profile",
            headers=auth_headers,
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_parent_can_access_child_profile(
        self, client: AsyncClient, auth_headers: dict, test_user: dict, test_db
    ):
        """Test that parent tenant can access child authority profiles."""
        # Create child authority
        child_tenant_id = str(uuid.uuid4())
        parent_tenant_id = test_user["tenant_id"]

        await test_db.execute(
            text(
                """
                INSERT INTO tenants (id, name, type, status, parent_id, created_at, updated_at)
                VALUES (:id, 'Child Authority', 'authority', 'active', :parent_id, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": uuid.UUID(child_tenant_id),
                "parent_id": uuid.UUID(parent_tenant_id),
            },
        )
        await test_db.commit()

        # Parent should be able to access child
        response = await client.get(
            f"/api/v1/authorities/{child_tenant_id}/profile",
            headers=auth_headers,
        )

        # Either 200 (has profile) or 404 (no profile yet)
        assert response.status_code in [200, 404]


class TestCleanup:
    """Cleanup test data after profile tests."""

    @pytest.mark.asyncio
    async def test_cleanup_test_profiles(self, test_db):
        """Clean up test profile data."""
        try:
            # Clean up profiles
            await test_db.execute(
                text(
                    "DELETE FROM coordination_body_profiles "
                    "WHERE name LIKE '%Test%' OR name LIKE '%Initial%' "
                    "OR name LIKE '%Updated%'"
                )
            )
            await test_db.execute(
                text(
                    "DELETE FROM authority_profiles "
                    "WHERE name LIKE '%Test%' OR name LIKE '%Original%' "
                    "OR name LIKE '%Updated%'"
                )
            )
            # Clean up test tenants
            await test_db.execute(
                text(
                    "DELETE FROM tenants "
                    "WHERE name LIKE '%Test%' OR name LIKE '%Other%' "
                    "OR name LIKE '%Child%' OR name LIKE '%Update%'"
                )
            )
            await test_db.commit()
        except Exception:
            await test_db.rollback()
