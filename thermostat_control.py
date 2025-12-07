import json
import subprocess
from datetime import datetime, time
from schedule import THERMOSTAT_SCHEDULE
import time
import pytz 
import os 

# --- Configuration Constants ---
# Used as fallback if settings.json is missing or lacks the 'project_path'
PROJECT_PATH_DEFAULT = '/home/landon/Thermostat'
SETTINGS_FILE_NAME = 'settings.json'
DATA_COLLECTOR_SCRIPT_NAME = 'data_collector.py'

# --- Helper Functions ---

def get_current_setpoint(schedule, default_target, timezone_name):
    """
    Determines the target temperature and mode based on the current time and the schedule.
    """
    try:
        tz = pytz.timezone(timezone_name)
        current_time = datetime.now(tz).time() 
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"ERROR: Unknown timezone '{timezone_name}'. Using system time.")
        current_time = datetime.now().time()
        
    sorted_schedule = sorted(schedule, key=lambda x: datetime.strptime(x['time'], '%H:%M').time())
    
    # Initialize active_setting with the last event to cover the period until the first event of the next day.
    if sorted_schedule:
        active_setting = {
            'target_f': sorted_schedule[-1]['target_f'],
            'mode': sorted_schedule[-1]['mode']
        }
    else:
        # Fallback to manual default if schedule is empty
        active_setting = {'target_f': default_target, 'mode': 'OFF'} 
    
    # Loop through the schedule to find the latest time entry that has passed today
    for entry in sorted_schedule:
        set_time = datetime.strptime(entry['time'], '%H:%M').time()
        
        if current_time >= set_time:
            active_setting['target_f'] = entry['target_f']
            active_setting['mode'] = entry['mode']
        else:
            # Since the list is sorted, we can stop checking once we hit a future time
            break
            
    return active_setting


def read_settings():
    """Reads configuration from settings.json and dynamically constructs file paths."""
    try:
        settings_file_path = os.path.join(os.path.dirname(__file__), SETTINGS_FILE_NAME)
        with open(settings_file_path, 'r') as f:
            settings = json.load(f)

        # Use 'project_path' from settings or fall back to default
        project_path = settings.get('project_path', PROJECT_PATH_DEFAULT)
        
        # Store absolute paths in the dictionary for use in other functions
        settings['SETTINGS_FILE'] = settings_file_path
        settings['DATA_COLLECTOR_SCRIPT'] = os.path.join(project_path, DATA_COLLECTOR_SCRIPT_NAME)

        return settings
    except FileNotFoundError:
        print(f"Error: Could not find '{SETTINGS_FILE_NAME}' in script directory.")
        # Return sensible defaults if file is missing
        return {
            "current_mode": "HEAT",
            "manual_target_f": 72.0,
            "hysteresis": 1.5,
            "timezone": "UTC",
            "last_check_time": datetime.now().isoformat(),
            "project_path": PROJECT_PATH_DEFAULT,
            "SETTINGS_FILE": os.path.join(PROJECT_PATH_DEFAULT, SETTINGS_FILE_NAME),
            "DATA_COLLECTOR_SCRIPT": os.path.join(PROJECT_PATH_DEFAULT, DATA_COLLECTOR_SCRIPT_NAME)
        }
    except json.JSONDecodeError:
        print(f"Error: Could not parse {SETTINGS_FILE_NAME}. Check JSON format.")
        return None

def write_settings(settings):
    """Writes the updated configuration back to the JSON file."""
    settings_file_path = settings['SETTINGS_FILE'] 
    
    # Remove the dynamically added path keys before writing back to the simplified settings.json
    settings_to_write = {k: v for k, v in settings.items() if k not in ['SETTINGS_FILE', 'DATA_COLLECTOR_SCRIPT']}
    
    with open(settings_file_path, 'w') as f:
        json.dump(settings_to_write, f, indent=4)

def fetch_sensor_data(data_collector_script_path):
    """Runs the data_collector script and parses its JSON output."""
    try:
        # Execute the collector script and capture its standard output
        result = subprocess.run(
            ['python3', data_collector_script_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        # The output of data_collector.py is a JSON string
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running data collector: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print("Error: Collector script returned invalid JSON.")
        return None

# --- Main Logic ---

def run_thermostat_cycle():
    """Performs one cycle of reading sensors, applying logic, and making a decision."""
    
    # 1. READ SETTINGS & DETERMINE TARGET
    current_settings = read_settings()
    if not current_settings:
        return
        
    timezone = current_settings.get('timezone', 'UTC')
    try:
        tz = pytz.timezone(timezone)
        current_localized_time = datetime.now(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"ERROR: Unknown timezone '{timezone}'. Using system time (naive).")
        current_localized_time = datetime.now()
        
    print(f"--- Thermostat Cycle Started at {current_localized_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ---")
    
    hysteresis = current_settings['hysteresis']
    
    schedule_setting = get_current_setpoint(
        THERMOSTAT_SCHEDULE, 
        current_settings['manual_target_f'],
        timezone 
    )
    
    target_f = schedule_setting['target_f']
    mode = schedule_setting['mode']
    
    print(f"- Schedule Target: {target_f:.1f}°F, Mode: {mode}")
    
    # 2. READ SENSORS
    sensor_data = fetch_sensor_data(current_settings['DATA_COLLECTOR_SCRIPT'])
    if not sensor_data or sensor_data.get('status') == 'ERROR' or sensor_data['temperature_f'] is None:
        print("CRITICAL: Failed to get valid sensor data. Aborting cycle.")
        return

    current_temp = sensor_data['temperature_f']
    current_humidity = sensor_data['humidity_percent']
    
    print(f"- Current Reading: {current_temp:.1f}°F, {current_humidity:.1f}% RH")
    
    # 3. CONTROL LOGIC
    action = "NO_CHANGE"
    
    if mode == 'HEAT':
        heat_on_temp = target_f - hysteresis
        
        if current_temp < heat_on_temp:
            action = "HEAT_ON"
        elif current_temp >= target_f:
            action = "HEAT_OFF"
            
    elif mode == 'COOL':
        cool_on_temp = target_f + hysteresis
        
        if current_temp > cool_on_temp:
            action = "COOL_ON"
        elif current_temp <= target_f:
            action = "COOL_OFF"
            
    elif mode == 'FAN':
        action = "FAN_ON" 
        
    elif mode == 'OFF':
        action = "SYSTEM_OFF"
        
    # 4. EXECUTE ACTION
    print(f"\n- DECISION: {action}")
    
    # NOTE: This is where you would call a function to control GPIO pins
    
    # 5. UPDATE SETTINGS (to log the last check time)
    current_settings['last_check_time'] = datetime.now().isoformat()
    write_settings(current_settings)
    print("--- Cycle Complete ---")


if __name__ == "__main__":
    
    # Run continuously every 30 seconds
    while True:
        run_thermostat_cycle()
        time.sleep(30)
