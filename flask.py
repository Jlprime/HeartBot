from typing import List
from sqlalchemy import create_engine, insert, text
import json
from collections.abc import MutableMapping

engine = create_engine('sqlite:///scraped_data.db')


""" @app.route("/", methods=["GET"])
def starting_url():
    json_data = flask.request.json
    a_value = json_data["a_key"]
    return "JSON value sent: " + a_value

app.run(host="0.0.0.0", port=8080) """

GIVING_SG = ['Title','DisplayName','Town','Duration','Openings','VolunteerUrl','Suitabilities']
VOLUNTEER_SG = ['Name', 'AgencyName', 'AddressTooltip','StartDateTime', 'None', 'RedirectionURL', 'None']

def append_db(json_input):
    PLATFORM, PORTAL = '', ''
    with open(json_input, encoding="utf8") as json_file:
        data = json.load(json_file)
        entries = data['entries']

    if data['source'] == 'giving-sg':
        PLATFORM, PORTAL = GIVING_SG, '\'GIVING_SG\''
    else:
        PLATFORM, PORTAL = VOLUNTEER_SG, '\'VOLUNTEER_SG\''

    with engine.connect() as connection:
        for i in entries:
            EVENTNAME = "\'" + i[PLATFORM[0]] + "\'"
            ORGANIZER = "\'" + i[PLATFORM[1]] + "\'"
            EVENTLOCATION = "\'" + i[PLATFORM[2]].split()[-1] + "\'"
            EVENTDATE = "\'" + i[PLATFORM[3]] + "\'"
            if PLATFORM[4] != 'None':
                VACANCIES = i[PLATFORM[4]]
            else:
                VACANCIES = 0
            SIGNUPLINK = "\'" + i[PLATFORM[5]] + "\'"
            if PLATFORM[6] != 'None':
                SUITABILITY = "\'" + i[PLATFORM[6]] + "\'"
            else:
                SUITABILITY = "\'None\'"

            COMMAND=f'''INSERT INTO VolunteerOpportunities(Portal, EventName, Organizer, EventLocation, EventDate, Vacancies, SignupLink, Suitability)
                        VALUES({PORTAL},{EVENTNAME},{ORGANIZER},{EVENTLOCATION},{EVENTDATE},{VACANCIES},{SIGNUPLINK},{SUITABILITY})'''

            connection.execute(COMMAND)

def rem_lis(lis):
    return lis[0]
    

def _flatten_dict_gen(d, parent_key, sep):
    for i, j in d.items():
        new_key = parent_key + sep + i if parent_key else i
        if isinstance(j, MutableMapping):
            yield from flatten_dict(j, new_key, sep=sep).items()
        elif type(j) == list:
            yield new_key, rem_lis(j)
        else:
            yield new_key, j

def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    return dict(_flatten_dict_gen(d, parent_key, sep))


append_db('test.json')