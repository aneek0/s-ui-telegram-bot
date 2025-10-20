"""Обработчики команд."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import settings
from src.keyboards import get_main_menu

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором."""
    return user_id in settings.admin_list


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Это бот для управления S-UI панелью VPN.\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    help_text = """
🤖 <b>Помощь по боту S-UI</b>

<b>Доступные команды:</b>
/start - Запустить бота и показать главное меню
/help - Показать это сообщение

<b>Функции бота:</b>
• 📊 Статус сервера - загрузка CPU, RAM, диска, сети, uptime
• 👥 Клиенты - список с онлайн статусом (🟢🟡🔴)
  - Автоматическая генерация ссылки подписки
  - Список доступных подключений
  - Детальная статистика трафика
• 📥 Inbounds - входящие соединения
• 📤 Outbounds - исходящие соединения
• 🔐 TLS - сертификаты и конфигурация
• ⚙️ Настройки - конфигурация панели S-UI
• 📋 Конфиг - параметры системы
• 📜 Логи - просмотр логов сервера
• 🔄 Перезапуск - Core или приложение

<b>О панели S-UI:</b>
S-UI - это продвинутая панель управления для Sing-Box с поддержкой множества протоколов и расширенной маршрутизацией трафика.
"""
    await message.answer(help_text, parse_mode="HTML")

