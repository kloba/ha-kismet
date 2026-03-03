"""Base entity for the Kismet integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KismetCoordinator, KismetData


class KismetEntity(CoordinatorEntity[KismetCoordinator]):
    """Base entity for Kismet."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KismetCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"

        version = None
        if coordinator.data:
            version = coordinator.data.system_status.get(
                "kismet.system.version"
            )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Kismet",
            manufacturer="Kismet",
            sw_version=version,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=(
                f"http://{entry.data['host']}:{entry.data['port']}"
            ),
        )
