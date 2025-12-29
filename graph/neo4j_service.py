"""Neo4j integration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from neo4j import GraphDatabase


@dataclass
class Neo4jConfig:
    uri: str
    user: str
    password: str


class Neo4jService:
    def __init__(self, config: Neo4jConfig) -> None:
        self._driver = GraphDatabase.driver(config.uri, auth=(config.user, config.password))

    def close(self) -> None:
        self._driver.close()

    def run_statements(self, statements: Iterable[str]) -> None:
        with self._driver.session() as session:
            for statement in statements:
                session.run(statement)

    def clear(self) -> None:
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
