import json

# Shared file (CISC5597) that will be replicated on all nodes
file_name = 'CISC5597.json'

# Initial file content
file_content = {"value": None}

# Function to write the value to file
def write_to_file(value):
    with open(file_name, 'w') as f:
        json.dump({"value": value}, f)

# Function to read the value from file
def read_from_file():
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
            return data.get('value', None)
    except FileNotFoundError:
        return None
