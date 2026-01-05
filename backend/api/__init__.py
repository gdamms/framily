from fastapi import APIRouter

from api.v1 import health, auth


router = APIRouter(prefix="/api/v1")


router.include_router(health.router)
router.include_router(auth.router)
