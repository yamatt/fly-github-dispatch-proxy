import os

import httpx
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from logger import log

app = FastAPI(title="GitHub Dispatch Proxy")

TRIGGER_AUTH_TOKEN = os.environ["TRIGGER_AUTH_TOKEN"]
GITHUB_PAT = os.environ["GITHUB_PAT"]


class DispatchResponse(BaseModel):
    status: str = Field(default="success", description="Execution status")
    repository: str = Field(
        ..., example="octocat/hello-world", description="Target repository path"
    )
    workflow: str = Field(
        ..., example="daily-build.yml", description="Triggered workflow file"
    )
    ref: str = Field(..., example="main", description="Git branch or reference target")


@app.post(
    "/trigger/{owner}/{repo}/{workflow_file}", status_code=status.HTTP_201_CREATED
)
async def trigger_workflow(
    owner: str,
    repo: str,
    workflow_file: str,
    ref: str = "main",
    authorization: str = Header(None),
):
    if not authorization or authorization != f"Bearer {TRIGGER_AUTH_TOKEN}":
        log.error(
            "Invalid Authorization header",
            owner=owner,
            repo=repo,
            workflow_file=workflow_file,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
        )

    github_url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/actions/workflows/{workflow_file}/dispatches"
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fly.io:github-dispatch-proxy",
    }

    async with httpx.AsyncClient() as client:
        gh_response = await client.post(github_url, headers=headers, json={"ref": ref})
        log.info(
            "GitHub API response",
            status_code=gh_response.status_code,
            response_text=gh_response.text,
        )

    if gh_response.status_code == 204:
        return {
            "status": "success",
            "repository": f"{owner}/{repo}",
            "workflow": workflow_file,
            "ref": ref,
        }

    raise HTTPException(
        status_code=gh_response.status_code,
        detail=f"GitHub API Error: {gh_response.text}",
    )
