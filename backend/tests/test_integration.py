"""Integration tests for Meridian."""
import os
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    """Test the complete user registration and login flow."""
    # Register
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@test.com",
            "password": "password123",
            "display_name": "Integration Test",
        },
    )
    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "integration@test.com",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_full_workflow(client, auth_headers):
    """Test the complete workflow: create tasks, plan day, complete tasks."""
    # Create several tasks
    task_ids = []
    for i in range(3):
        task_response = client.post(
            "/api/v1/tasks",
            json={
                "title": f"Integration Task {i+1}",
                "description": f"Task {i+1} description",
                "priority": i + 1,
                "category": "work",
            },
            headers=auth_headers,
        )
        assert task_response.status_code == 200
        task_ids.append(task_response.json()["id"])

    # Create a daily plan
    today = "2026-02-19"  # Use a fixed date for testing
    plan_response = client.post(
        f"/api/v1/plans/{today}",
        json={
            "task_order": task_ids,
            "notes": "Testing full workflow",
            "mood": 4,
        },
        headers=auth_headers,
    )
    assert plan_response.status_code == 200
    plan_id = plan_response.json()["id"]

    # Complete the plan
    complete_response = client.post(
        f"/api/v1/plans/{today}/complete",
        json={
            "task_completions": {
                task_ids[0]: True,
                task_ids[1]: True,
                task_ids[2]: False,
            },
            "notes": "Completed 2 of 3 tasks",
            "mood": 3,
        },
        headers=auth_headers,
    )
    assert complete_response.status_code == 200