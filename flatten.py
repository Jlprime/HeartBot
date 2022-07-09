def flatten(obj, path=tuple(), target=None):
    if target is None:
        target = {}

    if isinstance(obj, list):
        for idx, x in enumerate(obj):
            flatten(x, (*path, idx), target)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, (*path, k), target)
    else:
        target[path] = obj
    return target

import json
with open("test.json", "rb") as f:
    data = json.loads(f.read().decode())
print(flatten(data))
