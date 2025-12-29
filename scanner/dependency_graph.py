"""Dependency graph utilities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    modules: set[str] = field(default_factory=set)
    edges: set[tuple[str, str]] = field(default_factory=set)

    def add_module(self, module: str) -> None:
        self.modules.add(module)

    def add_edge(self, source: str, target: str) -> None:
        self.edges.add((source, target))

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        return {
            "modules": [{"name": module} for module in sorted(self.modules)],
            "edges": [
                {"source": source, "target": target}
                for source, target in sorted(self.edges)
            ],
        }
