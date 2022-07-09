from sqlalchemy import create_engine, insert, text
from datacleaning import nearest, convert_datetime, convert_link
import json

engine = create_engine('sqlite:///scraped_data.db')

GIVING_SG = ['Title','DisplayName','Town','Duration','Openings','VolunteerUrl','Suitabilities']
VOLUNTEER_SG = ['Name', 'AgencyName', 'Address','StartDateTime', 'None', 'RedirectionURL', 'None']

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
            #print(i[PLATFORM[2]])
            EVENTLOCATION = "\'" + nearest(i[PLATFORM[2]]) + "\'"
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

append_db('test.json')