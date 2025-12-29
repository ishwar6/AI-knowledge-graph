# AI-Powered Code Intelligence Graph (POC #2)

This repository contains a proof-of-concept pipeline that scans a Django (or similar Python) backend repo, builds a knowledge graph schema in Neo4j, and returns AI-driven insights.

## Features

- AST-based parsing of Python code to extract modules, models, views, services, and raw SQL usage.
- Graph ingestion into Neo4j with an expanded schema.
- AI-style insights including refactoring priorities, dead code candidates, and a complexity score.
- FastAPI endpoint to drive scans.

## Folder Structure

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

## Running the API

1. Install dependencies (FastAPI, Neo4j driver):

```bash
pip install fastapi uvicorn neo4j pydantic
```

2. Start the API:

```bash
uvicorn api.app:app --reload
```

3. Trigger a scan:

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

## Neo4j Schema

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

## Example Output

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
