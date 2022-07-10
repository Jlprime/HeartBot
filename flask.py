from sqlalchemy import create_engine, insert, text
from datacleaning import nearest, convert_datetime, convert_link
import json

engine = create_engine('sqlite:///scraped_data.db')

GIVING_SG = ['Title','DisplayName','Town','Duration','Openings','VolunteerUrl','Suitabilities', 'Url']
VOLUNTEER_SG = ['Name', 'AgencyName', 'Location Postal','StartDateTime', 'Available Slots', 'RedirectionURL', 'None', 'OpportunityImage']

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
            try:
                EVENTNAME = "\'" + i[PLATFORM[0]] + "\'"
                ORGANIZER = "\'" + i[PLATFORM[1]] + "\'"
                #print(i[PLATFORM[2]])
                EVENTLOCATION = "\'" + nearest(i[PLATFORM[2]]) + "\'"
                EVENTDATE = "\'" + str(convert_datetime(i[PLATFORM[3]], data['source'])) + "\'"
                VACANCIES = i[PLATFORM[4]]
                SIGNUPLINK = "\'" + convert_link(i[PLATFORM[5]], data['source'], False) + "\'"
                if PLATFORM[6] != 'None':
                    SUITABILITY = "\'" + i[PLATFORM[6]] + "\'"
                else:
                    SUITABILITY = "\'None\'"
                IMGLINK = "\'" + convert_link(i[PLATFORM[7]], data['source'], True) + "\'"
            except:
                continue

            COMMAND=f'''INSERT INTO VolunteerOpportunities(Portal, EventName, Organizer, EventLocation, EventDate, Vacancies, SignupLink, Suitability, ImageURL)
                        VALUES({PORTAL},{EVENTNAME},{ORGANIZER},{EVENTLOCATION},{EVENTDATE},{VACANCIES},{SIGNUPLINK},{SUITABILITY},{IMGLINK})'''

            connection.execute(COMMAND)

append_db('vol_data.json')