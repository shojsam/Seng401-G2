import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app 

client = TestClient(app)

@patch("app.routes.results.get_recent_results")
def test_get_results_success(mock_get_results):
    mock_get_results.return_value = [
        {"id": 101, "winner": "reformers", "played_at": "2026-03-25 14:00:00"},
        {"id": 102, "winner": "exploiters", "played_at": "2026-03-25 15:30:00"}
    ]

    response = client.get("/results/") 

    assert response.status_code == 200
    data = response.json()
    
    assert "results" in data
    assert len(data["results"]) == 2
    assert data["results"][0]["winner"] == "reformers"
    assert isinstance(data["results"][0]["played_at"], str)

@patch("app.routes.results.get_recent_results")
def test_get_results_empty(mock_get_results):
    mock_get_results.return_value = []

    response = client.get("/results/")

    assert response.status_code == 200
    assert response.json() == {"results": []}