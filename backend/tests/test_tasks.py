"""Tests for tasks router."""
import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_task(client, auth_headers):
    """Test creating a new task."""
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "priority": 3,
            "estimated_minutes": 30,
            "category": "work",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == 3
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks(client, auth_headers):
    """Test listing tasks with filters."""
    # Create some tasks
    for i in range(5):
        client.post(
            "/api/v1/tasks",
            json={"title": f"Task {i}", "priority": (i % 4) + 1},
            headers=auth_headers,
        )

    # List tasks
    response = client.get("/api/v1/tasks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) > 0
    assert "has_more" in data


@pytest.mark.asyncio
async def test_get_task(client, auth_headers):
    """Test getting a specific task."""
    # Create task
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Get Task Test"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Get task
    response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Get Task Test"


@pytest.mark.asyncio
async def test_get_task_not_found(client, auth_headers):
    """Test getting a non-existent task."""
    response = client.get(
        "/api/v1/tasks/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_task(client, auth_headers):
    """Test updating a task."""
    # Create task
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Original Title"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Update task
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated Title", "priority": 4},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == 4


@pytest.mark.asyncio
async def test_delete_task(client, auth_headers):
    """Test soft-deleting a task."""
    # Create task
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Delete Me"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Delete task
    response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Verify it's deleted (returns 404)
    get_response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_complete_task(client, auth_headers):
    """Test marking a task as complete."""
    # Create task
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Complete Me"},
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Complete task
    response = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_filter_tasks_by_priority(client, auth_headers):
    """Test filtering tasks by priority."""
    # Create tasks with different priorities
    for priority in [1, 2, 3, 4]:
        client.post(
            "/api/v1/tasks",
            json={"title": f"Priority {priority}", "priority": priority},
            headers=auth_headers,
        )

    # Filter by high priority
    response = client.get(
        "/api/v1/tasks?priority=3",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    for task in data["tasks"]:
        assert task["priority"] == 3