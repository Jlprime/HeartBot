from sqlalchemy import create_engine, insert, text
import json
from datetime import datetime

engine = create_engine('sqlite:///scraped_data.db')

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
            EVENTDATE = "\'" + str(convert_datetime(i[PLATFORM[3]], data['source'])) + "\'"
            if PLATFORM[4] != 'None':
                VACANCIES = i[PLATFORM[4]]
            else:
                VACANCIES = 0
            SIGNUPLINK = "\'" + convert_link(i[PLATFORM[5]], data['source']) + "\'"
            if PLATFORM[6] != 'None':
                SUITABILITY = "\'" + i[PLATFORM[6]] + "\'"
            else:
                SUITABILITY = "\'None\'"

            COMMAND=f'''INSERT INTO VolunteerOpportunities(Portal, EventName, Organizer, EventLocation, EventDate, Vacancies, SignupLink, Suitability)
                        VALUES({PORTAL},{EVENTNAME},{ORGANIZER},{EVENTLOCATION},{EVENTDATE},{VACANCIES},{SIGNUPLINK},{SUITABILITY})'''

            connection.execute(COMMAND)

def convert_datetime(val, source):
    if source == 'giving-sg':
        result = int(datetime.strptime(val, '%a, %d %b %Y').timestamp())
        return result
    else:
        number_list = [s for s in val if s.isdigit()]
        result = int(''.join(number_list)) // 1000
        return result

def convert_link(val, source):
    if source == 'giving-sg':
        return "https://www.giving.sg" + val
    else:
        return "https://www.volunteer.gov.sg/" + val

append_db('test_giving.json')