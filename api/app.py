"""FastAPI application entrypoint."""

from __future__ import annotations
from fastapi import FastAPI
from api.endpoints import router

app = FastAPI(title="AI Code Intelligence Graph")
app.include_router(router)
