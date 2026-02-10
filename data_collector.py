from sensor_reading import get_sensor_data
import json

def collect_and_print_data():
    """Retrieves sensor data and prints it as a JSON string."""
    data = get_sensor_data()
    print(json.dumps(data))

if __name__ == "__main__":
    collect_and_print_data()
