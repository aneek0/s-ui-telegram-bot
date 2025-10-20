"""Клиент для работы с S-UI API."""

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class SUiAPIError(Exception):
    """Ошибка API S-UI."""
    pass


class SUiClient:
    """Клиент для взаимодействия с S-UI API."""

    def __init__(self, base_url: str, token: str):
        """
        Инициализация клиента.

        Args:
            base_url: Базовый URL API (например, http://localhost:2095/app)
            token: API токен для аутентификации
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session: aiohttp.ClientSession | None = None

    async def _ensure_session(self):
        """Создать сессию если её нет."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Token": self.token}
            )

    async def close(self):
        """Закрыть сессию."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Выполнить HTTP запрос к API.

        Args:
            method: HTTP метод
            endpoint: Эндпоинт API
            params: Query параметры
            data: Данные для POST запроса

        Returns:
            Ответ API

        Raises:
            SUiAPIError: При ошибке API
        """
        await self._ensure_session()

        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
            ) as response:
                # Проверяем статус код
                if response.status == 401:
                    raise SUiAPIError("Неверный API токен. Получите новый токен из панели S-UI.")
                
                if response.status == 403:
                    raise SUiAPIError("Доступ запрещен. Проверьте права API токена.")
                
                # Проверяем Content-Type
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    raise SUiAPIError(
                        "API вернул HTML вместо JSON. Возможно токен устарел или неверный. "
                        "Получите новый токен: откройте панель S-UI → F12 → Network → "
                        "найдите любой API запрос → скопируйте заголовок 'Token'"
                    )
                
                # Пытаемся распарсить JSON
                try:
                    response_data = await response.json()
                except aiohttp.ContentTypeError as e:
                    text = await response.text()
                    logger.error(f"Не удалось распарсить JSON. Ответ: {text[:500]}")
                    raise SUiAPIError(f"Неверный формат ответа от API: {str(e)}")

                if not response_data.get("success"):
                    error_msg = response_data.get("msg", "Неизвестная ошибка")
                    raise SUiAPIError(f"API Error: {error_msg}")

                return response_data

        except SUiAPIError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе к {url}: {e}")
            raise SUiAPIError(f"Ошибка подключения: {str(e)}")

    async def get_inbounds(self, inbound_id: str | None = None) -> dict[str, Any]:
        """
        Получить список inbound соединений.

        Args:
            inbound_id: ID конкретного inbound (опционально)

        Returns:
            Данные inbound
        """
        params = {"id": inbound_id} if inbound_id else None
        return await self._request("GET", "/apiv2/inbounds", params=params)

    async def get_clients(self, client_id: str | None = None) -> dict[str, Any]:
        """
        Получить список клиентов.

        Args:
            client_id: ID конкретного клиента (опционально)

        Returns:
            Данные клиентов
        """
        params = {"id": client_id} if client_id else None
        return await self._request("GET", "/apiv2/clients", params=params)

    async def get_status(self, resource: str = "cpu,ram,disk") -> dict[str, Any]:
        """
        Получить статус сервера.

        Args:
            resource: Типы ресурсов для получения (cpu, ram, disk)

        Returns:
            Статус сервера
        """
        return await self._request("GET", "/apiv2/status", params={"r": resource})

    async def get_stats(
        self,
        resource: str,
        tag: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Получить статистику.

        Args:
            resource: Тип ресурса
            tag: Тег
            limit: Лимит записей

        Returns:
            Статистические данные
        """
        params = {
            "resource": resource,
            "tag": tag,
            "limit": limit,
        }
        return await self._request("GET", "/apiv2/stats", params=params)

    async def get_onlines(self) -> dict[str, Any]:
        """
        Получить список онлайн пользователей.

        Returns:
            Список онлайн пользователей
        """
        return await self._request("GET", "/apiv2/onlines")

    async def get_settings(self) -> dict[str, Any]:
        """
        Получить настройки приложения.

        Returns:
            Настройки приложения
        """
        return await self._request("GET", "/apiv2/settings")

    async def get_users(self) -> dict[str, Any]:
        """
        Получить список пользователей панели.

        Returns:
            Список пользователей
        """
        return await self._request("GET", "/apiv2/users")

    async def save_config(
        self,
        obj: str,
        action: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Сохранить конфигурацию.

        Args:
            obj: Тип объекта (inbound, client, etc.)
            action: Действие (add, update, delete)
            data: Данные для сохранения

        Returns:
            Результат операции
        """
        request_data = {
            "object": obj,
            "action": action,
            "data": data,
        }
        return await self._request("POST", "/apiv2/save", data=request_data)

    async def restart_app(self) -> dict[str, Any]:
        """
        Перезапустить приложение S-UI.

        Returns:
            Результат операции
        """
        return await self._request("POST", "/apiv2/restartApp")

    async def restart_core(self) -> dict[str, Any]:
        """
        Перезапустить Sing-Box Core.

        Returns:
            Результат операции
        """
        return await self._request("POST", "/apiv2/restartSb")

    async def get_logs(self, count: int = 100, level: str = "") -> dict[str, Any]:
        """
        Получить логи сервера.

        Args:
            count: Количество записей
            level: Уровень логирования

        Returns:
            Логи сервера
        """
        params = {"c": count}
        if level:
            params["l"] = level
        return await self._request("GET", "/apiv2/logs", params=params)

    async def load_full_data(self, last_update: str = "") -> dict[str, Any]:
        """
        Загрузить все данные.

        Args:
            last_update: Временная метка последнего обновления

        Returns:
            Полные данные системы
        """
        params = {"lu": last_update} if last_update else None
        return await self._request("GET", "/apiv2/load", params=params)

    async def get_outbounds(self) -> dict[str, Any]:
        """
        Получить список outbound соединений.

        Returns:
            Данные outbound
        """
        return await self._request("GET", "/apiv2/outbounds")

    async def get_endpoints(self) -> dict[str, Any]:
        """
        Получить endpoint объекты.

        Returns:
            Endpoints
        """
        return await self._request("GET", "/apiv2/endpoints")

    async def get_services(self) -> dict[str, Any]:
        """
        Получить service объекты.

        Returns:
            Services
        """
        return await self._request("GET", "/apiv2/services")

    async def get_tls(self) -> dict[str, Any]:
        """
        Получить TLS объекты.

        Returns:
            TLS данные
        """
        return await self._request("GET", "/apiv2/tls")

    async def get_config(self) -> dict[str, Any]:
        """
        Получить конфигурационные объекты.

        Returns:
            Конфигурация
        """
        return await self._request("GET", "/apiv2/config")

    async def get_changes(
        self,
        actor: str = "",
        key: str = "",
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Получить изменения пользователей.

        Args:
            actor: Имя актора (опционально)
            key: Ключ (опционально)
            limit: Лимит записей

        Returns:
            История изменений
        """
        params = {"c": limit}
        if actor:
            params["a"] = actor
        if key:
            params["k"] = key
        return await self._request("GET", "/apiv2/changes", params=params)

    async def convert_link(self, link: str) -> dict[str, Any]:
        """
        Конвертировать ссылку.

        Args:
            link: Ссылка для конвертации

        Returns:
            Результат конвертации
        """
        return await self._request("POST", "/apiv2/linkConvert", data={"link": link})

