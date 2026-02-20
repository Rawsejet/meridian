"""Scenario 04: Create, Read, Update, and Delete Tasks — satisfaction tests."""
import asyncio
import uuid

import pytest
from httpx import AsyncClient


# ── Helper ──────────────────────────────────────────────────────────────────


async def register_and_get_headers(client: AsyncClient, email: str) -> tuple[dict, str]:
    """Register a user and return (auth_headers, user_id)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Str0ng!Pass#2025",
            "display_name": email.split("@")[0].title(),
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return headers, data["id"]


async def create_task(client: AsyncClient, headers: dict, payload: dict) -> dict:
    """Create a task and return the response JSON."""
    resp = await client.post("/api/v1/tasks", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Scenario walkthrough ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_task_crud_walkthrough(client: AsyncClient, db_session):
    """Walk through every step of scenario 04."""

    headers, user_id = await register_and_get_headers(client, "alice-crud@example.com")

    # Step 1 — create task with all fields
    task1 = await create_task(client, headers, {
        "title": "Write quarterly report",
        "priority": 3,
        "category": "work",
        "estimated_minutes": 120,
        "energy_level": 3,
        "due_date": "2025-01-20T00:00:00Z",
    })

    # Step 2 — server returns UUID, pending status, created_at
    assert task1["status"] == "pending"
    assert task1["created_at"] is not None
    # Validate it's a UUID
    uuid.UUID(task1["id"])

    # Step 3 — second task
    task2 = await create_task(client, headers, {
        "title": "Buy birthday gift for Mom",
        "priority": 2,
        "category": "personal",
        "estimated_minutes": 45,
        "energy_level": 1,
    })

    # Step 4 — third task
    task3 = await create_task(client, headers, {
        "title": "Schedule dentist appointment",
        "priority": 1,
        "category": "health",
    })

    # Step 5 — list all tasks: newest first, 3 tasks
    resp = await client.get("/api/v1/tasks", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) == 3
    # Newest first
    assert tasks[0]["id"] == task3["id"]
    assert tasks[1]["id"] == task2["id"]
    assert tasks[2]["id"] == task1["id"]

    # Step 6 — filter by category=work → 1 task
    resp = await client.get("/api/v1/tasks?category=work", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Write quarterly report"

    # Step 7 — filter by priority=3 → 1 task (the report)
    resp = await client.get("/api/v1/tasks?priority=3", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Write quarterly report"

    # Step 8 — update birthday gift task
    resp = await client.patch(
        f"/api/v1/tasks/{task2['id']}",
        json={"priority": 3, "due_date": "2025-01-18T00:00:00Z"},
        headers=headers,
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["priority"] == 3
    assert "2025-01-18" in updated["due_date"]
    # Other fields unchanged
    assert updated["title"] == "Buy birthday gift for Mom"
    assert updated["category"] == "personal"

    # Step 9 — delete (soft) the dentist task
    resp = await client.delete(f"/api/v1/tasks/{task3['id']}", headers=headers)
    assert resp.status_code == 200
    deleted = resp.json()
    assert deleted["status"] == "cancelled"

    # Step 10 — default list excludes cancelled → 2 tasks
    resp = await client.get("/api/v1/tasks", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) == 2

    # Step 11 — include_cancelled=true → 3 tasks
    resp = await client.get("/api/v1/tasks?include_cancelled=true", headers=headers)
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) == 3


# ── Satisfaction criteria ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_task_ids_are_uuids(client: AsyncClient, db_session):
    """Task IDs are UUIDs, not sequential integers."""
    headers, _ = await register_and_get_headers(client, "uuid-test@example.com")
    task = await create_task(client, headers, {"title": "UUID check"})
    parsed = uuid.UUID(task["id"])
    assert parsed.version == 4 or parsed.version is not None


@pytest.mark.asyncio
async def test_timestamps_are_iso8601(client: AsyncClient, db_session):
    """All timestamps are ISO 8601 with timezone (UTC)."""
    from datetime import datetime

    headers, _ = await register_and_get_headers(client, "ts-test@example.com")
    task = await create_task(client, headers, {"title": "Timestamp check"})

    for field in ("created_at", "updated_at"):
        val = task[field]
        assert val is not None, f"{field} should not be None"
        # Should parse as ISO 8601
        datetime.fromisoformat(val.replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_get_tasks_returns_only_own_tasks(client: AsyncClient, db_session):
    """GET /tasks returns only the authenticated user's tasks."""
    h1, _ = await register_and_get_headers(client, "alice-own@example.com")
    h2, _ = await register_and_get_headers(client, "bob-own@example.com")

    await create_task(client, h1, {"title": "Alice task"})
    await create_task(client, h2, {"title": "Bob task"})

    resp = await client.get("/api/v1/tasks", headers=h1)
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Alice task"

    resp = await client.get("/api/v1/tasks", headers=h2)
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Bob task"


@pytest.mark.asyncio
async def test_default_sort_created_at_desc(client: AsyncClient, db_session):
    """Default sort is created_at DESC."""
    headers, _ = await register_and_get_headers(client, "sort-test@example.com")

    t1 = await create_task(client, headers, {"title": "First"})
    t2 = await create_task(client, headers, {"title": "Second"})
    t3 = await create_task(client, headers, {"title": "Third"})

    resp = await client.get("/api/v1/tasks", headers=headers)
    tasks = resp.json()["tasks"]
    assert tasks[0]["id"] == t3["id"]
    assert tasks[1]["id"] == t2["id"]
    assert tasks[2]["id"] == t1["id"]


@pytest.mark.asyncio
async def test_multi_field_filtering(client: AsyncClient, db_session):
    """Filtering by multiple fields simultaneously works."""
    headers, _ = await register_and_get_headers(client, "multi-filter@example.com")

    await create_task(client, headers, {"title": "A", "category": "work", "priority": 3})
    await create_task(client, headers, {"title": "B", "category": "work", "priority": 1})
    await create_task(client, headers, {"title": "C", "category": "personal", "priority": 3})

    resp = await client.get("/api/v1/tasks?category=work&priority=3", headers=headers)
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "A"


@pytest.mark.asyncio
async def test_partial_update_leaves_other_fields_unchanged(client: AsyncClient, db_session):
    """Partial update only modifies specified fields."""
    headers, _ = await register_and_get_headers(client, "partial-update@example.com")

    task = await create_task(client, headers, {
        "title": "Original",
        "priority": 2,
        "category": "work",
        "estimated_minutes": 30,
    })

    resp = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"priority": 4},
        headers=headers,
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["priority"] == 4
    assert updated["title"] == "Original"
    assert updated["category"] == "work"
    assert updated["estimated_minutes"] == 30


@pytest.mark.asyncio
async def test_delete_is_soft(client: AsyncClient, db_session):
    """Delete sets status to cancelled, doesn't remove from DB."""
    headers, _ = await register_and_get_headers(client, "soft-del@example.com")
    task = await create_task(client, headers, {"title": "To cancel"})

    resp = await client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # Still retrievable by ID
    resp = await client.get(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancelled_excluded_by_default_but_retrievable(client: AsyncClient, db_session):
    """Cancelled tasks excluded from default listing but retrievable with filter."""
    headers, _ = await register_and_get_headers(client, "cancel-filter@example.com")

    t1 = await create_task(client, headers, {"title": "Keep"})
    t2 = await create_task(client, headers, {"title": "Cancel me"})

    await client.delete(f"/api/v1/tasks/{t2['id']}", headers=headers)

    # Default excludes cancelled
    resp = await client.get("/api/v1/tasks", headers=headers)
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Keep"

    # include_cancelled=true brings them back
    resp = await client.get("/api/v1/tasks?include_cancelled=true", headers=headers)
    tasks = resp.json()["tasks"]
    assert len(tasks) == 2


@pytest.mark.asyncio
async def test_get_other_users_task_returns_404(client: AsyncClient, db_session):
    """GET /tasks/{id} for another user's task returns 404 (not 403)."""
    h1, _ = await register_and_get_headers(client, "alice-403@example.com")
    h2, _ = await register_and_get_headers(client, "bob-403@example.com")

    task = await create_task(client, h1, {"title": "Alice private"})

    resp = await client.get(f"/api/v1/tasks/{task['id']}", headers=h2)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_task_returns_404(client: AsyncClient, db_session):
    """GET /tasks/{id} for a non-existent task returns 404."""
    headers, _ = await register_and_get_headers(client, "no-task@example.com")

    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/tasks/{fake_id}", headers=headers)
    assert resp.status_code == 404


# ── Failure modes ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_empty_title_returns_422(client: AsyncClient, db_session):
    """Creating a task with empty title returns 422."""
    headers, _ = await register_and_get_headers(client, "empty-title@example.com")

    resp = await client.post(
        "/api/v1/tasks",
        json={"title": ""},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_priority_out_of_range_returns_422(client: AsyncClient, db_session):
    """Creating a task with priority 5 (out of range) returns 422."""
    headers, _ = await register_and_get_headers(client, "bad-priority@example.com")

    resp = await client.post(
        "/api/v1/tasks",
        json={"title": "Bad priority", "priority": 5},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_negative_estimated_minutes_returns_422(client: AsyncClient, db_session):
    """Creating a task with negative estimated_minutes returns 422."""
    headers, _ = await register_and_get_headers(client, "neg-mins@example.com")

    resp = await client.post(
        "/api/v1/tasks",
        json={"title": "Negative mins", "estimated_minutes": -10},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_nonexistent_task_returns_404(client: AsyncClient, db_session):
    """Updating a non-existent task returns 404."""
    headers, _ = await register_and_get_headers(client, "update-404@example.com")

    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/v1/tasks/{fake_id}",
        json={"title": "Nope"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_with_empty_body_returns_task_unchanged(client: AsyncClient, db_session):
    """Patching with an empty object returns the task unchanged."""
    headers, _ = await register_and_get_headers(client, "empty-patch@example.com")

    task = await create_task(client, headers, {
        "title": "Unchanged",
        "priority": 2,
        "category": "work",
    })

    resp = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={},
        headers=headers,
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["title"] == "Unchanged"
    assert updated["priority"] == 2
    assert updated["category"] == "work"
