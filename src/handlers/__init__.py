from aiogram import Router

from src.handlers.start import router as start_router
from src.handlers.search import router as search_router
from src.handlers.admin import router as admin_router
from src.handlers.tools import router as tools_router
from src.handlers.filters_menu import router as filters_menu_router
from src.handlers.marketplace import router as marketplace_router


def setup_routers() -> Router:
    router = Router()
    
    router.include_router(start_router)
    router.include_router(search_router)
    router.include_router(admin_router)
    router.include_router(tools_router)
    router.include_router(filters_menu_router)
    router.include_router(marketplace_router)
    
    return router
