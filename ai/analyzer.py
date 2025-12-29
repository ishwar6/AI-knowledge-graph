"""Generate AI-style insights from scan results."""

from __future__ import annotations

from dataclasses import asdict

from scanner.django_scanner import ScanResult


def analyze_scan(scan: ScanResult) -> dict[str, object]:
    model_coupling = sorted(
        scan.models,
        key=lambda model: model.fk_count,
        reverse=True,
    )
    most_coupled = model_coupling[0] if model_coupling else None

    view_queries = sorted(scan.views, key=lambda view: view.queries, reverse=True)
    noisy_views = view_queries[:5]

    used_models = {model for _, model in scan.view_model_usage}
    dead_models = [model.name for model in scan.models if model.name not in used_models]

    complexity_score = _complexity_score(scan)

    refactoring_priority = []
    if most_coupled:
        refactoring_priority.append(
            {
                "entity": f"{most_coupled.name} Model",
                "reason": f"High coupling ({most_coupled.fk_count} FK) + used by {most_coupled.used_in_views} APIs",
                "remediation": "Split into bounded contexts to reduce coupling",
            }
        )

    for view in noisy_views:
        if view.queries > 0:
            refactoring_priority.append(
                {
                    "entity": view.name,
                    "reason": f"{view.queries} raw SQL calls per request",
                    "fix": "Add select_related/prefetch_related and caching",
                }
            )

    return {
        "refactoring_priority": refactoring_priority,
        "dead_code": dead_models,
        "complexity_score": complexity_score,
        "summary": {
            "modules": len(scan.modules),
            "models": len(scan.models),
            "views": len(scan.views),
            "services": len(scan.services),
            "raw_queries": len(scan.raw_queries),
        },
        "raw": {
            "modules": [asdict(module) for module in scan.modules],
            "models": [asdict(model) for model in scan.models],
            "views": [asdict(view) for view in scan.views],
            "services": [asdict(service) for service in scan.services],
        },
    }


def _complexity_score(scan: ScanResult) -> float:
    if not scan.modules:
        return 0.0
    avg_complexity = sum(module.complexity for module in scan.modules) / len(scan.modules)
    raw_query_weight = len(scan.raw_queries) * 0.1
    return round(min(1.0, (avg_complexity / 10) + raw_query_weight), 2)
