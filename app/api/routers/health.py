"""Liveness and readiness endpoints.

These answer two different questions and are kept separate from the start:

* ``GET /health`` — is this process alive? It touches no dependency, so a failing
  database can never cause the container to be killed and restarted pointlessly.
  This is what the container healthcheck polls.
* ``GET /health/ready`` — can this process serve traffic? It reports on the backing
  services, and is what an orchestrator would gate traffic on.
"""

from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.core.health import CheckStatus, run_checks

router = APIRouter(tags=["health"])


class LivenessResponse(BaseModel):
    """Confirms the process is running."""

    status: Literal["alive"] = "alive"


class ReadinessResponse(BaseModel):
    """Per-dependency readiness detail."""

    ready: bool
    checks: dict[str, CheckStatus]


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 whenever the process is running. Touches no dependency.",
    response_model=LivenessResponse,
)
async def liveness() -> LivenessResponse:
    """Report that the process is alive."""
    return LivenessResponse()


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description=(
        "Reports whether backing services are usable. Dependencies that are not wired "
        "up yet are reported as `not_configured`; a dependency that fails its probe "
        "makes this endpoint return 503."
    ),
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "A dependency is unavailable"}},
)
async def readiness(response: Response) -> ReadinessResponse:
    """Run every dependency probe and summarise the result."""
    checks = await run_checks()
    ready = all(result is not CheckStatus.FAILED for result in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(ready=ready, checks=checks)
