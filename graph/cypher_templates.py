"""Cypher statement builders for the knowledge graph."""

from __future__ import annotations

from typing import Iterable

from scanner.django_scanner import ScanResult


def build_statements(scan: ScanResult) -> list[str]:
    statements: list[str] = []

    for module in scan.modules:
        statements.append(
            "MERGE (m:Module {name: $name}) "
            "SET m.path = $path, m.loc = $loc, m.complexity = $complexity"
            .replace("$name", repr(module.name))
            .replace("$path", repr(module.path))
            .replace("$loc", str(module.loc))
            .replace("$complexity", str(module.complexity))
        )

    for model in scan.models:
        statements.append(
            "MERGE (m:Model {name: $name}) "
            "SET m.loc = $loc, m.fk_count = $fk, m.index_count = $index, m.used_in_views = $used"
            .replace("$name", repr(model.name))
            .replace("$loc", str(model.loc))
            .replace("$fk", str(model.fk_count))
            .replace("$index", str(model.index_count))
            .replace("$used", str(model.used_in_views))
        )

    for view in scan.views:
        statements.append(
            "MERGE (v:View {name: $name}) "
            "SET v.method = $method, v.path = $path"
            .replace("$name", repr(view.name))
            .replace("$method", repr(view.method))
            .replace("$path", repr(view.path))
        )

    for service in scan.services:
        statements.append(
            "MERGE (s:Service {name: $name}) SET s.file_path = $path"
            .replace("$name", repr(service.name))
            .replace("$path", repr(service.file_path))
        )

    for query in scan.raw_queries:
        statements.append(
            "MERGE (q:DBQuery {raw_sql: $raw}) SET q.originates_from = $origin"
            .replace("$raw", repr(query.raw_sql))
            .replace("$origin", repr(query.originates_from))
        )

    statements.extend(_module_edges(scan.module_dependencies))
    statements.extend(_view_model_edges(scan.view_model_usage))
    statements.extend(_view_service_edges(scan.view_service_calls))

    return statements


def _module_edges(edges: Iterable[tuple[str, str]]) -> list[str]:
    statements: list[str] = []
    for source, target in edges:
        statements.append(
            "MATCH (a:Module {name: $source}), (b:Module {name: $target}) "
            "MERGE (a)-[:DEPENDS_ON]->(b)"
            .replace("$source", repr(source))
            .replace("$target", repr(target))
        )
    return statements


def _view_model_edges(edges: Iterable[tuple[str, str]]) -> list[str]:
    statements: list[str] = []
    for view, model in edges:
        statements.append(
            "MATCH (v:View {name: $view}), (m:Model {name: $model}) "
            "MERGE (v)-[:USES_MODEL]->(m)"
            .replace("$view", repr(view))
            .replace("$model", repr(model))
        )
    return statements


def _view_service_edges(edges: Iterable[tuple[str, str]]) -> list[str]:
    statements: list[str] = []
    for view, service in edges:
        statements.append(
            "MATCH (v:View {name: $view}), (s:Service {name: $service}) "
            "MERGE (v)-[:CALLS]->(s)"
            .replace("$view", repr(view))
            .replace("$service", repr(service))
        )
    return statements
