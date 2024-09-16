import json

def load_query(json_file):
    with open(json_file, 'r') as file:
        queries = json.load(file)
    return queries