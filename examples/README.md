# Dashboard Examples

This folder contains dashboard and card examples to visualize data from the Mitrastar GPT-2541GNAC router in Home Assistant.

## Available Files

### 1. `dashboard_example.yaml`
Contains examples using native Home Assistant (Lovelace) cards. No additional installation required.

**Includes:**
- Router overview with optical information
- Gauges for RX/TX power and temperature
- Status of all LAN interfaces
- WAN statistics
- Traffic graphs (requires Statistics integration)
- Error monitoring
- Quick port status view

### 2. `apexcharts_example.yaml`
Advanced graphs using ApexCharts Card. Requires installation from HACS.

**Features:**
- Real-time bandwidth graphs
- LAN port comparison
- Historical optical signal monitoring
- Temperature graphs

**Installation:**
```
HACS → Frontend → Search "ApexCharts Card" → Install
```

### 3. `mini_graph_card_example.yaml`
Elegant and compact graphs using Mini Graph Card. Requires installation from HACS.

**Features:**
- Smooth and attractive graphs
- Color thresholds for temperature
- 24h and 7-day views
- Graphs with gradient fill

**Installation:**
```
HACS → Frontend → Search "Mini Graph Card" → Install
```

## How to Use

### Method 1: Complete Dashboard (Recommended for beginners)
1. Go to **Settings** → **Dashboards**
2. Create a new dashboard or edit an existing one
3. Click the three dots → **Edit Dashboard** → **Raw Configuration Editor**
4. Copy and paste the content from `dashboard_example.yaml`
5. Save

### Method 2: Individual Cards
1. Edit your dashboard
2. Click **Add Card**
3. Select **Manual** (at the end of the list)
4. Copy and paste the card you want from the example file
5. Save

### Method 3: YAML View
1. In your dashboard, click the edit icon
2. Click the three dots → **Raw Configuration Editor**
3. Copy the sections you need
4. Paste into your existing configuration

## Customization

### Change Entities
If your sensors have different names, replace the `entity:` with the correct names. For example:

```yaml
# Before
entity: sensor.optical_rx_power

# After (if your sensor has a different name)
entity: sensor.mitrastar_optical_rx_power
```

### Adjust Colors
You can change colors using hexadecimal codes:

```yaml
color: '#1f77b4'  # Blue
color: '#ff7f0e'  # Orange
color: '#2ecc71'  # Green
color: '#e74c3c'  # Red
```

### Modify Thresholds
For gauges and graphs with threshold-based colors:

```yaml
severity:
  green: 0    # Green from this value
  yellow: 60  # Yellow from this value
  red: 70     # Red from this value
```

### Change Time Period
For graphs:

```yaml
hours_to_show: 24      # For Mini Graph Card
days_to_show: 7        # For Statistics Graph
graph_span: 12h        # For ApexCharts Card
```

## Recommended Cards by Use Case

### Basic Monitoring
Use `dashboard_example.yaml` - No additional installations required.

### Bandwidth Analysis
Use cards from `apexcharts_example.yaml` - Best for viewing trends and patterns.

### Compact Dashboard
Use `mini_graph_card_example.yaml` - Perfect for tablets or small screens.

### Troubleshooting
Use the "Network Errors & Drops" card from `dashboard_example.yaml` to detect issues.

## Available Sensors

### Optical Sensors
- `sensor.optical_rx_power` - Receive power (dBm)
- `sensor.optical_tx_power` - Transmit power (dBm)
- `sensor.sff_temperature` - SFP module temperature (°C)
- `sensor.laser_bias_current` - Laser current (mA)
- `sensor.laser_supply_voltage` - Supply voltage (V)

### LAN Sensors (eth0-eth4)
For each interface (e.g., eth1):
- `sensor.lan_eth1_rx_status` - Status (Up/Down/Disabled)
- `sensor.lan_eth1_rx_total_bytes` - Bytes received
- `sensor.lan_eth1_tx_total_bytes` - Bytes transmitted
- `sensor.lan_eth1_rx_total_packets` - Packets received
- `sensor.lan_eth1_tx_total_packets` - Packets transmitted
- `sensor.lan_eth1_rx_errors` - Reception errors
- `sensor.lan_eth1_tx_errors` - Transmission errors
- `sensor.lan_eth1_rx_drops` - Dropped packets (RX)
- `sensor.lan_eth1_tx_drops` - Dropped packets (TX)

### WAN Sensors
For each WAN interface (veip0.2, veip0.3, ppp0.1):
- `sensor.wan_ppp0_1_rx_total_bytes` - Bytes received
- `sensor.wan_ppp0_1_tx_total_bytes` - Bytes transmitted
- `sensor.wan_ppp0_1_rx_total_packets` - Packets received
- `sensor.wan_ppp0_1_tx_total_packets` - Packets transmitted
- And others similar to LAN...

### Speed Sensors (Real-time bandwidth)
- `sensor.wan_download_speed` - WAN download speed (B/s)
- `sensor.wan_upload_speed` - WAN upload speed (B/s)
- `sensor.lan_eth1_download_speed` - LAN port 1 download speed (B/s)
- `sensor.lan_eth1_upload_speed` - LAN port 1 upload speed (B/s)
- Similar sensors for eth3 and eth4

## Tips

1. **Performance**: If you have many graphs, increase the update interval to reduce load
2. **Storage**: Historical graphs require the recorder to be configured in Home Assistant
3. **Mobile**: `glance` type cards are perfect for mobile dashboards
4. **Notifications**: Combine these sensors with automations to receive problem alerts

## Automation Example

```yaml
# Notification when optical signal is low
automation:
  - alias: "Low Optical Signal Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.optical_rx_power
        below: -25
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Low Optical Signal"
          message: "RX Power: {{ states('sensor.optical_rx_power') }} dBm"
```

## Support

If you encounter any issues or have suggestions for new cards, open an issue on GitHub.
