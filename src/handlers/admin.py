"""Обработчики для административных функций."""

import logging

from aiogram import F, Router
from aiogram.types import Message

from src.config import settings

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором."""
    return user_id in settings.admin_list


@router.message(F.text)
async def handle_unknown_text(message: Message):
    """Обработка неизвестных текстовых сообщений."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    
    await message.answer(
        "❓ Неизвестная команда. Используйте /help для просмотра доступных команд."
    )

