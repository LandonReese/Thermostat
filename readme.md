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

**Option A: Using a Virtual Environment (Recommended)**

    # Navigate to your project directory
    cd /path/to/Thermostat
    
    # Create a virtual environment
    python3 -m venv venv
    
    # Activate the virtual environment
    source venv/bin/activate
    
    # Install required libraries from requirements.txt
    pip install -r requirements.txt

**Option B: System-wide Installation**

    # Ensure pip is up to date
    sudo pip3 install --break-system-packages --upgrade pip
    
    # Install required libraries
    sudo pip3 install --break-system-packages adafruit-blinka adafruit-circuitpython-tca9548a adafruit-circuitpython-hdc302x pytz

**Note:** The systemd service will automatically use the virtual environment if it exists in the project directory. If no venv is found, it will use the system python3.

Enable I2C: Ensure the I2C interface is enabled on your Raspberry Pi.
Bash

    sudo raspi-config

    Navigate to 3 Interface Options → I5 I2C → Yes.

3. Configuring the files for your RPi

After cloning the repository, you need to update a few paths:

    a. Update settings.json:
       Edit the "project_path" setting to match your installation path:
       "project_path": "/home/your_username/Thermostat"

    b. Update thermostat.service:
       Edit the following lines in thermostat.service:
       - User=your_username (change 'landon' to your actual username)
       - WorkingDirectory=/home/your_username/Thermostat (update the path)
       - ExecStart=/home/your_username/Thermostat/start_thermostat.sh (update the path)

    c. Make the startup script executable:
       chmod +x start_thermostat.sh 

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

### 1. Setup and Symlink the Service File

**Important:** Before linking the service file, ensure you have:
1. Updated the paths in `thermostat.service` (User, WorkingDirectory, ExecStart)
2. Made `start_thermostat.sh` executable: `chmod +x start_thermostat.sh`
3. (Optional) Created and activated a virtual environment with dependencies installed

Create a symbolic link from this repository to the systemd directory. This allows you to update the service configuration by simply editing the file in this folder.

    # Link the file to /etc/systemd/system/
    # Syntax: sudo ln -s [ABSOLUTE_PATH_TO_REPO_FILE] [DESTINATION]
    sudo ln -s /home/your_username/Thermostat/thermostat.service /etc/systemd/system/thermostat.service
    
    # Reload systemd to recognize the new service
    sudo systemctl daemon-reload
    
    # Enable the service to start on boot
    sudo systemctl enable thermostat.service
    
    # Start the service
    sudo systemctl start thermostat.service
    
    # Check the status
    sudo systemctl status thermostat.service

**How it works:** The `start_thermostat.sh` wrapper script automatically detects if a virtual environment exists in the project directory. If `venv/bin/python3` is found, it uses that. Otherwise, it falls back to the system `python3`. This means you can use the project with or without a virtual environment - just update the paths in `thermostat.service` and you're ready to go!
