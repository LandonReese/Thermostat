Raspberry Pi Zero W Smart Thermostat Project

This project implements a fully customizable, schedule-driven thermostat system using a Raspberry Pi Zero 2 W. It reads temperature and humidity data from an I2C sensor (via an I2C multiplexer), applies control logic based on a defined schedule and hysteresis, and determines the required action (e.g., HEAT_ON, COOL_OFF).
Project Goal

The primary goal is to provide a Python-based application that continuously monitors ambient conditions and automatically adjusts climate control based on a time-of-day schedule defined in schedule.py.

Project File Structure
File Name		Purpose
thermostat_control.py	Main Application Logic. Contains the primary run_thermostat_cycle() loop, reads settings, checks the schedule, fetches sensor data, applies control logic, and determines the necessary HVAC action.
schedule.py		Defines the daily temperature/mode schedule (time, target temperature, and mode).
settings.json		Stores the current operational state and configuration (e.g., current_mode, hysteresis, timezone).
data_collector.py	A wrapper script that calls sensor_reading.py and outputs the resulting sensor data as a JSON string to standard output (used for inter-process communication).
sensor_reading.py	Hardware Interaction. Handles initialization of the I2C bus, the TCA9548A multiplexer, and the HDC302x sensor to read the current temperature and humidity.

Prerequisites & Setup
1. Hardware Requirements

    Raspberry Pi: Raspberry Pi Zero 2 W (or any other Raspberry Pi model).

    Sensor: HDC302x Temperature/Humidity Sensor.

    I2C Multiplexer: TCA9548A (used in sensor_reading.py to communicate with the sensor on channel 0).

    HVAC Interface: (To be added) A relay board or similar device connected to the Pi's GPIO pins to physically control the HEATING and COOLING systems.

2. Software Dependencies

This project requires specific Python libraries, particularly for I2C communication and timezone handling.

    Install Required Libraries:
    
    # Ensure pip is up to date
    sudo pip3 install --break-system-packages --upgrade pip
    
    Install Adafruit Blinka (the CircuitPython compatibility layer), Specific CircuitPython libraries for I2C, timezone handling library
    sudo pip3 install --break-system-packages adafruit-blinka adafruit-circuitpython-tca9548a adafruit-circuitpython-hdc302x pytz

Enable I2C: Ensure the I2C interface is enabled on your Raspberry Pi.
Bash

    sudo raspi-config

    Navigate to 3 Interface Options → I5 I2C → Yes.

Configuring the files for your RPi.

    Update this setting within settings.json to the name of you raspberry pi
    "project_path": "/home/your_username/Thermostat"

    Update the systemd service file (thermostat.service) to the name of you raspberry pi as well.
    # IMPORTANT: Change 'YOUR_USERNAME' to your actual Raspberry Pi username if different
    User=YOUR_USERNAME
    # IMPORTANT: Change this to the absolute path of your project directory
    WorkingDirectory=/home/YOUR_USERNAME/Thermostat 

Running the Thermostat

The core of the system is thermostat_control.py, which is designed to be run continuously.
1. Manually Starting the Control Loop

The thermostat_control.py script is set up with an infinite loop and a 30-second sleep (time.sleep(30)) to cycle continuously.
Bash

# Navigate to your project directory
cd /path/to/Thermostat

# Run the main control script
python3 thermostat_control.py

2. Customizing the Schedule

Edit the THERMOSTAT_SCHEDULE list in the schedule.py file. The control logic will automatically apply the setting corresponding to the last time entry that has passed.
Key		Description					Example
time		24-hour time to activate the setting.		'14:00' (2 PM)
target_f	Desired Fahrenheit temperature setpoint.	68.0
mode		System control mode.				'OFF', 'HEAT', 'COOL', 'FAN'

Current Default Schedule (from schedule.py):

THERMOSTAT_SCHEDULE = [
    {'time': '06:00', 'target_f': 72.0, 'mode': 'HEAT'},
    {'time': '08:00', 'target_f': 65.0, 'mode': 'OFF'},
    {'time': '17:00', 'target_f': 70.0, 'mode': 'COOL'},
    {'time': '22:00', 'target_f': 68.0, 'mode': 'COOL'},
]

3. Customizing Initial Settings

You can change the operational parameters in settings.json.

    hysteresis: The temperature band (in °F) around the target temperature used to prevent rapid cycling (short cycling).

        HEAT ON is triggered at Target - Hysteresis.

        COOL ON is triggered at Target + Hysteresis.

    timezone: Critical for correct schedule timing. Set this to your local timezone (e.g., "America/New_York").

Current Default Settings (from settings.json):
JSON

{
    "current_mode": "HEAT",
    "manual_target_f": 72.0,
    "hysteresis": 1.5,
    "timezone": "America/Chicago",
    "last_check_time": "2025-12-02T06:47:20.535415"
}

## System Service & Automation

To ensure the thermostat runs continuously and restarts automatically if the Raspberry Pi reboots or the script crashes, we use a **systemd service**. The service file is included in this repository (`thermostat.service`).

### 1. Symlink the Service File

Instead of copying the file, create a symbolic link from this repository to the systemd directory. This allows you to update the service configuration by simply editing the file in this folder.

**Note:** Ensure the paths inside `thermostat.service` (specifically `WorkingDirectory` and `ExecStart`) match your actual installation path before linking.

# Link the file to /etc/systemd/system/
# Syntax: sudo ln -s [ABSOLUTE_PATH_TO_REPO_FILE] [DESTINATION]
sudo ln -s /home/landon/Thermostat/thermostat.service /etc/systemd/system/thermostat.service
