"""Errors returned by the capability plugin bus."""

from __future__ import annotations


class BusError(RuntimeError):
    """Base error carrying the public E-series error code."""

    code = "E-500"

    def as_result(self) -> dict:
        return {
            "ok": False,
            "error": {"code": self.code, "message": str(self)},
            "degraded": True,
        }


class ManifestError(BusError):
    code = "E-400"


class LifecycleError(BusError):
    code = "E-409"


class RoutingError(BusError):
    code = "E-404"


class PermissionDenied(BusError):
    code = "E-403"


class CallTimeout(BusError):
    code = "E-504"


class PluginFailure(BusError):
    code = "E-500"
