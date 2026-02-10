# Raspberry Pi Smart Thermostat

A fully customizable, schedule-driven thermostat system for Raspberry Pi that monitors temperature and humidity using I2C sensors and automatically controls HVAC systems based on time-of-day schedules.

## Overview

This project implements a thermostat control system that:
- Reads temperature and humidity data from HDC302x sensors via I2C
- Applies control logic based on customizable daily schedules
- Uses hysteresis to prevent rapid cycling (short cycling)
- Determines HVAC actions (HEAT_ON, HEAT_OFF, COOL_ON, COOL_OFF, FAN_ON, SYSTEM_OFF)
- Runs continuously as a systemd service with automatic restart capabilities

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [System Service Setup](#system-service-setup)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## Hardware Requirements

- **Raspberry Pi**: Raspberry Pi Zero 2 W (or compatible model)
- **Temperature/Humidity Sensor**: HDC302x
- **I2C Multiplexer**: TCA9548A (sensor connected on channel 0)
- **HVAC Interface**: Relay board or GPIO-controlled device

## Project Structure

| File | Purpose |
|------|---------|
| `thermostat_control.py` | Main application logic. Contains the control loop that reads settings, checks schedules, fetches sensor data, and determines HVAC actions. |
| `schedule.py` | Defines the daily temperature/mode schedule (time, target temperature, mode). |
| `settings.json` | Stores operational state and configuration (mode, hysteresis, timezone, etc.). |
| `data_collector.py` | Wrapper script that calls `sensor_reading.py` and outputs JSON-formatted sensor data for inter-process communication. |
| `sensor_reading.py` | Hardware interaction layer. Initializes I2C bus, TCA9548A multiplexer, and HDC302x sensor to read temperature and humidity. |
| `start_thermostat.sh` | Startup wrapper script that automatically detects and uses a virtual environment if available. |
| `thermostat.service` | Systemd service file for running the thermostat as a background service. |

## Installation

### 1. Enable I2C Interface

Enable the I2C interface on your Raspberry Pi:

```bash
sudo raspi-config
# Navigate to: 3 Interface Options → I5 I2C → Yes
```

### 2. Install Python Dependencies

**Option A: Using a Virtual Environment (Recommended)**

```bash
# Navigate to your project directory
cd /path/to/Thermostat

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required libraries
pip install -r requirements.txt
```

**Option B: System-wide Installation**

```bash
# Ensure pip is up to date
sudo pip3 install --break-system-packages --upgrade pip

# Install required libraries
sudo pip3 install --break-system-packages -r requirements.txt
```

**Note:** The systemd service automatically uses the virtual environment if it exists in the project directory. Otherwise, it falls back to system `python3`.

### 3. Configure Project Paths

After cloning the repository, update the following files with your system-specific paths:

**a. Update `settings.json`:**
```json
{
    "project_path": "/home/your_username/Thermostat"
}
```

**b. Update `thermostat.service`:**
Edit the following lines:
- `User=your_username` (replace `landon` with your username)
- `WorkingDirectory=/home/your_username/Thermostat`
- `ExecStart=/home/your_username/Thermostat/start_thermostat.sh`

**c. Make the startup script executable:**
```bash
chmod +x start_thermostat.sh
```

## Configuration

### Settings (`settings.json`)

The `settings.json` file stores operational configuration:

```json
{
    "current_mode": "HEAT",
    "manual_target_f": 72.0,
    "hysteresis": 1.5,
    "timezone": "America/Chicago",
    "last_check_time": "2025-12-02T06:47:20.535415",
    "project_path": "/home/your_username/Thermostat"
}
```

**Key Settings:**
- **`hysteresis`**: Temperature band (in °F) around the target temperature to prevent rapid cycling
  - HEAT ON triggers at `Target - Hysteresis`
  - COOL ON triggers at `Target + Hysteresis`
- **`timezone`**: Critical for correct schedule timing. Use IANA timezone names (e.g., `"America/New_York"`, `"America/Chicago"`, `"Europe/London"`)

### Schedule (`schedule.py`)

Edit the `THERMOSTAT_SCHEDULE` list in `schedule.py` to define your daily temperature schedule. The control logic automatically applies the setting corresponding to the most recent time entry that has passed.

**Schedule Entry Format:**
| Key | Description | Example |
|-----|-------------|---------|
| `time` | 24-hour time to activate the setting | `'14:00'` (2 PM) |
| `target_f` | Desired Fahrenheit temperature setpoint | `68.0` |
| `mode` | System control mode | `'OFF'`, `'HEAT'`, `'COOL'`, `'FAN'` |

**Example Schedule:**
```python
THERMOSTAT_SCHEDULE = [
    {'time': '06:00', 'target_f': 72.0, 'mode': 'HEAT'},
    {'time': '08:00', 'target_f': 65.0, 'mode': 'OFF'},
    {'time': '17:00', 'target_f': 70.0, 'mode': 'COOL'},
    {'time': '22:00', 'target_f': 68.0, 'mode': 'COOL'},
]
```

## Usage

### Manual Execution

Run the thermostat control script directly:

```bash
# Navigate to your project directory
cd /path/to/Thermostat

# Activate virtual environment (if using one)
source venv/bin/activate

# Run the main control script
python3 thermostat_control.py
```

The script runs continuously, checking sensor data and applying control logic every 30 seconds.

### Testing Sensor Reading

Test the sensor hardware independently:

```bash
python3 sensor_reading.py
```

This will output a snapshot of current temperature and humidity readings.

## System Service Setup

To run the thermostat as a background service that starts automatically on boot:

### 1. Setup Systemd Service

**Important:** Before proceeding, ensure you have:
1. Updated paths in `thermostat.service` (User, WorkingDirectory, ExecStart)
2. Made `start_thermostat.sh` executable: `chmod +x start_thermostat.sh`
3. (Optional) Created and activated a virtual environment with dependencies installed

Create a symbolic link to enable the service:

```bash
# Link the service file to systemd directory
sudo ln -s /home/your_username/Thermostat/thermostat.service /etc/systemd/system/thermostat.service

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable thermostat.service

# Start the service
sudo systemctl start thermostat.service

# Check the service status
sudo systemctl status thermostat.service
```

### 2. Service Management

**View logs:**
```bash
sudo journalctl -u thermostat.service -f
```

**Stop the service:**
```bash
sudo systemctl stop thermostat.service
```

**Restart the service:**
```bash
sudo systemctl restart thermostat.service
```

**Disable auto-start on boot:**
```bash
sudo systemctl disable thermostat.service
```

**How it works:** The `start_thermostat.sh` wrapper script automatically detects if a virtual environment exists in the project directory. If `venv/bin/python3` is found, it uses that. Otherwise, it falls back to system `python3`.

## Customization

### Adding New Schedule Entries

Add entries to `THERMOSTAT_SCHEDULE` in `schedule.py`. Entries are automatically sorted by time, and the most recent passed time entry becomes active.

### Adjusting Hysteresis

Modify the `hysteresis` value in `settings.json` to change the temperature band:
- **Lower values** (e.g., 0.5°F): More frequent cycling, tighter temperature control
- **Higher values** (e.g., 2.0°F): Less frequent cycling, wider temperature range

### Changing Timezone

Update the `timezone` field in `settings.json` with your IANA timezone name. Common examples:
- `"America/New_York"` (Eastern Time)
- `"America/Chicago"` (Central Time)
- `"America/Denver"` (Mountain Time)
- `"America/Los_Angeles"` (Pacific Time)
- `"Europe/London"` (UK Time)

## Troubleshooting

### Sensor Reading Failures

**Problem:** `CRITICAL: Failed to get valid sensor data`

**Solutions:**
1. Verify I2C is enabled: `sudo raspi-config` → Interface Options → I2C
2. Check I2C device detection: `i2cdetect -y 1`
3. Verify sensor connections and I2C address
4. Test sensor directly: `python3 sensor_reading.py`

### Service Won't Start

**Problem:** Service fails to start or crashes immediately

**Solutions:**
1. Check service status: `sudo systemctl status thermostat.service`
2. View logs: `sudo journalctl -u thermostat.service -n 50`
3. Verify all paths in `thermostat.service` are correct
4. Ensure `start_thermostat.sh` is executable: `chmod +x start_thermostat.sh`
5. Test manual execution: `./start_thermostat.sh`

### Timezone Issues

**Problem:** Schedule times don't match expected times

**Solutions:**
1. Verify timezone in `settings.json` uses IANA format
2. Check system timezone: `timedatectl`
3. Ensure Raspberry Pi has correct system time (consider using NTP)

### Import Errors

**Problem:** `ModuleNotFoundError` when running scripts

**Solutions:**
1. Verify dependencies are installed: `pip list`
2. If using venv, ensure it's activated: `source venv/bin/activate`
3. Reinstall requirements: `pip install -r requirements.txt`

### Permission Errors

**Problem:** Permission denied errors when accessing files

**Solutions:**
1. Verify file ownership: `ls -l`
2. Ensure service user matches file owner
3. Check `settings.json` permissions are readable
