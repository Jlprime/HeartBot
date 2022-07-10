import json

with open("../pipeline/output/volunteer_gov_sg_data.json", encoding="utf-8") as json_file1:
    json_object1 = json.load(json_file1)

with open("export.json", encoding="utf-8") as json_file2:
    json_object2 = json.load(json_file2)


def overwrite():
    for i in json_object1['entries']:
        for j in json_object2:
            if i['RedirectionURL'] == j.replace('https://www.volunteer.gov.sg', '', 1):
                i.update(json_object2[j])
                continue
    
    with open('vol_data.json', 'w') as f:
        json.dump(json_object1, f)
    return

overwrite()