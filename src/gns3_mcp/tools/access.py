"""Access/RBAC tools: users, groups, roles, privileges, and ACL management."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def _trim_user(u: dict[str, Any]) -> dict[str, Any]:
    keep = ("user_id", "username", "email", "full_name", "is_active", "is_superadmin")
    return {k: u[k] for k in keep if k in u}


def register(mcp: FastMCP) -> None:
    # --- read-only views ---
    @mcp.tool
    async def whoami() -> dict[str, Any]:
        """Return the currently authenticated user."""
        return _trim_user(await client().get("/access/users/me"))

    @mcp.tool
    async def users_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List user accounts."""
        items = await client().list("/access/users", limit=limit)
        return [_trim_user(u) for u in items]

    @mcp.tool
    async def user_get(user_id: str) -> dict[str, Any]:
        """Get a user account."""
        return _trim_user(await client().get(f"/access/users/{user_id}"))

    @mcp.tool
    async def user_groups(user_id: str) -> list[dict[str, Any]]:
        """List the groups a user belongs to."""
        return await client().get(f"/access/users/{user_id}/groups")

    @mcp.tool
    async def groups_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List user groups."""
        return await client().list("/access/groups", limit=limit)

    @mcp.tool
    async def group_members(group_id: str) -> list[dict[str, Any]]:
        """List members of a user group."""
        items = await client().get(f"/access/groups/{group_id}/members")
        return [_trim_user(u) for u in items]

    @mcp.tool
    async def roles_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List roles."""
        return await client().list("/access/roles", limit=limit)

    @mcp.tool
    async def role_privileges(role_id: str) -> list[dict[str, Any]]:
        """List the privileges granted to a role."""
        return await client().get(f"/access/roles/{role_id}/privileges")

    @mcp.tool
    async def privileges_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List all assignable privileges in the system."""
        return await client().list("/access/privileges", limit=limit)

    @mcp.tool
    async def acl_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List Access Control Entries (ACEs) in the ACL."""
        return await client().list("/access/acl", limit=limit)

    @mcp.tool
    async def acl_endpoints() -> list[dict[str, Any]]:
        """List the endpoints (resources) that ACEs can be attached to."""
        return await client().get("/access/acl/endpoints")

    if read_only():
        return

    # --- users ---
    @mcp.tool
    async def user_create(
        username: str,
        password: str,
        email: str | None = None,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> dict[str, Any]:
        """Create a user account."""
        body: dict[str, Any] = {"username": username, "password": password, "is_active": is_active}
        if email:
            body["email"] = email
        if full_name:
            body["full_name"] = full_name
        return _trim_user(await client().post("/access/users", json=body))

    @mcp.tool
    async def user_update(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a user (password, email, is_active, ...)."""
        return _trim_user(await client().put(f"/access/users/{user_id}", json=updates))

    @mcp.tool
    async def user_delete(user_id: str) -> str:
        """Delete a user account."""
        await client().delete(f"/access/users/{user_id}", parse=False)
        return f"User {user_id} deleted."

    # --- groups ---
    @mcp.tool
    async def group_create(name: str) -> dict[str, Any]:
        """Create a user group."""
        return await client().post("/access/groups", json={"name": name})

    @mcp.tool
    async def group_update(group_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a user group."""
        return await client().put(f"/access/groups/{group_id}", json=updates)

    @mcp.tool
    async def group_delete(group_id: str) -> str:
        """Delete a user group."""
        await client().delete(f"/access/groups/{group_id}", parse=False)
        return f"Group {group_id} deleted."

    @mcp.tool
    async def group_member_add(group_id: str, user_id: str) -> str:
        """Add a user to a group."""
        await client().put(f"/access/groups/{group_id}/members/{user_id}", parse=False)
        return f"User {user_id} added to group {group_id}."

    @mcp.tool
    async def group_member_remove(group_id: str, user_id: str) -> str:
        """Remove a user from a group."""
        await client().delete(f"/access/groups/{group_id}/members/{user_id}", parse=False)
        return f"User {user_id} removed from group {group_id}."

    # --- roles ---
    @mcp.tool
    async def role_create(name: str, description: str | None = None) -> dict[str, Any]:
        """Create a role."""
        body: dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        return await client().post("/access/roles", json=body)

    @mcp.tool
    async def role_update(role_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a role."""
        return await client().put(f"/access/roles/{role_id}", json=updates)

    @mcp.tool
    async def role_delete(role_id: str) -> str:
        """Delete a role."""
        await client().delete(f"/access/roles/{role_id}", parse=False)
        return f"Role {role_id} deleted."

    @mcp.tool
    async def role_privilege_grant(role_id: str, privilege_id: str) -> str:
        """Grant a privilege to a role."""
        await client().put(f"/access/roles/{role_id}/privileges/{privilege_id}", parse=False)
        return f"Privilege {privilege_id} granted to role {role_id}."

    @mcp.tool
    async def role_privilege_revoke(role_id: str, privilege_id: str) -> str:
        """Revoke a privilege from a role."""
        await client().delete(f"/access/roles/{role_id}/privileges/{privilege_id}", parse=False)
        return f"Privilege {privilege_id} revoked from role {role_id}."

    # --- ACL ---
    @mcp.tool
    async def acl_create(
        path: str, ace_type: str, role_id: str, propagate: bool = True,
        user_id: str | None = None, group_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an ACE binding a user or group to a role on a resource path.

        ace_type is 'user' or 'group'; provide the matching user_id or group_id.
        """
        body: dict[str, Any] = {
            "path": path, "ace_type": ace_type, "role_id": role_id, "propagate": propagate,
        }
        if user_id:
            body["user_id"] = user_id
        if group_id:
            body["group_id"] = group_id
        return await client().post("/access/acl", json=body)

    @mcp.tool
    async def acl_update(ace_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update an ACE."""
        return await client().put(f"/access/acl/{ace_id}", json=updates)

    @mcp.tool
    async def acl_delete(ace_id: str) -> str:
        """Delete an ACE."""
        await client().delete(f"/access/acl/{ace_id}", parse=False)
        return f"ACE {ace_id} deleted."
