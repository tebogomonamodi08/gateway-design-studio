from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import time


@dataclass
class ProviderState:
    name: str
    status: str = "Healthy"  # Healthy, Latency, Timeout, Failure
    requests: int = 0
    latency_ms: int = 100
    success_rate: float = 99.0
    last_check: float = field(default_factory=time.time)


class Topology:
    def __init__(self):
        self.nodes: Dict[str, ProviderState] = {}

    def add_provider(self, name: str):
        if name not in self.nodes:
            self.nodes[name] = ProviderState(name=name)

    def get_snapshot(self) -> List[ProviderState]:
        return list(self.nodes.values())

    def simulate(self, provider: str, mode: str):
        # mode: normal, latency, timeout, failure
        p = self.nodes.get(provider)
        if not p:
            return
        p.last_check = time.time()
        if mode == "normal":
            p.status = "Healthy"
            p.latency_ms = 120
            p.success_rate = 98.0
        elif mode == "latency":
            p.status = "Latency"
            p.latency_ms = 800
            p.success_rate = 95.0
        elif mode == "timeout":
            p.status = "Timeout"
            p.latency_ms = 3000
            p.success_rate = 60.0
        elif mode == "failure":
            p.status = "Failure"
            p.latency_ms = 0
            p.success_rate = 0.0

    def record_request(self, provider: str, latency_ms: int, success: bool):
        p = self.nodes.get(provider)
        if not p:
            return
        p.requests += 1
        p.latency_ms = int((p.latency_ms * (p.requests - 1) + latency_ms) / p.requests)
        p.success_rate = ((p.success_rate * (p.requests - 1)) + (100.0 if success else 0.0)) / p.requests


DEFAULT = Topology()

__all__ = ["Topology", "DEFAULT"]
