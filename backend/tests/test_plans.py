"""Tests for daily plans router."""
import pytest
from datetime import datetime, date, timedelta


@pytest.mark.asyncio
async def test_create_plan(client, auth_headers):
    """Test creating a daily plan."""
    today = datetime.utcnow().date().isoformat()
    response = client.post(
        f"/api/v1/plans/{today}",
        json={
            "task_order": [],
            "notes": "My daily plan",
            "mood": 4,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "My daily plan"
    assert data["mood"] == 4


@pytest.mark.asyncio
async def test_get_plan(client, auth_headers):
    """Test getting a daily plan."""
    today = datetime.utcnow().date().isoformat()

    # Create plan
    client.post(
        f"/api/v1/plans/{today}",
        json={"task_order": [], "notes": "Test plan"},
        headers=auth_headers,
    )

    # Get plan
    response = client.get(
        f"/api/v1/plans/{today}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Test plan"


@pytest.mark.asyncio
async def test_list_plans(client, auth_headers):
    """Test listing plans for last N days."""
    response = client.get(
        "/api/v1/plans?days=7",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "plans" in data


@pytest.mark.asyncio
async def test_reorder_tasks(client, auth_headers):
    """Test reordering tasks in a plan."""
    today = datetime.utcnow().date().isoformat()

    # Create plan with some tasks
    client.post(
        f"/api/v1/plans/{today}",
        json={"task_order": ["task1", "task2", "task3"]},
        headers=auth_headers,
    )

    # Reorder
    response = client.patch(
        f"/api/v1/plans/{today}/reorder",
        json={"task_order": ["task3", "task1", "task2"]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_order"] == ["task3", "task1", "task2"]


@pytest.mark.asyncio
async def test_complete_plan(client, auth_headers):
    """Test completing a daily plan."""
    today = datetime.utcnow().date().isoformat()

    # Create plan
    client.post(
        f"/api/v1/plans/{today}",
        json={"task_order": ["task1", "task2"]},
        headers=auth_headers,
    )

    # Complete plan
    response = client.post(
        f"/api/v1/plans/{today}/complete",
        json={
            "task_completions": {"task1": True, "task2": False},
            "notes": "Good day",
            "mood": 5,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 2
    assert data["completed_tasks"] == 1


@pytest.mark.asyncio
async def test_get_plan_reflection(client, auth_headers):
    """Test getting plan reflection/stats."""
    today = datetime.utcnow().date().isoformat()

    # Create and complete plan
    client.post(
        f"/api/v1/plans/{today}",
        json={"task_order": ["task1"]},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/plans/{today}/complete",
        json={"task_completions": {"task1": True}},
        headers=auth_headers,
    )

    # Get reflection
    response = client.get(
        f"/api/v1/plans/{today}/reflection",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_tasks" in data
    assert "completion_rate" in data