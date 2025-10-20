"""Обработчики callback запросов."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.keyboards import (
    get_back_button,
    get_confirm_restart,
    get_logs_menu,
    get_main_menu,
)
from src.sui_api import SUiAPIError, SUiClient
from src.config import settings

logger = logging.getLogger(__name__)
router = Router()

# Создаём глобальный клиент
sui_client = SUiClient(settings.sui_url, settings.sui_token)


def format_bytes(bytes_value: int) -> str:
    """Форматирование байтов в читаемый вид."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню."""
    await callback.message.edit_text(
        "📋 Главное меню:",
        reply_markup=get_main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "status")
async def callback_status(callback: CallbackQuery):
    """Показать статус сервера."""
    await callback.answer()
    
    try:
        # Запрашиваем статус с правильными параметрами согласно документации API
        response = await sui_client.get_status(resource="cpu,ram,disk,uptime,loads,netIO,tcpCount,udpCount")
        obj = response.get("obj", {})
        
        # Логируем для отладки
        logger.info(f"Получен статус с метриками: {list(obj.keys())}")
        
        # Форматируем статус
        status_text = "📊 <b>Статус сервера:</b>\n\n"
        
        # CPU
        if "cpu" in obj:
            cpu = obj["cpu"]
            if isinstance(cpu, (int, float)):
                status_text += f"🖥 <b>CPU:</b> {cpu:.1f}%\n"
        
        # Память (согласно документации API это "ram")
        if "ram" in obj:
            ram = obj["ram"]
            if isinstance(ram, dict):
                total = ram.get("total", 0)
                used = ram.get("used", 0)
                if total > 0:
                    percent = (used / total * 100)
                    status_text += f"💾 <b>RAM:</b> {format_bytes(used)} / {format_bytes(total)} ({percent:.1f}%)\n"
        elif "mem" in obj:
            mem = obj["mem"]
            if isinstance(mem, dict):
                total = mem.get("total", 0)
                used = mem.get("used", 0)
                if total > 0:
                    percent = (used / total * 100)
                    status_text += f"💾 <b>RAM:</b> {format_bytes(used)} / {format_bytes(total)} ({percent:.1f}%)\n"
        
        # Диск
        if "disk" in obj:
            disk = obj["disk"]
            if isinstance(disk, dict):
                total = disk.get("total", 0)
                used = disk.get("used", 0)
                if total > 0:
                    percent = (used / total * 100)
                    status_text += f"💿 <b>Диск:</b> {format_bytes(used)} / {format_bytes(total)} ({percent:.1f}%)\n"
        
        # Uptime
        if "uptime" in obj:
            uptime = obj["uptime"]
            if isinstance(uptime, (int, float)):
                days = int(uptime // 86400)
                hours = int((uptime % 86400) // 3600)
                minutes = int((uptime % 3600) // 60)
                status_text += f"\n⏱ <b>Uptime:</b> {days}д {hours}ч {minutes}м\n"
        
        # Загрузка (loads)
        if "loads" in obj:
            loads = obj["loads"]
            if isinstance(loads, list) and len(loads) >= 3:
                status_text += f"📈 <b>Load Average:</b> {loads[0]:.2f}, {loads[1]:.2f}, {loads[2]:.2f}\n"
        
        # TCP/UDP соединения
        if "tcpCount" in obj:
            status_text += f"\n🔹 <b>TCP соединений:</b> {obj['tcpCount']}\n"
        if "udpCount" in obj:
            status_text += f"🔸 <b>UDP соединений:</b> {obj['udpCount']}\n"
        
        # NetIO
        if "netIO" in obj:
            netio = obj["netIO"]
            if isinstance(netio, dict):
                up = netio.get("up", 0)
                down = netio.get("down", 0)
                status_text += f"\n🚦 <b>Трафик:</b>\n"
                status_text += f"   ⬆️ Отправлено: {format_bytes(up)}\n"
                status_text += f"   ⬇️ Получено: {format_bytes(down)}\n"
        
        # Онлайн клиенты
        try:
            online_response = await sui_client.get_onlines()
            online_data = online_response.get("obj", {})
            online_users = online_data.get("user", []) if isinstance(online_data, dict) else []
            if online_users:
                status_text += f"\n🌐 <b>Клиентов онлайн:</b> {len(online_users)}\n"
        except:
            pass
        
        await callback.message.edit_text(
            status_text,
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении статуса: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении статуса:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "clients")
async def callback_clients(callback: CallbackQuery):
    """Показать список клиентов с кнопками и онлайн статусом."""
    await callback.answer()
    
    try:
        response = await sui_client.get_clients()
        clients_data = response.get("obj", {})
        
        # API возвращает словарь с ключом 'clients'
        if isinstance(clients_data, dict):
            clients = clients_data.get("clients", [])
        elif isinstance(clients_data, list):
            clients = clients_data
        else:
            logger.error(f"Неожиданный тип данных клиентов: {type(clients_data)}")
            clients = []
        
        if not clients:
            await callback.message.edit_text(
                "👥 <b>Клиенты:</b>\n\nКлиенты не найдены.",
                parse_mode="HTML",
                reply_markup=get_back_button(),
            )
            return
        
        # Получаем онлайн пользователей
        try:
            online_response = await sui_client.get_onlines()
            online_data = online_response.get("obj", {})
            online_users = online_data.get("user", []) if isinstance(online_data, dict) else []
        except:
            online_users = []
        
        from src.keyboards import get_clients_keyboard
        
        # Подсчитываем общий трафик всех клиентов
        total_up = 0
        total_down = 0
        for client in clients:
            if isinstance(client, dict):
                up = client.get("up", 0)
                down = client.get("down", 0)
                if isinstance(up, (int, float)):
                    total_up += up
                if isinstance(down, (int, float)):
                    total_down += down
        
        def format_traffic(bytes_val):
            if bytes_val < 1024**3:  # Меньше 1GB
                return f"{bytes_val / (1024**2):.2f}MB"
            else:
                return f"{bytes_val / (1024**3):.2f}GB"
        
        text = f"👥 <b>Клиенты ({len(clients)}):</b>\n\n"
        text += f"📊 <b>Общий трафик:</b>\n"
        text += f"⬆️ Отправлено: {format_traffic(total_up)}\n"
        text += f"⬇️ Получено: {format_traffic(total_down)}\n"
        text += f"📈 Всего: {format_traffic(total_up + total_down)}\n\n"
        text += "Выберите клиента для просмотра деталей:"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_clients_keyboard(clients, online_users),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении клиентов: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении списка клиентов:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data.startswith("client_info:"))
async def callback_client_info(callback: CallbackQuery):
    """Показать полную информацию о клиенте включая ссылки."""
    await callback.answer()
    
    client_id = int(callback.data.split(":")[1])
    
    try:
        # Получаем данные клиента
        response = await sui_client.get_clients()
        clients_data = response.get("obj", {})
        
        if isinstance(clients_data, dict):
            clients = clients_data.get("clients", [])
        else:
            clients = []
        
        # Найти клиента по ID
        client = None
        for c in clients:
            if c.get("id") == client_id:
                client = c
                break
        
        if not client:
            await callback.message.edit_text(
                "❌ Клиент не найден",
                reply_markup=get_back_button(),
            )
            return
        
        name = client.get("name", "Без имени")
        enable = client.get("enable", False)
        volume = client.get("volume", 0)
        used_up = client.get("up", 0)
        used_down = client.get("down", 0)
        expiry = client.get("expiry", 0)
        desc = client.get("desc", "")
        group = client.get("group", "")
        inbound_ids = client.get("inbounds", [])
        
        # Проверяем онлайн статус
        try:
            online_response = await sui_client.get_onlines()
            online_data = online_response.get("obj", {})
            online_users = online_data.get("user", []) if isinstance(online_data, dict) else []
            is_online = name in online_users
        except:
            is_online = False
        
        # Формируем статус
        if is_online:
            status_icon = "🟢"
            status_text = "Онлайн"
        elif enable:
            status_icon = "🟡"
            status_text = "Офлайн"
        else:
            status_icon = "🔴"
            status_text = "Отключен"
        
        text = f"{status_icon} <b>{name}</b>\n\n"
        text += f"📊 <b>Статус:</b> {status_text}\n"
        
        # Статистика трафика
        used_total = used_up + used_down
        
        if volume > 0:
            percent = (used_total / volume * 100)
            remaining = volume - used_total
            text += f"\n💾 <b>Трафик:</b>\n"
            text += f"   Лимит: {format_bytes(volume)}\n"
            text += f"   Использовано: {format_bytes(used_total)} ({percent:.1f}%)\n"
            text += f"   Осталось: {format_bytes(remaining)}\n"
        else:
            text += f"\n💾 <b>Трафик:</b> {format_bytes(used_total)} (безлимит)\n"
        
        text += f"   ⬇️ Загрузка: {format_bytes(used_down)}\n"
        text += f"   ⬆️ Отдача: {format_bytes(used_up)}\n"
        
        # Получаем настройки для подписки
        try:
            settings_response = await sui_client.get_settings()
            settings_obj = settings_response.get("obj", {})
            
            # Получаем путь подписки (по умолчанию /sub согласно документации)
            sub_uri = settings_obj.get("subURI", settings_obj.get("subPath", "/sub"))
            sub_domain = settings_obj.get("subDomain", "")
            # Получаем порт подписки (может быть отдельным или тем же что и панель)
            sub_port = settings_obj.get("subPort", settings_obj.get("webPort", None))
            
            # Логируем для отладки
            logger.info(f"Настройки подписки: sub_uri={sub_uri}, sub_domain={sub_domain}, sub_port={sub_port}")
            
            # Если sub_uri пустой, используем стандартный путь /sub
            if not sub_uri or sub_uri.strip() == "":
                sub_uri = "/sub"
            
            # Убеждаемся что sub_uri начинается с /
            if sub_uri and not sub_uri.startswith("/"):
                sub_uri = "/" + sub_uri
            
            from src.config import settings
            from urllib.parse import urlparse
            parsed = urlparse(settings.sui_url)
            
            if sub_domain:
                # Если указан отдельный домен для подписки
                if sub_port and sub_port not in [80, 443]:
                    sub_url = f"https://{sub_domain}:{sub_port}{sub_uri}/{name}"
                else:
                    sub_url = f"https://{sub_domain}{sub_uri}/{name}"
            else:
                # Используем URL из конфига бота
                scheme = parsed.scheme
                hostname = parsed.hostname
                # Используем порт подписки если указан, иначе порт из URL
                if sub_port:
                    port = sub_port
                else:
                    port = parsed.port
                
                if port and port not in [80, 443]:
                    sub_url = f"{scheme}://{hostname}:{port}{sub_uri}/{name}"
                else:
                    sub_url = f"{scheme}://{hostname}{sub_uri}/{name}"
            
            logger.info(f"Сформирована ссылка подписки: {sub_url}")
            text += f"\n🔗 <b>Подписка:</b>\n<code>{sub_url}</code>\n"
        except Exception as e:
            logger.error(f"Ошибка генерации ссылки подписки: {e}")
            pass
        
        # Получаем inbounds для ссылок
        if inbound_ids:
            try:
                load_response = await sui_client.load_full_data()
                load_data = load_response.get("obj", {})
                inbounds = load_data.get("inbounds", [])
                
                text += f"\n📱 <b>Доступные подключения:</b>\n"
                for inbound_id in inbound_ids:
                    for inbound in inbounds:
                        if inbound.get("id") == inbound_id:
                            tag = inbound.get("tag", "")
                            protocol = inbound.get("type", "")
                            port = inbound.get("listen_port", 0)
                            text += f"   • {tag} ({protocol}) - порт {port}\n"
            except:
                pass
        
        if expiry > 0:
            from datetime import datetime
            expiry_date = datetime.fromtimestamp(expiry / 1000)
            text += f"\n📅 <b>Истекает:</b> {expiry_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        if group:
            text += f"👥 <b>Группа:</b> {group}\n"
        
        if desc:
            text += f"\n📝 <b>Описание:</b> {desc}\n"
        
        from src.keyboards import get_client_actions
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_client_actions(client_id, name),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении информации о клиенте: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "inbounds")
async def callback_inbounds(callback: CallbackQuery):
    """Показать список inbound соединений."""
    await callback.answer()
    
    try:
        response = await sui_client.get_inbounds()
        inbounds_data = response.get("obj", {})
        
        # API возвращает словарь с ключом 'inbounds'
        if isinstance(inbounds_data, dict):
            inbounds = inbounds_data.get("inbounds", [])
        elif isinstance(inbounds_data, list):
            inbounds = inbounds_data
        else:
            logger.error(f"Неожиданный тип данных inbounds: {type(inbounds_data)}")
            inbounds = []
        
        if not inbounds:
            await callback.message.edit_text(
                "📥 <b>Inbounds:</b>\n\nInbound соединения не найдены.",
                parse_mode="HTML",
                reply_markup=get_back_button(),
            )
            return
        
        text = "📥 <b>Список Inbound соединений:</b>\n\n"
        
        for idx, inbound in enumerate(inbounds, 1):
            # Проверяем что inbound - это словарь
            if not isinstance(inbound, dict):
                logger.warning(f"Inbound {idx} не является словарем: {inbound}")
                continue
                
            tag = inbound.get("tag", "N/A")
            protocol = inbound.get("type", inbound.get("protocol", "N/A"))
            listen = inbound.get("listen", "::")
            port = inbound.get("listen_port", inbound.get("port", "N/A"))
            # enable может отсутствовать, считаем что включен по умолчанию
            enable = inbound.get("enable", True)
            
            status = "✅" if enable else "❌"
            
            text += f"{idx}. {status} <b>{tag}</b>\n"
            text += f"   🔌 Протокол: {protocol}\n"
            text += f"   🌐 Адрес: {listen}:{port}\n\n"
        
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (список слишком длинный)"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении inbounds: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении inbounds:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "outbounds")
async def callback_outbounds(callback: CallbackQuery):
    """Показать список outbound соединений."""
    await callback.answer()
    
    try:
        response = await sui_client.get_outbounds()
        outbounds_data = response.get("obj", {})
        
        # API возвращает словарь с ключом 'outbounds'
        if isinstance(outbounds_data, dict):
            outbounds = outbounds_data.get("outbounds", [])
        elif isinstance(outbounds_data, list):
            outbounds = outbounds_data
        else:
            outbounds = []
        
        if not outbounds:
            await callback.message.edit_text(
                "📤 <b>Outbounds:</b>\n\nOutbound соединения не найдены.",
                parse_mode="HTML",
                reply_markup=get_back_button(),
            )
            return
        
        text = "📤 <b>Список Outbound соединений:</b>\n\n"
        
        for idx, outbound in enumerate(outbounds, 1):
            if not isinstance(outbound, dict):
                continue
                
            tag = outbound.get("tag", "N/A")
            out_type = outbound.get("type", "N/A")
            
            text += f"{idx}. <b>{tag}</b>\n"
            text += f"   🔌 Тип: {out_type}\n\n"
        
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (список слишком длинный)"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении outbounds: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении outbounds:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "tls")
async def callback_tls(callback: CallbackQuery):
    """Показать TLS сертификаты."""
    await callback.answer()
    
    try:
        load_response = await sui_client.load_full_data()
        load_data = load_response.get("obj", {})
        
        # Логируем для отладки
        logger.info(f"TLS data keys: {load_data.keys() if isinstance(load_data, dict) else 'not dict'}")
        
        # API возвращает словарь с ключом 'tls' или 'tlsConfigs'
        if isinstance(load_data, dict):
            tls_certs = load_data.get("tls", load_data.get("tlsConfigs", []))
        else:
            tls_certs = []
        
        if not tls_certs:
            await callback.message.edit_text(
                "🔐 <b>TLS сертификаты:</b>\n\nСертификаты не найдены.",
                parse_mode="HTML",
                reply_markup=get_back_button(),
            )
            return
        
        text = "🔐 <b>TLS сертификаты:</b>\n\n"
        
        for idx, cert in enumerate(tls_certs, 1):
            if not isinstance(cert, dict):
                logger.warning(f"TLS cert {idx} не является словарем: {cert}")
                continue
            
            # Логируем для отладки
            logger.info(f"TLS cert {idx} поля: {cert.keys()}")
            
            # Пробуем разные варианты полей
            server_name = cert.get("server_name", cert.get("serverName", cert.get("sni", "")))
            cert_file = cert.get("certificate", cert.get("cert", cert.get("cert_file", cert.get("certificateFile", ""))))
            key_file = cert.get("key", cert.get("key_file", cert.get("keyFile", "")))
            
            # Получаем ID и используем его для имени если нет server_name
            cert_id = cert.get("id", idx)
            if not server_name:
                # Пытаемся найти любое полезное имя
                for key in ["name", "tag", "domain"]:
                    if key in cert and cert[key]:
                        server_name = cert[key]
                        break
            
            if not server_name:
                server_name = f"TLS #{cert_id}"
            
            text += f"{idx}. <b>{server_name}</b>\n"
            if cert_file:
                # Показываем только имя файла, не полный путь
                cert_name = cert_file.split("/")[-1] if "/" in cert_file else cert_file
                text += f"   📄 Сертификат: {cert_name}\n"
            if key_file:
                key_name = key_file.split("/")[-1] if "/" in key_file else key_file
                text += f"   🔑 Ключ: {key_name}\n"
            
            # Дополнительная информация
            if "alpn" in cert:
                alpn = cert["alpn"]
                if isinstance(alpn, list):
                    text += f"   🔧 ALPN: {', '.join(alpn)}\n"
                else:
                    text += f"   🔧 ALPN: {alpn}\n"
            
            text += "\n"
        
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (список слишком длинный)"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении TLS: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении TLS:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "config")
async def callback_config(callback: CallbackQuery):
    """Показать конфигурацию."""
    await callback.answer()
    
    try:
        response = await sui_client.get_config()
        config_data = response.get("obj", {})
        
        text = "📋 <b>Конфигурация системы:</b>\n\n"
        
        if isinstance(config_data, dict):
            # Показываем основные параметры конфигурации
            for key, value in list(config_data.items())[:15]:  # Первые 15 параметров
                if isinstance(value, (str, int, bool, float)):
                    text += f"• <code>{key}</code>: {value}\n"
        
        if len(text) < 50:
            text += "Конфигурация пуста или недоступна."
        
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (конфигурация обрезана)"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении config: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении конфигурации:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    """Показать настройки панели."""
    await callback.answer()
    
    try:
        response = await sui_client.get_settings()
        settings_obj = response.get("obj", {})
        
        text = "⚙️ <b>Настройки панели:</b>\n\n"
        
        # Основные настройки веб-интерфейса
        if "webPort" in settings_obj:
            text += f"🌐 Web порт: <code>{settings_obj['webPort']}</code>\n"
        
        if "webDomain" in settings_obj:
            text += f"🌍 Домен: <code>{settings_obj['webDomain']}</code>\n"
        
        if "webBasePath" in settings_obj:
            text += f"📂 Базовый путь: <code>{settings_obj['webBasePath']}</code>\n"
        
        if "webListen" in settings_obj and settings_obj['webListen']:
            text += f"🔊 Web Listen: <code>{settings_obj['webListen']}</code>\n"
        
        # SSL сертификаты
        if "webCertFile" in settings_obj or "webKeyFile" in settings_obj:
            text += f"\n🔐 <b>SSL сертификаты:</b>\n"
            if "webCertFile" in settings_obj:
                text += f"   📜 Cert: <code>{settings_obj['webCertFile']}</code>\n"
            if "webKeyFile" in settings_obj:
                text += f"   🔑 Key: <code>{settings_obj['webKeyFile']}</code>\n"
        
        # Настройки подписки
        if "subPort" in settings_obj:
            text += f"\n📡 <b>Подписка:</b>\n"
            text += f"   Порт: <code>{settings_obj['subPort']}</code>\n"
        
        if "subPath" in settings_obj:
            text += f"   Путь: <code>{settings_obj['subPath']}</code>\n"
        
        if "subDomain" in settings_obj and settings_obj['subDomain']:
            text += f"   Домен: <code>{settings_obj['subDomain']}</code>\n"
        
        if "subCertFile" in settings_obj or "subKeyFile" in settings_obj:
            text += f"\n🔐 <b>SSL подписки:</b>\n"
            if "subCertFile" in settings_obj:
                text += f"   📜 Cert: <code>{settings_obj['subCertFile']}</code>\n"
            if "subKeyFile" in settings_obj:
                text += f"   🔑 Key: <code>{settings_obj['subKeyFile']}</code>\n"
        
        # Другие настройки
        if "sessionTimeout" in settings_obj:
            text += f"\n⏱ Таймаут сессии: {settings_obj['sessionTimeout']} мин\n"
        
        if "timeLocation" in settings_obj:
            text += f"🌍 Часовой пояс: {settings_obj['timeLocation']}\n"
        
        if "trafficAge" in settings_obj:
            text += f"📊 Возраст трафика: {settings_obj['trafficAge']} дней\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении настроек: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении настроек:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "logs")
async def callback_logs(callback: CallbackQuery):
    """Показать меню логов."""
    await callback.answer()
    await callback.message.edit_text(
        "📝 Выберите количество записей логов:",
        reply_markup=get_logs_menu(),
    )


@router.callback_query(F.data.startswith("logs_"))
async def callback_logs_count(callback: CallbackQuery):
    """Показать логи с определённым количеством записей."""
    await callback.answer()
    
    count = int(callback.data.split("_")[1])
    
    try:
        response = await sui_client.get_logs(count=count)
        logs = response.get("obj", [])
        
        if not logs:
            await callback.message.edit_text(
                "📝 <b>Логи:</b>\n\nЛоги не найдены.",
                parse_mode="HTML",
                reply_markup=get_back_button(),
            )
            return
        
        text = f"📝 <b>Последние {count} записей логов:</b>\n\n"
        text += "```\n"
        
        # Берём последние записи и показываем их в хронологическом порядке (старые сверху, новые снизу)
        for log in logs[-count:]:
            text += f"{log}\n"
        
        text += "```"
        
        # Если слишком длинно, обрезаем
        if len(text) > 4000:
            text = text[:4000] + "\n```\n... (логи обрезаны)"
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при получении логов: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении логов:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "restart_core")
async def callback_restart_core(callback: CallbackQuery):
    """Запрос подтверждения перезапуска Core."""
    await callback.answer()
    await callback.message.edit_text(
        "🔄 <b>Перезапуск Sing-Box Core</b>\n\n"
        "Вы уверены, что хотите перезапустить Core?\n"
        "Это временно прервёт все активные соединения.",
        parse_mode="HTML",
        reply_markup=get_confirm_restart("restart_core"),
    )


@router.callback_query(F.data == "restart_app")
async def callback_restart_app(callback: CallbackQuery):
    """Запрос подтверждения перезапуска приложения."""
    await callback.answer()
    await callback.message.edit_text(
        "🔄 <b>Перезапуск приложения S-UI</b>\n\n"
        "Вы уверены, что хотите перезапустить приложение?\n"
        "Это может занять некоторое время.",
        parse_mode="HTML",
        reply_markup=get_confirm_restart("restart_app"),
    )


@router.callback_query(F.data == "confirm_restart_core")
async def callback_confirm_restart_core(callback: CallbackQuery):
    """Подтверждённый перезапуск Core."""
    await callback.answer("Перезапускаю Core...")
    
    try:
        await sui_client.restart_core()
        await callback.message.edit_text(
            "✅ Sing-Box Core успешно перезапущен!",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при перезапуске Core: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при перезапуске Core:\n{str(e)}",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "confirm_restart_app")
async def callback_confirm_restart_app(callback: CallbackQuery):
    """Подтверждённый перезапуск приложения."""
    await callback.answer("Перезапускаю приложение...")
    
    try:
        await sui_client.restart_app()
        await callback.message.edit_text(
            "✅ Приложение S-UI успешно перезапущено!",
            reply_markup=get_back_button(),
        )
    except SUiAPIError as e:
        logger.error(f"Ошибка при перезапуске приложения: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при перезапуске приложения:\n{str(e)}",
            reply_markup=get_back_button(),
        )

