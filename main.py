import time
import csv
from purpleair import PurpleAir
from datetime import datetime, timedelta
import json
import os

def load_config():
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            return config
    except FileNotFoundError:
        print("Error: config.json file not found.")
        return None

def minutes_to_label(average_minutes):
    if average_minutes == 10080:
        return "1week"
    elif average_minutes == 1440:
        return "1day"
    else:
        return f"{average_minutes}min"

def create_folder(start_date, end_date):
    # Create a folder with the start and end date in 'yyyy-mm-dd' format
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    folder_name = f"PurpleAir_{start_date_str}_{end_date_str}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    return folder_name

def get_sensor_indices_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as sensors_file:
            csv_reader = csv.DictReader(sensors_file)
            return [row["sensor_index"] for row in csv_reader]
    except FileNotFoundError:
        print(f"Error: {file_path} file not found.")
        return []

def validate_date_range(start_date, end_date, average_minutes):
    if average_minutes == 1440 and (end_date - start_date).days > 365:
        return False
    elif average_minutes == 10080 and (end_date - start_date).days <= 21:
        return False
    return True

def get_sensor_data_and_history(sensor_index, average_minutes, start_date, end_date, folder_name, fields, fields_to_extend):
    # Convert fields and fields_to_extend to tuples
    fields = tuple(fields)
    fields_to_extend = tuple(fields_to_extend)

    # Validate date range
    if not validate_date_range(start_date, end_date, average_minutes):
        print("Invalid date range. Please ensure the difference is within the specified limits.")
        return

    # Get sensor data including 'longitude' and 'latitude'
    sensor_data = p.get_sensor_data(sensor_index=sensor_index, fields=fields_to_extend)
    print(sensor_data)

    # Get sensor history for the specified time range
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    sensor_history = p.get_sensor_history(
        sensor_index=sensor_index,
        average=average_minutes,
        fields=fields,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )
    print(sensor_history)

    # Add 'latitude' and 'longitude' to fields list in the result dictionary
    sensor_history['fields'].extend(list(fields_to_extend))

    # Add 'latitude' and 'longitude' to each element in sensor history data
    for data_point in sensor_history['data']:
        data_point.extend([sensor_data['sensor']['latitude'], sensor_data['sensor']['longitude']])

    # Sort the array by timestamp
    sensor_history['data'] = sorted(sensor_history['data'], key=lambda x: x[0])

    # Change timestamp format to 'yyyy-mm-dd hh:mm:ss'
    for data_point in sensor_history['data']:
        data_point[0] = datetime.utcfromtimestamp(data_point[0]).strftime('%Y-%m-%d %H:%M:%S')

    # Create and save CSV file inside the specified folder
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    label = minutes_to_label(average_minutes)
    csv_filename = f"{sensor_index}_{label}_{start_date_str}_{end_date_str}.csv"
    if not sensor_history['data']:
        csv_filename = f"{sensor_index}_{label}_{start_date_str}_{end_date_str}_empty.csv"
    csv_filepath = os.path.join(folder_name, csv_filename)

    with open(csv_filepath, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(sensor_history['fields'])
        csv_writer.writerows(sensor_history['data'])

if __name__ == "__main__":
    # Load API key and average_minutes from config.json
    config = load_config()
    if not config:
        exit()

    api_key = config.get("api_key")
    average_minutes = config.get("average_minutes", 1440)
    fields = config.get("fields", ['humidity', 'temperature', 'pressure', 'voc', 'pm1.0_atm', 'pm2.5_atm', 'pm10.0_atm'])
    fields_to_extend = config.get("fields_to_extend", ['longitude', 'latitude'])

    # Initialize PurpleAir object with API key
    p = PurpleAir(api_key)

    # Get sensor indices from sensors.csv
    sensor_indices = get_sensor_indices_from_file("sensors.csv")

  

    # Input start date and end date from command line
    while True:
        try:
            start_date_str = input("Enter the start date (yyyy-mm-dd): ")
            end_date_str = input("Enter the end date (yyyy-mm-dd): ")
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if validate_date_range(start_date, end_date, average_minutes):
                break
            else:
                print("Invalid date range. Please ensure the difference is within the specified limits.")
        except ValueError:
            print("Invalid date format. Please use yyyy-mm-dd.")
    # Create a folder with the current date
    folder_name = create_folder(start_date, end_date)
    # Process each sensor index
    for sensor_index in sensor_indices:
        time.sleep(1)

        get_sensor_data_and_history(sensor_index, average_minutes, start_date, end_date, folder_name, fields, fields_to_extend)
