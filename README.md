# Mitrastar GPT-2541GNAC Home Assistant Integration

A custom Home Assistant integration for the Mitrastar GPT-2541GNAC router that exposes network statistics and optical transceiver information via SSH.

## Features

This integration provides sensors for:

### LAN Interface Statistics (eth0-eth4)
For each interface, both RX and TX directions:
- Status (Up/Down/Disabled)
- Total bytes and packets
- Multicast, Unicast, and Broadcast packet counts
- Error and drop counters

### WAN Interface Statistics
For veip0.2, veip0.3, and ppp0.1 interfaces:
- Total bytes and packets
- Multicast, Unicast, and Broadcast packet counts
- Error and drop counters
- VLAN ID information

### Optical Transceiver Statistics
- RX Optical Power (dBm)
- TX Optical Power (dBm)
- TX Bias Current (mA)
- Supply Voltage (V)
- SFF Temperature (°C)

## Requirements

### Router Configuration
- SSH access must be enabled on the router
- Router should support the following commands:
  - `showlanstats`
  - `showwanstats`
  - `lasercheck`

The integration uses the `asyncssh` Python library, which is automatically installed by Home Assistant. No additional system packages are required.

## Installation

### HACS Installation (Recommended)
1. Add this repository as a custom repository in HACS
2. Search for "Mitrastar GPT-2541GNAC" in HACS
3. Install the integration
4. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/mitrastar_gpt2541gnac` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Mitrastar GPT-2541GNAC"
4. Enter your router details:
   - **Host**: Router IP address (default: 192.168.1.1)
   - **Username**: SSH username (default: 1234)
   - **Password**: SSH password

## Usage

Once configured, all sensors will be automatically created and updated every 30 seconds.

### Example Sensors
- `sensor.lan_eth1_rx_total_bytes` - LAN port 1 received bytes
- `sensor.lan_eth1_tx_total_packets` - LAN port 1 transmitted packets
- `sensor.wan_ppp0_1_rx_total_bytes` - WAN PPP interface received bytes
- `sensor.optical_rx_power` - Fiber optic receive power
- `sensor.sff_temperature` - SFP module temperature

### Example Automations

Monitor fiber connection quality:
```yaml
automation:
  - alias: "Alert on low optical power"
    trigger:
      - platform: numeric_state
        entity_id: sensor.optical_rx_power
        below: -25
    action:
      - service: notify.mobile_app
        data:
          message: "Fiber RX power is low: {{ states('sensor.optical_rx_power') }} dBm"
```

Monitor network errors:
```yaml
automation:
  - alias: "Alert on LAN errors"
    trigger:
      - platform: state
        entity_id: sensor.lan_eth1_rx_errors
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int + 10 }}"
    action:
      - service: notify.mobile_app
        data:
          message: "LAN eth1 errors increased"
```

## Troubleshooting

### Connection Issues
- Verify SSH access: `ssh -oHostKeyAlgorithms=+ssh-rsa username@router_ip`
- Verify the router IP, username, and password are correct
- Check Home Assistant logs for detailed error messages
- Ensure the router supports legacy SSH RSA keys

### Missing Sensors
- Some sensors may not appear if the router doesn't return data for those interfaces
- Check the router's SSH output manually to verify available data

## Data Update Interval

The integration polls the router every 30 seconds by default. This can be adjusted in the `__init__.py` file by modifying the `SCAN_INTERVAL` constant.

## Security Considerations

- SSH credentials are stored encrypted in Home Assistant's configuration
- The integration uses SSH with legacy RSA host key algorithms required by the router
- Host key checking is disabled (router may not have stable SSH host keys)

## Support

For issues, feature requests, or contributions, please visit:
https://github.com/aguerrero/Mitrastar-GPT-2541GNAC

## License

This integration is provided as-is for personal use.
