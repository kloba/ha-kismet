# Kismet Integration for Home Assistant

[![HACS Validation](https://github.com/kloba/ha-kismet/actions/workflows/hacs.yml/badge.svg)](https://github.com/kloba/ha-kismet/actions/workflows/hacs.yml)
[![Hassfest Validation](https://github.com/kloba/ha-kismet/actions/workflows/hassfest.yml/badge.svg)](https://github.com/kloba/ha-kismet/actions/workflows/hassfest.yml)

A Home Assistant custom component for [Kismet Wireless](https://www.kismetwireless.net/) IDS/IPS. Polls the Kismet REST API to expose sensors, binary sensors, and device tracking in Home Assistant.

## Features

- **Sensors**: Uptime, memory usage, total/active/WiFi/BLE device counts, alert count, packet rate
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
