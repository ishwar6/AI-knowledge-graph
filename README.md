# AI-Powered Code Intelligence Graph (POC #2)

Turn a Django (or Node / Go) backend into a living, queryable knowledge graph. This proof-of-concept scans your repo with AST parsing, pushes structure into Neo4j, and then returns AI-style insights about architecture hotspots, coupling, and anti-patterns.

If your repo feels like spaghetti, this is the map.

## Why this exists

Modern backend projects tend to drift into:

- **Tightly coupled models** that become impossible to change
- **Duplicate service logic** hidden across files
- **Views hitting the DB directly** without caching or batching
- **Implicit dependencies** buried in imports or service calls

This project is a fast, practical way to visualize and explain those issues.

## What it does

**Scan → Graph → Insights**

1. Parse Python files using the AST.
2. Create nodes and relationships in Neo4j.
3. Run AI-style heuristics to surface architectural signals.

You get answers like:

- Which model is most coupled?
- Which API endpoints execute raw SQL repeatedly?
- What looks unused or dead?
- Which modules are circularly dependent?

## Repository layout

```
neo4j-code-intel/
│─ scanner/
│   ├─ ast_parser.py
│   ├─ django_scanner.py
│   ├─ dependency_graph.py
│─ graph/
│   ├─ neo4j_service.py
│   ├─ cypher_templates.py
│─ ai/
│   ├─ analyzer.py
│   ├─ refactor_rules.yaml
│─ api/
│   ├─ app.py
│   ├─ endpoints.py
│─ examples/
│   ├─ sample_django_repo/
│─ README.md
│─ docker-compose.yml
```

## Quick start

### 1) Install dependencies

```bash
pip install fastapi uvicorn neo4j pydantic
```

### 2) Start Neo4j (optional but recommended)

```bash
docker-compose up -d
```

### 3) Run the API

```bash
uvicorn api.app:app --reload
```

### 4) Trigger a scan

```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "examples/sample_django_repo",
    "neo4j_uri": "bolt://localhost:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "password",
    "reset_graph": true
  }'
```

## Neo4j schema (expanded)

```
(:Module {name, path, loc, complexity})
(:Model {name, loc, fk_count, index_count, used_in_views:int})
(:View {name, method, path})
(:Service {name, file_path})
(:DBQuery {raw_sql, originates_from})

(:Module)-[:DEPENDS_ON]->(:Module)
(:Model)-[:FOREIGN_KEY_TO]->(:Model)
(:View)-[:CALLS]->(:Service)
(:Service)-[:EXECUTES_QUERY]->(:DBQuery)
(:View)-[:USES_MODEL]->(:Model)
```

## AI insights (sample)

```json
{
  "refactoring_priority": [
    {
      "entity": "BusinessUser Model",
      "reason": "High coupling (14 FK) + used by 9 APIs",
      "remediation": "Split into User, BusinessMeta, BillingProfile"
    }
  ],
  "dead_code": ["LegacyInvoiceModel"],
  "complexity_score": 0.82
}
```

## Example Cypher queries

```cypher
// Most coupled model
MATCH (m:Model)-[:FOREIGN_KEY_TO]->()
RETURN m.name AS model, COUNT(*) AS fk_edges
ORDER BY fk_edges DESC
LIMIT 5;

// Views with repeated SQL calls
MATCH (v:View)-[:CALLS]->(:Service)-[:EXECUTES_QUERY]->(q:DBQuery)
RETURN v.name AS view, COUNT(q) AS sql_calls
ORDER BY sql_calls DESC
LIMIT 5;
```

## What to build next

Ideas that pair nicely with this POC:

- Add coverage for **Node** or **Go** parsers
- Attach **query frequency** or **response time** metrics
- Add **DRF cache suggestions** per endpoint
- Export visualization-ready graph bundles

---

If you want this adapted for a real production repo, plug in your codebase, point Neo4j at it, and iterate from there.
