"""Tests for intelligence layer."""
import pytest


@pytest.mark.asyncio
async def test_parse_task_success(mock_llm, client, auth_headers):
    """Test parsing natural language task."""
    mock_llm.responses = [
        '{"title": "Buy groceries", "priority": 3, "estimated_minutes": 30}'
    ]

    response = client.post(
        "/api/v1/intelligence/tasks/parse",
        json={
            "text": "Buy groceries tomorrow high priority 30 min",
            "timezone": "UTC",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["priority"] == 3


@pytest.mark.asyncio
async def test_parse_task_fallback(mock_llm, client, auth_headers):
    """Test parsing fallback when LLM fails."""
    mock_llm.responses = ["invalid json"]

    response = client.post(
        "/api/v1/intelligence/tasks/parse",
        json={
            "text": "Simple task",
            "timezone": "UTC",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    # Fallback should use text as title
    assert data["title"] == "Simple task"


@pytest.mark.asyncio
async def test_get_suggestions(mock_llm, client, auth_headers):
    """Test getting task ordering suggestions."""
    mock_llm.responses = [
        '{"task_order": ["id1", "id2"], "reasoning": [], "warnings": []}'
    ]

    response = client.post(
        "/api/v1/intelligence/suggestions",
        json={
            "task_ids": ["id1", "id2"],
            "user_timezone": "UTC",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_order" in data
    assert "reasoning" in data
    assert "warnings" in data


@pytest.mark.asyncio
async def test_get_insights(mock_llm, client, auth_headers):
    """Test getting weekly insights."""
    response = client.get(
        "/api/v1/intelligence/insights?days=7",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_tasks_completed" in data
    assert "average_completion_rate" in data