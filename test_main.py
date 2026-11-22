import os

# Set required environment variables before importing the FastAPI app
os.environ.setdefault("TRIGGER_AUTH_TOKEN", "test-trigger-token")
os.environ.setdefault("GITHUB_PAT", "test-github-pat")

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

AUTH_HEADERS = {"Authorization": "Bearer test-trigger-token"}
GITHUB_DISPATCH_URL = (
    "https://api.github.com/repos/octocat/hello-world"
    "/actions/workflows/deploy.yml/dispatches"
)


def test_missing_auth_header():
    response = client.post("/trigger/octocat/hello-world/deploy.yml")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid Authorization header"}


def test_invalid_auth_token():
    response = client.post(
        "/trigger/octocat/hello-world/deploy.yml",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid Authorization header"}


@respx.mock
def test_trigger_workflow_default_ref_no_inputs():
    github_route = respx.post(GITHUB_DISPATCH_URL).mock(
        return_value=httpx.Response(204)
    )

    response = client.post(
        "/trigger/octocat/hello-world/deploy.yml",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "repository": "octocat/hello-world",
        "workflow": "deploy.yml",
        "ref": "main",
        "inputs": {},
    }

    # Verify the outgoing request to GitHub
    assert github_route.called
    sent_request = github_route.calls.last.request
    assert sent_request.headers["Authorization"] == "Bearer test-github-pat"
    assert sent_request.read() == b'{"ref":"main"}'


@respx.mock
def test_trigger_workflow_custom_ref_and_query_inputs():
    github_route = respx.post(GITHUB_DISPATCH_URL).mock(
        return_value=httpx.Response(204)
    )

    response = client.post(
        "/trigger/octocat/hello-world/deploy.yml?ref=develop&environment=staging&dry_run=true",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "repository": "octocat/hello-world",
        "workflow": "deploy.yml",
        "ref": "develop",
        "inputs": {
            "environment": "staging",
            "dry_run": "true",
        },
    }

    # Verify 'ref' is at the top level and excluded from 'inputs'
    assert github_route.called
    sent_payload = github_route.calls.last.request.read().decode("utf-8")
    assert '"ref":"develop"' in sent_payload
    assert '"inputs":{"environment":"staging","dry_run":"true"}' in sent_payload


@respx.mock
def test_github_api_error_propagation():
    respx.post(GITHUB_DISPATCH_URL).mock(
        return_value=httpx.Response(
            422, text='{"message": "Workflow does not have workflow_dispatch trigger"}'
        )
    )

    response = client.post(
        "/trigger/octocat/hello-world/deploy.yml",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422
    assert "GitHub API Error:" in response.json()["detail"]
    assert (
        "Workflow does not have workflow_dispatch trigger" in response.json()["detail"]
    )
