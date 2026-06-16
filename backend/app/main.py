from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .runtime_env import sanitize_proxy_environment

sanitize_proxy_environment()

from .routes.debug import router as debug_router
from .routes.screening import router as screening_router
from .routes.v1_screening import router as screening_v1_router

app = FastAPI(
    title="Stock2to3Selection API",
    description="Multi-client second-board analysis backend powered by FastAPI and Akshare.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(screening_router)
app.include_router(screening_v1_router)
app.include_router(debug_router)

desktop_shell_dir = Path(__file__).resolve().parents[2] / "web" / "desktop-shell"
if desktop_shell_dir.exists():
    app.mount(
        "/desktop-shell",
        StaticFiles(directory=desktop_shell_dir, html=True),
        name="desktop-shell",
    )
