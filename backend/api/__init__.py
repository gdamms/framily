from fastapi import APIRouter

from api.v1 import health, auth, framily, frame, pictures, user


router = APIRouter(prefix="/api/v1")


router.include_router(health.router)
router.include_router(auth.router)
router.include_router(framily.router)
router.include_router(frame.router)
router.include_router(pictures.router)
router.include_router(user.router)
