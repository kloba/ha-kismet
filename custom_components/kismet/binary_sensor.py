"""Binary sensor platform for Kismet integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KismetCoordinator
from .entity import KismetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kismet binary sensors."""
    coordinator: KismetCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        KismetServerOnline(coordinator),
        KismetAlertsActive(coordinator),
    ]

    # Add per-datasource binary sensors
    if coordinator.data and coordinator.data.datasources:
        for source in coordinator.data.datasources:
            uuid = source.get("kismet.datasource.uuid", "")
            name = source.get(
                "kismet.datasource.name",
                source.get("kismet.datasource.interface", uuid),
            )
            if uuid:
                entities.append(
                    KismetDatasourceOnline(coordinator, uuid, name)
                )

    async_add_entities(entities)


class KismetServerOnline(KismetEntity, BinarySensorEntity):
    """Binary sensor for Kismet server online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "server_online"

    def __init__(self, coordinator: KismetCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, "server_online")

    @property
    def is_on(self) -> bool:
        """Return true if server is online."""
        return self.coordinator.data.online if self.coordinator.data else False


class KismetAlertsActive(KismetEntity, BinarySensorEntity):
    """Binary sensor for whether any alerts are active."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "alerts_active"

    def __init__(self, coordinator: KismetCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, "alerts_active")

    @property
    def is_on(self) -> bool:
        """Return true if there are alerts."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.alert_count > 0


class KismetDatasourceOnline(KismetEntity, BinarySensorEntity):
    """Binary sensor for datasource online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: KismetCoordinator,
        source_uuid: str,
        source_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, f"datasource_{source_uuid}")
        self._source_uuid = source_uuid
        self._attr_translation_key = "datasource_online"
        self._attr_name = f"Datasource {source_name}"

    @property
    def is_on(self) -> bool:
        """Return true if datasource is running."""
        if not self.coordinator.data:
            return False
        for source in self.coordinator.data.datasources:
            if source.get("kismet.datasource.uuid") == self._source_uuid:
                return bool(source.get("kismet.datasource.running", False))
        return False
