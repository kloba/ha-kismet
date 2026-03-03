"""The Kismet integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KismetApiClient
from .const import (
    CONF_API_KEY,
    CONF_ENABLE_DEVICE_TRACKER,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import KismetCoordinator

type KismetConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: KismetConfigEntry) -> bool:
    """Set up Kismet from a config entry."""
    session = async_get_clientsession(hass)
    client = KismetApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_API_KEY],
    )

    coordinator = KismetCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    platforms = [Platform(p) for p in PLATFORMS]
    if entry.options.get(CONF_ENABLE_DEVICE_TRACKER, False):
        platforms.append(Platform.DEVICE_TRACKER)

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: KismetConfigEntry) -> bool:
    """Unload a config entry."""
    platforms = [Platform(p) for p in PLATFORMS]
    if entry.options.get(CONF_ENABLE_DEVICE_TRACKER, False):
        platforms.append(Platform.DEVICE_TRACKER)

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, platforms
    ):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: KismetConfigEntry
) -> None:
    """Handle options update — reload the entry."""
    await hass.config_entries.async_reload(entry.entry_id)
