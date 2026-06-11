"""Unit tests for health checker."""

from __future__ import annotations

from health.checker import HealthReport, check_all, check_http_status, check_service


class OkProbe:
    def ping(self) -> bool:
        return True


class FailProbe:
    def ping(self) -> bool:
        return False


class BoomProbe:
    def ping(self) -> bool:
        raise RuntimeError("connection refused")


def test_check_service_ok_and_fail() -> None:
    assert check_service("api", OkProbe()).healthy is True
    assert check_service("neo4j", FailProbe()).healthy is False


def test_check_service_catches_exceptions() -> None:
    status = check_service("db", BoomProbe())
    assert status.healthy is False
    assert "connection refused" in status.detail


def test_check_all_report() -> None:
    report = check_all({"api": OkProbe(), "neo4j": FailProbe()})
    assert isinstance(report, HealthReport)
    assert report.healthy is False
    assert len(report.services) == 2


def test_check_http_status() -> None:
    assert check_http_status({"status_code": 200}) is True
    assert check_http_status({"status": 503}) is False
