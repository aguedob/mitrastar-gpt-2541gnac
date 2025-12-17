"""Sensor platform for Mitrastar GPT-2541GNAC integration."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    UnitOfDataRate,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitrastar sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    router_device_info = data["device_info"]

    # Device information with real data from router
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=router_device_info.get("model", "Mitrastar GPT-2541GNAC"),
        manufacturer=router_device_info.get("manufacturer", "Mitrastar"),
        model=router_device_info.get("model", "GPT-2541GNAC"),
        sw_version=router_device_info.get("sw_version"),
        hw_version=router_device_info.get("hw_version"),
        serial_number=router_device_info.get("serial_number"),
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )

    sensors = []

    # LAN interface sensors (eth0-eth4)
    for interface in ["eth0", "eth1", "eth2", "eth3", "eth4"]:
        for direction in ["rx", "tx"]:
            prefix = f"lan_{interface}_{direction}"

            # Status sensor
            sensors.append(
                MitrastarSensor(
                    coordinator,
                    device_info,
                    f"{prefix}_status",
                    f"LAN {interface.upper()} {direction.upper()} Status",
                    None,
                    None,
                    None,
                    "mdi:ethernet",
                )
            )

            # Byte counters
            sensors.append(
                MitrastarSensor(
                    coordinator,
                    device_info,
                    f"{prefix}_total_bytes",
                    f"LAN {interface.upper()} {direction.upper()} Total Bytes",
                    UnitOfInformation.BYTES,
                    SensorDeviceClass.DATA_SIZE,
                    SensorStateClass.TOTAL_INCREASING,
                    "mdi:counter",
                )
            )

            # Packet counters
            for metric in [
                "total_packets",
                "multicast_packets",
                "unicast_packets",
                "broadcast_packets",
            ]:
                sensors.append(
                    MitrastarSensor(
                        coordinator,
                        device_info,
                        f"{prefix}_{metric}",
                        f"LAN {interface.upper()} {direction.upper()} {metric.replace('_', ' ').title()}",
                        "packets",
                        None,
                        SensorStateClass.TOTAL_INCREASING,
                        "mdi:package-variant",
                    )
                )

            # Error counters
            for metric in ["errors", "drops"]:
                sensors.append(
                    MitrastarSensor(
                        coordinator,
                        device_info,
                        f"{prefix}_{metric}",
                        f"LAN {interface.upper()} {direction.upper()} {metric.title()}",
                        metric,
                        None,
                        SensorStateClass.TOTAL_INCREASING,
                        "mdi:alert-circle",
                    )
                )

    # Add speed sensors for active LAN interfaces
    for interface in ["eth1", "eth3", "eth4"]:
        for direction in ["rx", "tx"]:
            prefix = f"lan_{interface}_{direction}"
            direction_name = "Download" if direction == "rx" else "Upload"
            
            sensors.append(
                MitrastarSpeedSensor(
                    coordinator,
                    device_info,
                    f"{prefix}_total_bytes",
                    f"LAN {interface.upper()} {direction_name} Speed",
                    "mdi:speedometer",
                )
            )

    # WAN interface sensors
    for interface in ["veip0.2", "veip0.3", "ppp0.1"]:
        safe_interface = interface.replace(".", "_")
        for direction in ["rx", "tx"]:
            prefix = f"wan_{interface}_{direction}"

            # Byte counters
            sensors.append(
                MitrastarSensor(
                    coordinator,
                    device_info,
                    f"{prefix}_total_bytes",
                    f"WAN {interface} {direction.upper()} Total Bytes",
                    UnitOfInformation.BYTES,
                    SensorDeviceClass.DATA_SIZE,
                    SensorStateClass.TOTAL_INCREASING,
                    "mdi:counter",
                )
            )

            # Packet counters
            for metric in [
                "total_packets",
                "multicast_packets",
                "unicast_packets",
                "broadcast_packets",
            ]:
                sensors.append(
                    MitrastarSensor(
                        coordinator,
                        device_info,
                        f"{prefix}_{metric}",
                        f"WAN {interface} {direction.upper()} {metric.replace('_', ' ').title()}",
                        "packets",
                        None,
                        SensorStateClass.TOTAL_INCREASING,
                        "mdi:package-variant",
                    )
                )

            # Error counters
            for metric in ["errors", "drops"]:
                sensors.append(
                    MitrastarSensor(
                        coordinator,
                        device_info,
                        f"{prefix}_{metric}",
                        f"WAN {interface} {direction.upper()} {metric.title()}",
                        metric,
                        None,
                        SensorStateClass.TOTAL_INCREASING,
                        "mdi:alert-circle",
                    )
                )

    # Add speed sensors for WAN interface (mainly ppp0.1)
    for direction in ["rx", "tx"]:
        prefix = f"wan_ppp0.1_{direction}"
        direction_name = "Download" if direction == "rx" else "Upload"
        
        sensors.append(
            MitrastarSpeedSensor(
                coordinator,
                device_info,
                f"{prefix}_total_bytes",
                f"WAN {direction_name} Speed",
                "mdi:speedometer",
            )
        )

    # Laser/Optical sensors
    sensors.extend(
        [
            MitrastarSensor(
                coordinator,
                device_info,
                "laser_rx_power",
                "Optical RX Power",
                "dBm",
                None,
                SensorStateClass.MEASUREMENT,
                "mdi:signal",
            ),
            MitrastarSensor(
                coordinator,
                device_info,
                "laser_tx_power",
                "Optical TX Power",
                "dBm",
                None,
                SensorStateClass.MEASUREMENT,
                "mdi:signal",
            ),
            MitrastarSensor(
                coordinator,
                device_info,
                "laser_bias_current",
                "Laser Bias Current",
                UnitOfElectricCurrent.MILLIAMPERE,
                SensorDeviceClass.CURRENT,
                SensorStateClass.MEASUREMENT,
                "mdi:current-dc",
            ),
            MitrastarSensor(
                coordinator,
                device_info,
                "laser_voltage",
                "Laser Supply Voltage",
                UnitOfElectricPotential.VOLT,
                SensorDeviceClass.VOLTAGE,
                SensorStateClass.MEASUREMENT,
                "mdi:lightning-bolt",
            ),
            MitrastarSensor(
                coordinator,
                device_info,
                "laser_temperature",
                "SFF Temperature",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                SensorStateClass.MEASUREMENT,
                "mdi:thermometer",
            ),
        ]
    )

    async_add_entities(sensors)


class MitrastarSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Mitrastar sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
        key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        self._attr_unique_id = f"mitrastar_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._key in self.coordinator.data
        )


class MitrastarSpeedSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Mitrastar speed/bandwidth sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
        source_key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the speed sensor."""
        super().__init__(coordinator)
        self._source_key = source_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = UnitOfDataRate.BYTES_PER_SECOND
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = icon
        self._attr_unique_id = f"mitrastar_{source_key}_speed"
        self._attr_device_info = device_info
        self._last_value = None
        self._last_update = None

    @property
    def native_value(self):
        """Return the speed calculated from the difference."""
        if self._source_key not in self.coordinator.data:
            return None

        current_value = self.coordinator.data.get(self._source_key)
        if current_value is None:
            return None

        current_time = datetime.now()

        # Need at least two readings to calculate speed
        if self._last_value is None or self._last_update is None:
            self._last_value = current_value
            self._last_update = current_time
            return 0

        # Calculate time difference in seconds
        time_diff = (current_time - self._last_update).total_seconds()
        
        if time_diff <= 0:
            return self.native_value if hasattr(self, '_cached_speed') else 0

        # Calculate bytes difference
        value_diff = current_value - self._last_value
        
        # Handle counter reset (shouldn't happen, but just in case)
        if value_diff < 0:
            self._last_value = current_value
            self._last_update = current_time
            return 0

        # Calculate speed (bytes per second)
        speed = value_diff / time_diff

        # Update last values
        self._last_value = current_value
        self._last_update = current_time
        self._cached_speed = round(speed, 2)

        return self._cached_speed

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._source_key in self.coordinator.data
        )
