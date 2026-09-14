"""Registry of readiness probes.

Dependency probes register themselves here as they are implemented (database on
Day 2, Redis on Day 4). Keeping the registry in the core layer means those modules
can register without importing the API layer, which preserves the one-way
dependency rule.

Until a dependency registers a probe it is reported as ``not_configured`` rather
than ``ok`` — readiness must never claim a connection that does not exist yet.
"""

import logging
from collections.abc import Awaitable, Callable
from enum import StrEnum

logger = logging.getLogger(__name__)

#: Dependencies this service is expected to have once fully wired.
KNOWN_DEPENDENCIES: tuple[str, ...] = ("database", "redis")


class CheckStatus(StrEnum):
    """Outcome of a single readiness probe."""

    OK = "ok"
    FAILED = "failed"
    NOT_CONFIGURED = "not_configured"


ReadinessCheck = Callable[[], Awaitable[CheckStatus]]

_checks: dict[str, ReadinessCheck] = {}


def register_check(name: str, check: ReadinessCheck) -> None:
    """Register ``check`` as the readiness probe for the dependency ``name``."""
    _checks[name] = check


async def run_checks() -> dict[str, CheckStatus]:
    """Run every known dependency probe and collect the results.

    A probe that raises is reported as failed rather than propagating: readiness is
    a diagnostic endpoint, so it must describe a broken dependency instead of
    becoming a second failure. This is an outermost boundary, so the error is logged.
    """
    results: dict[str, CheckStatus] = {}
    for name in KNOWN_DEPENDENCIES:
        probe = _checks.get(name)
        if probe is None:
            results[name] = CheckStatus.NOT_CONFIGURED
            continue
        try:
            results[name] = await probe()
        except Exception:
            logger.exception("readiness probe failed: %s", name)
            results[name] = CheckStatus.FAILED
    return results
