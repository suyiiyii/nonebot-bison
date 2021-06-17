from pathlib import Path
import json
path = Path(__file__).parent
def get_json(file_name: str):
    with open(path / file_name, 'r') as f:
        file_text = f.read() 
        return json.loads(file_text)

def get_file(file_name:str):
    with open(path / file_name, 'r') as f:
        file_text = f.read() 
        return file_text
