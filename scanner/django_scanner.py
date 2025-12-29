"""Scan Django-like repositories and extract entities for graph creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from scanner.ast_parser import ParsedClass, ParsedFile, parse_python_file


@dataclass
class ModuleInfo:
    name: str
    path: str
    loc: int
    complexity: int


@dataclass
class ModelInfo:
    name: str
    loc: int
    fk_count: int
    index_count: int
    used_in_views: int = 0


@dataclass
class ViewInfo:
    name: str
    method: str
    path: str
    queries: int


@dataclass
class ServiceInfo:
    name: str
    file_path: str


@dataclass
class RawQueryInfo:
    raw_sql: str
    originates_from: str


@dataclass
class ScanResult:
    modules: list[ModuleInfo] = field(default_factory=list)
    models: list[ModelInfo] = field(default_factory=list)
    views: list[ViewInfo] = field(default_factory=list)
    services: list[ServiceInfo] = field(default_factory=list)
    raw_queries: list[RawQueryInfo] = field(default_factory=list)
    module_dependencies: list[tuple[str, str]] = field(default_factory=list)
    view_model_usage: list[tuple[str, str]] = field(default_factory=list)
    view_service_calls: list[tuple[str, str]] = field(default_factory=list)


def _python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        yield path


def _module_name(root: Path, path: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def _loc(path: Path) -> int:
    return sum(1 for _ in path.read_text(encoding="utf-8").splitlines())


def _is_model_class(parsed: ParsedClass) -> bool:
    return any("models.Model" in base or base.endswith("Model") for base in parsed.bases)


def _is_view_class(parsed: ParsedClass) -> bool:
    view_markers = ("View", "APIView", "ViewSet")
    return any(base.endswith(view_markers) for base in parsed.bases)


def _is_service_file(path: Path) -> bool:
    return "services" in path.parts


def _count_fk_indicators(parsed: ParsedClass) -> int:
    return sum(
        1
        for method in parsed.methods
        for call in method.calls
        if "ForeignKey" in call or "ManyToMany" in call
    )


def _count_index_indicators(parsed: ParsedClass) -> int:
    return sum(
        1
        for method in parsed.methods
        for call in method.calls
        if "Index" in call
    )


def scan_repo(root: Path) -> ScanResult:
    result = ScanResult()
    parsed_files: list[ParsedFile] = []

    for path in _python_files(root):
        parsed_files.append(parse_python_file(path))

    for parsed in parsed_files:
        module_name = _module_name(root, parsed.path)
        result.modules.append(
            ModuleInfo(
                name=module_name,
                path=str(parsed.path),
                loc=_loc(parsed.path),
                complexity=len(parsed.functions) + len(parsed.classes),
            )
        )

        for cls in parsed.classes:
            if _is_model_class(cls):
                result.models.append(
                    ModelInfo(
                        name=cls.name,
                        loc=_loc(parsed.path),
                        fk_count=_count_fk_indicators(cls),
                        index_count=_count_index_indicators(cls),
                    )
                )
            if _is_view_class(cls):
                queries = sum(1 for call in _collect_calls(cls) if "execute" in call)
                result.views.append(
                    ViewInfo(
                        name=cls.name,
                        method="class",
                        path=str(parsed.path),
                        queries=queries,
                    )
                )

        for func in parsed.functions:
            if func.has_request_param and "view" in parsed.path.stem:
                result.views.append(
                    ViewInfo(
                        name=func.name,
                        method="function",
                        path=str(parsed.path),
                        queries=sum(1 for call in func.calls if "execute" in call),
                    )
                )

        if _is_service_file(parsed.path):
            for cls in parsed.classes:
                result.services.append(ServiceInfo(name=cls.name, file_path=str(parsed.path)))
            for func in parsed.functions:
                result.services.append(ServiceInfo(name=func.name, file_path=str(parsed.path)))

        for raw_call in parsed.raw_sql_calls:
            result.raw_queries.append(
                RawQueryInfo(
                    raw_sql=raw_call,
                    originates_from=str(parsed.path),
                )
            )

        for import_info in parsed.imports:
            if import_info.module:
                result.module_dependencies.append((module_name, import_info.module))

    _hydrate_relationships(result)
    return result


def _collect_calls(parsed: ParsedClass) -> list[str]:
    calls: list[str] = []
    for method in parsed.methods:
        calls.extend(method.calls)
    return calls


def _hydrate_relationships(result: ScanResult) -> None:
    model_lookup = {model.name.lower(): model for model in result.models}
    for view in result.views:
        for model_name, model in model_lookup.items():
            if model_name in view.name.lower():
                result.view_model_usage.append((view.name, model.name))
                model.used_in_views += 1

    service_lookup = {service.name.lower(): service for service in result.services}
    for view in result.views:
        for service_name, service in service_lookup.items():
            if service_name in view.name.lower():
                result.view_service_calls.append((view.name, service.name))
