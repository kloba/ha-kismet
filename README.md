# Kismet Integration for Home Assistant

[![HACS Validation](https://github.com/kloba/ha-kismet/actions/workflows/hacs.yml/badge.svg)](https://github.com/kloba/ha-kismet/actions/workflows/hacs.yml)
[![Hassfest Validation](https://github.com/kloba/ha-kismet/actions/workflows/hassfest.yml/badge.svg)](https://github.com/kloba/ha-kismet/actions/workflows/hassfest.yml)

A Home Assistant custom component for [Kismet Wireless](https://www.kismetwireless.net/) IDS/IPS. Polls the Kismet REST API to expose sensors, binary sensors, and device tracking in Home Assistant.

## Features

- **Sensors**: Uptime, memory usage, total/active/WiFi/BLE device counts, alert count, packet rate, nearby devices
- **WiFi Signal Sensors**: Dynamic per-device sensors with signal quality (Strong/Good/Fair/Weak) — renders as colored timeline bars in history-graph
- **Binary Sensors**: Server online status, datasource status, alerts active
- **Device Tracker**: Track specific MAC addresses for presence detection
- **HACS Compatible**: Install via HACS custom repository

## Requirements

- Kismet server with REST API enabled (default port 2501)
- Kismet API key (found in `~/.kismet/kismet_httpd.conf` as `httpd_auth=`)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > **Custom Repositories**
3. Add `https://github.com/kloba/ha-kismet` with category **Integration**
4. Search for "Kismet" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/kismet/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "Kismet"
3. Enter your Kismet server details:
   - **Host**: IP address or hostname of your Kismet server
   - **Port**: REST API port (default: 2501)
   - **API Key**: Your Kismet API key

### Options

After adding the integration, configure options via the integration's **Configure** button:

| Option | Default | Description |
|--------|---------|-------------|
| Scan interval | 30s | How often to poll the Kismet server (10-300s) |
| Active device window | 300s | Devices seen within this window are considered active |
| Signal threshold | -60 dBm | Minimum signal strength for nearby device list |
| Tracked MACs | (empty) | Comma-separated MAC addresses for presence tracking |
| Enable device tracker | Off | Create device tracker entities for tracked MACs |

## Entities

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.kismet_uptime` | Server start timestamp |
| `sensor.kismet_memory_usage` | RSS memory usage (MiB) |
| `sensor.kismet_total_devices` | Total devices ever seen |
| `sensor.kismet_active_devices` | Currently active devices |
| `sensor.kismet_wifi_devices` | Active WiFi (802.11) devices |
| `sensor.kismet_ble_devices` | Active BLE devices |
| `sensor.kismet_alerts` | Total alert count (last alert text as attribute) |
| `sensor.kismet_packet_rate` | Current packet rate (pkt/s) |
| `sensor.kismet_nearby_devices` | Count of nearby WiFi clients (device list as attribute) |

### WiFi Signal Quality Sensors

Dynamically created for each WiFi client device detected by Kismet. Uses `SensorDeviceClass.ENUM` with states **Strong**, **Good**, **Fair**, **Weak** — HA renders these as colored timeline bars in history-graph cards.

- Signal thresholds: Strong (>= -40 dBm), Good (-40 to -55), Fair (-55 to -70), Weak (< -70)
- Entity becomes `unavailable` (grey in timeline) when device is not active
- Devices are retained in memory for 8 hours after last detection
- Labels: `Manufacturer (XXYY)` for known vendors, full MAC for unknown
- Extra attributes: `mac`, `manufacturer`, `signal_dbm`, `signal_strength` (0-100 scale)

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.kismet_server_online` | Server connectivity status |
| `binary_sensor.kismet_alerts_active` | Whether any alerts exist |
| `binary_sensor.kismet_datasource_*` | Per-datasource online status |

### Device Trackers

When enabled with tracked MACs, creates `device_tracker.kismet_<mac>` entities with `home`/`not_home` state based on the active device window.

## Getting Your API Key

The Kismet API key is stored in `~/.kismet/kismet_httpd.conf`:

```
httpd_auth=your_api_key_here
```

You can also generate a new key in the Kismet web UI under **Settings**.
