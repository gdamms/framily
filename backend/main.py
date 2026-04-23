from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from core.config import settings
from api import router

app = FastAPI(
    title=settings.TITLE,
    version=settings.VERSION,
)

# Configure CORS
origins = settings.CORS_ORIGINS
if origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def _is_within_directory(candidate: Path, directory: Path) -> bool:
    try:
        candidate.relative_to(directory)
    except ValueError:
        return False
    return True


if settings.SERVE_FRONTEND:
    frontend_dist_dir = Path(settings.FRONTEND_DIST_DIR).resolve()
    frontend_index_file = frontend_dist_dir / "index.html"

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_frontend_root():
        if frontend_index_file.exists():
            return FileResponse(frontend_index_file)
        raise HTTPException(status_code=503, detail="Frontend build is not available")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        requested_file = (frontend_dist_dir / full_path).resolve()
        if _is_within_directory(requested_file, frontend_dist_dir) and requested_file.is_file():
            return FileResponse(requested_file)

        if frontend_index_file.exists():
            return FileResponse(frontend_index_file)

        raise HTTPException(status_code=404, detail="Not found")
