import json
import subprocess
from datetime import datetime, time
from schedule import THERMOSTAT_SCHEDULE
import time
import pytz 

# --- Configuration ---
SETTINGS_FILE = 'settings.json'
DATA_COLLECTOR_SCRIPT = './data_collector.py' # Relative path to the collector script

# --- Helper Functions ---

def get_current_setpoint(schedule, default_target, timezone_name):
    """
    Determines the target temperature based on the time and the schedule.
    It returns the setting that is currently active.
    """
    try:
        # 1. Get the current time in the specified timezone
        tz = pytz.timezone(timezone_name)
        current_time = datetime.now(tz).time() # Use timezone aware time for comparison
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"ERROR: Unknown timezone '{timezone_name}'. Using system time.")
        current_time = datetime.now().time()
        
    # Sort the schedule by time to ensure we check them in order
    sorted_schedule = sorted(schedule, key=lambda x: datetime.strptime(x['time'], '%H:%M').time())
    
    # 2. FIX: Initialize active_setting with the last event of the entire schedule.
    # This correctly handles the time period between the last event (e.g., 22:00) 
    # and the first event of the next day (e.g., 06:00).
    if sorted_schedule:
        active_setting = {
            'target_f': sorted_schedule[-1]['target_f'],
            'mode': sorted_schedule[-1]['mode']
        }
    else:
        # Fallback to manual default if schedule is empty
        active_setting = {'target_f': default_target, 'mode': 'OFF'} 
    
    # 3. Loop through the schedule. If current_time has passed a set_time today,
    # the active_setting will be overwritten.
    for entry in sorted_schedule:
        set_time = datetime.strptime(entry['time'], '%H:%M').time()
        
        # Compare time objects
        if current_time >= set_time:
            # Update the setting as this event has occurred today
            active_setting['target_f'] = entry['target_f']
            active_setting['mode'] = entry['mode']
        else:
            # Since the list is sorted, we can stop checking once we hit a future time
            break
            
    return active_setting


def read_settings():
    """Reads the current configuration and hysteresis from the JSON file."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {SETTINGS_FILE} not found. Please create it first.")
        # Return sensible defaults if file is missing
        return {
            "current_mode": "HEAT",
            "manual_target_f": 72.0,
            "hysteresis": 1.5,
            "timezone": "UTC",
            "last_check_time": datetime.now().isoformat()
        }
    except json.JSONDecodeError:
        print(f"Error: Could not parse {SETTINGS_FILE}. Check JSON format.")
        return None

def write_settings(settings):
    """Writes the updated configuration back to the JSON file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def fetch_sensor_data():
    """Runs the data_collector script and parses its JSON output."""
    try:
        # Execute the collector script and capture its standard output
        result = subprocess.run(
            ['python3', DATA_COLLECTOR_SCRIPT], 
            capture_output=True, 
            text=True, 
            check=True
        )
        # The output of data_collector.py is a JSON string
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        # Include stderr output for debugging
        print(f"Error running data collector: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print("Error: Collector script returned invalid JSON.")
        return None

# --- Main Logic ---

def run_thermostat_cycle():
    """Performs one cycle of reading sensors, applying logic, and making a decision."""
    
    # 1. READ SETTINGS
    current_settings = read_settings()
    if not current_settings:
        return
        
    # --- GET TIMEZONE AWARE CURRENT TIME FOR LOGGING ---
    timezone = current_settings.get('timezone', 'UTC')
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"ERROR: Unknown timezone '{timezone}'. Using system time (naive).")
        tz = None

    # Calculate the localized current time
    if tz:
        current_localized_time = datetime.now(tz)
    else:
        current_localized_time = datetime.now()
        
    # Print the cycle start time using the localized time object
    print(f"--- Thermostat Cycle Started at {current_localized_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ---")
    
    
    hysteresis = current_settings['hysteresis']
    
    # Use timezone in setpoint function
    schedule_setting = get_current_setpoint(
        THERMOSTAT_SCHEDULE, 
        current_settings['manual_target_f'],
        timezone 
    )
    
    target_f = schedule_setting['target_f']
    mode = schedule_setting['mode']
    
    print(f"- Timezone: {timezone}")
    print(f"- Schedule Target: {target_f:.1f}°F, Mode: {mode}")
    
    # 2. READ SENSORS
    sensor_data = fetch_sensor_data()
    if not sensor_data or sensor_data.get('status') == 'ERROR' or sensor_data['temperature_f'] is None:
        print("CRITICAL: Failed to get valid sensor data. Aborting cycle.")
        return

    current_temp = sensor_data['temperature_f']
    current_humidity = sensor_data['humidity_percent']
    
    print(f"- Current Reading: {current_temp:.1f}°F, {current_humidity:.1f}% RH")
    
    # 3. CONTROL LOGIC
    # Determine the required action based on mode, temperature, and hysteresis
    action = "NO_CHANGE"
    
    if mode == 'HEAT':
        # Heat ON if current temp is below target minus hysteresis (deadband)
        heat_on_temp = target_f - hysteresis
        
        if current_temp < heat_on_temp:
            action = "HEAT_ON"
        elif current_temp >= target_f:
            action = "HEAT_OFF"
            
        print(f"- Heat ON threshold: < {heat_on_temp:.1f}°F")
        
    elif mode == 'COOL':
        # Cool ON if current temp is above target plus hysteresis
        cool_on_temp = target_f + hysteresis
        
        if current_temp > cool_on_temp:
            action = "COOL_ON"
        elif current_temp <= target_f:
            action = "COOL_OFF"
            
        print(f"- Cool ON threshold: > {cool_on_temp:.1f}°F")
            
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
    
    # To run continuously every 5 seconds
    while True:
        run_thermostat_cycle()
        print(f"Waiting 5 seconds before next cycle...")
        time.sleep(30)
