# schedule.py

# --- Thermostat Schedule ---
# Define a schedule of setpoints based on the time of day and day of the week.
# This simple schedule repeats daily. You can expand this to include 
# 'day_of_week' (0=Monday, 6=Sunday) for more complex weekly logic.

# Settings:
# 'time': The time to activate the setting (24-hour format, HH:MM).
# 'target_f': The desired temperature setpoint in Fahrenheit.
# 'mode': The system mode ('HEAT', 'COOL', 'FAN', 'OFF').

THERMOSTAT_SCHEDULE = [
    {
        'time': '06:00',      # 6:00 AM (Wake Up)
        'target_f': 72.0,
        'mode': 'HEAT'
    },
    {
        'time': '08:00',      # 8:00 AM (Leave for work/day setting)
        'target_f': 65.0,
        'mode': 'OFF'
    },
    {
        'time': '17:00',      # 5:00 PM (Arrive Home)
        'target_f': 70.0,
        'mode': 'COOL'
    },
    {
        'time': '22:00',      # 10:00 PM (Bedtime)
        'target_f': 68.0,
        'mode': 'COOL'
    },
    # Example for cooling mode (seasonal change)
    # {
    #     'time': '06:00',
    #     'target_f': 76.0,
    #     'mode': 'COOL'
    # }
]
