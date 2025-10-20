"""Клавиатуры для телеграм бота."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Статус", callback_data="status"),
            InlineKeyboardButton(text="👥 Клиенты", callback_data="clients"),
        ],
        [
            InlineKeyboardButton(text="📥 Inbounds", callback_data="inbounds"),
            InlineKeyboardButton(text="📤 Outbounds", callback_data="outbounds"),
        ],
        [
            InlineKeyboardButton(text="🔐 TLS", callback_data="tls"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        ],
        [
            InlineKeyboardButton(text="📝 Логи", callback_data="logs"),
        ],
        [
            InlineKeyboardButton(text="🔄 Перезапуск Core", callback_data="restart_core"),
            InlineKeyboardButton(text="🔄 Перезапуск App", callback_data="restart_app"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    keyboard = [[InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_restart(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения перезапуска."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="back_to_menu"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_logs_menu() -> InlineKeyboardMarkup:
    """Меню выбора логов."""
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Последние 50", callback_data="logs_50"),
            InlineKeyboardButton(text="📝 Последние 100", callback_data="logs_100"),
        ],
        [
            InlineKeyboardButton(text="📝 Последние 200", callback_data="logs_200"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_client_actions(client_id: int, client_name: str) -> InlineKeyboardMarkup:
    """Действия с клиентом."""
    keyboard = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"client_info:{client_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="clients")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_clients_keyboard(clients: list, online_users: list = None) -> InlineKeyboardMarkup:
    """Клавиатура со списком клиентов с индикацией онлайн статуса."""
    keyboard = []
    online_set = set(online_users) if online_users else set()
    
    for client in clients[:20]:  # Максимум 20 клиентов
        if isinstance(client, dict):
            client_id = client.get("id")
            name = client.get("name", "Unknown")
            enable = client.get("enable", False)
            
            # Определяем статус
            if name in online_set:
                status = "🟢"  # Онлайн и активен
            elif enable:
                status = "🟡"  # Активен но офлайн
            else:
                status = "🔴"  # Отключен
            
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status} {name}",
                    callback_data=f"client_info:{client_id}",
                )
            ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

