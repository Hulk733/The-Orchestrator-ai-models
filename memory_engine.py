import os, json

MEMORY_DIR = "core/memory"

def store_context(agent, data):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    file_path = f"{MEMORY_DIR}/{agent}.json"
    memory_log = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            memory_log = json.load(f)
    memory_log.append({"input": data})
    with open(file_path, "w") as f:
        json.dump(memory_log, f, indent=2)
    return memory_log

def recall_context(agent):
    file_path = f"{MEMORY_DIR}/{agent}.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []
