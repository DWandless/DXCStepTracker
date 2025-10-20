def load_data(file_path):
    import pandas as pd
    
    # Load data from a CSV file
    data = pd.read_csv(file_path)
    return data

def load_json(file_path):
    import json
    
    # Load data from a JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def load_data_from_api(api_url):
    import requests
    
    # Load data from an API
    response = requests.get(api_url)
    data = response.json()
    return data