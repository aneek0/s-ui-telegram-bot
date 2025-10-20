"""Главный модуль телеграм бота."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from src.config import settings
from src.handlers import main_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота."""
    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher()
    dp.include_router(main_router)
    
    # Устанавливаем команды бота для меню
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="stats", description="Детальная статистика сервера"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Команды бота установлены в меню")
    
    logger.info("Бот запущен!")
    
    try:
        # Запуск polling
        await dp.start_polling(bot)
    finally:
        # Закрываем сессию бота
        await bot.session.close()
        
        # Закрываем сессию SUiClient
        from src.handlers.callbacks import sui_client
        await sui_client.close()
        
        logger.info("Бот остановлен, все сессии закрыты")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

