"""AST parsing utilities for Python source files."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class ParsedImport:
    module: str
    name: str | None


@dataclass
class ParsedFunction:
    name: str
    lineno: int
    calls: list[str] = field(default_factory=list)
    has_request_param: bool = False


@dataclass
class ParsedClass:
    name: str
    lineno: int
    bases: list[str] = field(default_factory=list)
    methods: list[ParsedFunction] = field(default_factory=list)


@dataclass
class ParsedFile:
    path: Path
    imports: list[ParsedImport] = field(default_factory=list)
    functions: list[ParsedFunction] = field(default_factory=list)
    classes: list[ParsedClass] = field(default_factory=list)
    raw_sql_calls: list[str] = field(default_factory=list)


class _CallCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.raw_sql_calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _resolve_call_name(node.func)
        if name:
            self.calls.append(name)
            if name.endswith("cursor.execute") or name.endswith("execute"):
                self.raw_sql_calls.append(name)
        self.generic_visit(node)


def _resolve_call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value = _resolve_call_name(node.value)
        if value:
            return f"{value}.{node.attr}"
        return node.attr
    return None


def _resolve_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_resolve_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return "<unknown>"


def _collect_imports(tree: ast.AST) -> list[ParsedImport]:
    imports: list[ParsedImport] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ParsedImport(module=alias.name, name=None))
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(ParsedImport(module=module, name=alias.name))
    return imports


def _collect_functions(nodes: Iterable[ast.AST]) -> list[ParsedFunction]:
    functions: list[ParsedFunction] = []
    for node in nodes:
        if isinstance(node, ast.FunctionDef):
            collector = _CallCollector()
            collector.visit(node)
            arg_names = {arg.arg for arg in node.args.args}
            has_request_param = "request" in arg_names
            functions.append(
                ParsedFunction(
                    name=node.name,
                    lineno=node.lineno,
                    calls=collector.calls,
                    has_request_param=has_request_param,
                )
            )
    return functions


def _collect_classes(nodes: Iterable[ast.AST]) -> list[ParsedClass]:
    classes: list[ParsedClass] = []
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            bases = [_resolve_name(base) for base in node.bases]
            methods = _collect_functions(node.body)
            classes.append(
                ParsedClass(
                    name=node.name,
                    lineno=node.lineno,
                    bases=bases,
                    methods=methods,
                )
            )
    return classes


def parse_python_file(path: Path) -> ParsedFile:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = _collect_imports(tree)
    functions = _collect_functions(tree.body)
    classes = _collect_classes(tree.body)

    raw_sql_calls: list[str] = []
    for func in functions:
        raw_sql_calls.extend(func.calls)
    for cls in classes:
        for method in cls.methods:
            raw_sql_calls.extend(method.calls)

    return ParsedFile(
        path=path,
        imports=imports,
        functions=functions,
        classes=classes,
        raw_sql_calls=[call for call in raw_sql_calls if "execute" in call],
    )
