"""API endpoints for scanning and analysis."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai.analyzer import analyze_scan
from graph.cypher_templates import build_statements
from graph.neo4j_service import Neo4jConfig, Neo4jService
from scanner.django_scanner import scan_repo

router = APIRouter()


class ScanRequest(BaseModel):
    repo_path: str
    neo4j_uri: str | None = None
    neo4j_user: str | None = None
    neo4j_password: str | None = None
    reset_graph: bool = True


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/scan")
async def scan(request: ScanRequest) -> dict[str, object]:
    repo_path = Path(request.repo_path)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository path not found")

    scan_result = scan_repo(repo_path)
    statements = build_statements(scan_result)

    if request.neo4j_uri and request.neo4j_user and request.neo4j_password:
        config = Neo4jConfig(
            uri=request.neo4j_uri,
            user=request.neo4j_user,
            password=request.neo4j_password,
        )
        service = Neo4jService(config)
        try:
            if request.reset_graph:
                service.clear()
            service.run_statements(statements)
        finally:
            service.close()

    insights = analyze_scan(scan_result)
    return {
        "insights": insights,
        "statement_count": len(statements),
    }
