"""Config flow for Kismet integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KismetApiClient, KismetAuthError, KismetConnectionError
from .const import (
    CONF_ACTIVE_WINDOW,
    CONF_API_KEY,
    CONF_ENABLE_DEVICE_TRACKER,
    CONF_SCAN_INTERVAL,
    CONF_TRACKED_MACS,
    DEFAULT_ACTIVE_WINDOW,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_API_KEY): str,
    }
)


class KismetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kismet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = KismetApiClient(
                session,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_API_KEY],
            )
            try:
                status = await client.async_check_connection()
            except KismetAuthError:
                errors["base"] = "invalid_auth"
            except KismetConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                version = status.get("kismet.system.version", "unknown")
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Kismet ({version})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> KismetOptionsFlow:
        """Get the options flow for this handler."""
        return KismetOptionsFlow(config_entry)


class KismetOptionsFlow(OptionsFlow):
    """Handle options for Kismet."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_ACTIVE_WINDOW,
                        default=options.get(
                            CONF_ACTIVE_WINDOW, DEFAULT_ACTIVE_WINDOW
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                    vol.Optional(
                        CONF_TRACKED_MACS,
                        default=options.get(CONF_TRACKED_MACS, ""),
                    ): str,
                    vol.Optional(
                        CONF_ENABLE_DEVICE_TRACKER,
                        default=options.get(
                            CONF_ENABLE_DEVICE_TRACKER, False
                        ),
                    ): bool,
                }
            ),
        )
