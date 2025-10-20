"""Обработчики команд бота."""

from aiogram import Router

from .admin import router as admin_router
from .callbacks import router as callback_router
from .commands import router as command_router

# Главный роутер
main_router = Router()
main_router.include_routers(command_router, callback_router, admin_router)

__all__ = ["main_router"]

