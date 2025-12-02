# sensor_reading.py
import board
import busio
import adafruit_tca9548a
import adafruit_hdc302x
import datetime

# Configuration
HDC_CHANNEL = 0


def get_sensor_data():
    """Reads temperature and humidity from the HDC3022 sensor."""
    try:
        # 1. Initialize I2C bus and Multiplexer
        i2c = busio.I2C(board.SCL, board.SDA)
        tca = adafruit_tca9548a.TCA9548A(i2c)
        
        # 2. Initialize HDC3022 on the specified channel
        hdc = adafruit_hdc302x.HDC302x(tca[HDC_CHANNEL])

        # 3. Read raw data
        temperature_c = hdc.temperature
        humidity_percent = hdc.relative_humidity

        # 4. Process data
        temperature_f = (temperature_c * 9/5) + 32
        timestamp = datetime.datetime.now().isoformat()

        # 5. Return data as a dictionary
        return {
            'timestamp': timestamp,
            'temperature_f': round(temperature_f, 2),
            'humidity_percent': round(humidity_percent, 2),
            'status': 'OK'
        }

    except Exception as e:
        print(f"Error reading sensor data: {e}")
        # Return a dictionary with error status
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'temperature_f': None,
            'humidity_percent': None,
            'status': 'ERROR',
            'error_message': str(e)
        }


if __name__ == "__main__":
    # Example usage when running the script directly
    data = get_sensor_data()
    print("--- Current Sensor Snapshot ---")
    print(f"Timestamp: {data['timestamp']}")
    print(f"Temperature: {data['temperature_f']} °F")
    print(f"Humidity: {data['humidity_percent']} %")
    print(f"Status: {data['status']}")
