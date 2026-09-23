"""Versioned safety resources with an unverified development fallback."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Callable


@dataclass(frozen=True)
class Resource:
    resource_id: str
    label: str
    contact_method: str | None
    locale: str


@dataclass(frozen=True)
class ResourceBundle:
    version: str
    last_verified: datetime | None
    resources: tuple[Resource, ...]
    integrity_hash: str


def bundle_hash(version: str, resources: tuple[Resource, ...]) -> str:
    payload = {"version": version, "resources": [r.__dict__ for r in resources]}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture_bundle() -> ResourceBundle:
    resources = (Resource("sg-unverified-fixture", "Development fixture: verified Singapore safety contacts pending", None, "en-SG"),)
    version = "fixture-unverified-v1"
    return ResourceBundle(version, None, resources, bundle_hash(version, resources))


@dataclass(frozen=True)
class ResolvedResources:
    bundle: ResourceBundle
    source: str
    stale: bool
    notice: str | None


class ResourceRegistry:
    def __init__(self, live_lookup: Callable[[], ResourceBundle] | None = None,
                 fallback: ResourceBundle | None = None,
                 stale_after: timedelta | None = None):
        self.live_lookup = live_lookup
        self.fallback = fallback or fixture_bundle()
        self.stale_after = stale_after  # Unspecified until resource governance review.

    @staticmethod
    def _valid(bundle: ResourceBundle) -> bool:
        return (isinstance(bundle, ResourceBundle) and bool(bundle.resources)
                and bundle.integrity_hash == bundle_hash(bundle.version, bundle.resources))

    def resolve(self, now: datetime, *, offline: bool = False) -> ResolvedResources:
        if not offline and self.live_lookup is not None:
            try:
                live = self.live_lookup()
                if self._valid(live):
                    stale = live.last_verified is None or (self.stale_after is not None and now - live.last_verified > self.stale_after)
                    return ResolvedResources(live, "live", stale, "Verification date unavailable or old" if stale else None)
            except Exception:
                pass
        if not self._valid(self.fallback):
            raise ValueError("Built-in safety resource integrity failed")
        stale = self.fallback.last_verified is None or (self.stale_after is not None and now - self.fallback.last_verified > self.stale_after)
        return ResolvedResources(self.fallback, "built_in", stale,
                                 "Fallback safety resources are unverified or may be stale" if stale else None)
