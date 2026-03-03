"""Async API client for Kismet REST API."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import (
    DEFAULT_SCHEME,
    DEVICE_FIELDS,
    ENDPOINT_ACTIVE_DEVICES,
    ENDPOINT_ALERTS_LAST_TIME,
    ENDPOINT_ALL_ALERTS,
    ENDPOINT_DATASOURCES,
    ENDPOINT_DEVICES_BY_MAC,
    ENDPOINT_SYSTEM_STATUS,
    STATUS_FIELDS,
)

_LOGGER = logging.getLogger(__name__)


class KismetAuthError(Exception):
    """Raised when API key is invalid."""


class KismetConnectionError(Exception):
    """Raised when unable to connect to Kismet."""


class KismetApiClient:
    """Async client for Kismet REST API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        port: int,
        api_key: str,
        *,
        scheme: str = DEFAULT_SCHEME,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._base_url = f"{scheme}://{host}:{port}"
        self._cookies = {"KISMET": api_key}

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an authenticated request to Kismet."""
        url = f"{self._base_url}{endpoint}"
        try:
            resp = await self._session.request(
                method,
                url,
                cookies=self._cookies,
                json=json_data,
                timeout=30,
            )
            if resp.status == 401:
                raise KismetAuthError("Invalid API key")
            resp.raise_for_status()
            return await resp.json(content_type=None)
        except KismetAuthError:
            raise
        except ClientResponseError as err:
            if err.status == 401:
                raise KismetAuthError("Invalid API key") from err
            raise KismetConnectionError(
                f"HTTP error {err.status}: {err.message}"
            ) from err
        except ClientError as err:
            raise KismetConnectionError(
                f"Cannot connect to Kismet at {self._base_url}: {err}"
            ) from err

    async def async_check_connection(self) -> dict[str, Any]:
        """Check connection and auth by fetching system status."""
        return await self._request("GET", ENDPOINT_SYSTEM_STATUS)

    async def async_get_system_status(self) -> dict[str, Any]:
        """Get system status with field simplification."""
        return await self._request(
            "POST",
            ENDPOINT_SYSTEM_STATUS,
            json_data={"fields": STATUS_FIELDS},
        )

    async def async_get_datasources(self) -> list[dict[str, Any]]:
        """Get all datasources."""
        return await self._request("GET", ENDPOINT_DATASOURCES)

    async def async_get_all_alerts(self) -> list[dict[str, Any]]:
        """Get all alerts."""
        return await self._request("GET", ENDPOINT_ALL_ALERTS)

    async def async_get_alerts_since(self, timestamp: int) -> list[dict[str, Any]]:
        """Get alerts since a given timestamp."""
        endpoint = ENDPOINT_ALERTS_LAST_TIME.replace("{ts}", str(timestamp))
        result = await self._request("GET", endpoint)
        if isinstance(result, dict):
            return result.get("kismet.alert.list", [])
        return result if isinstance(result, list) else []

    async def async_get_active_devices(
        self, timestamp: int
    ) -> list[dict[str, Any]]:
        """Get devices active since timestamp with field simplification."""
        endpoint = ENDPOINT_ACTIVE_DEVICES.replace("{ts}", str(timestamp))
        return await self._request(
            "POST",
            endpoint,
            json_data={"fields": DEVICE_FIELDS},
        )

    async def async_get_devices_by_mac(
        self, macs: list[str]
    ) -> list[dict[str, Any]]:
        """Get specific devices by MAC address."""
        return await self._request(
            "POST",
            ENDPOINT_DEVICES_BY_MAC,
            json_data={
                "devices": macs,
                "fields": DEVICE_FIELDS,
            },
        )
