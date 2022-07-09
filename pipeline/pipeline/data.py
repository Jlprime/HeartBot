import json

def save_json(filename, data):
  with open(f"/srv/output/{filename}", "w") as f:
    json.dump(data, f)

def load_json(filename):
  with open(f"/srv/output/{filename}", "r") as f:
    return json.load(f)