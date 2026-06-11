"""Service health checks (Phase 1 / ops)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class HealthProbe(Protocol):
    def ping(self) -> bool: ...


@dataclass(frozen=True)
class ServiceStatus:
    name: str
    healthy: bool
    detail: str = ""


@dataclass
class HealthReport:
    services: list[ServiceStatus] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(service.healthy for service in self.services)


def check_service(name: str, probe: HealthProbe) -> ServiceStatus:
    """Ping one dependency."""
    try:
        ok = probe.ping()
    except Exception as exc:  # noqa: BLE001 — health probe boundary
        return ServiceStatus(name=name, healthy=False, detail=str(exc))
    return ServiceStatus(name=name, healthy=ok, detail="ok" if ok else "probe failed")


def check_all(probes: dict[str, HealthProbe]) -> HealthReport:
    """Run all registered probes."""
    report = HealthReport()
    for name, probe in sorted(probes.items()):
        report.services.append(check_service(name, probe))
    return report


def check_http_status(response: dict[str, Any], *, expected: int = 200) -> bool:
    """Helper for API health endpoints."""
    status = response.get("status_code", response.get("status"))
    return int(status) == expected
