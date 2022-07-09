import string
import sqlalchemy as db

engine = db.create_engine("sqlite:///scraped_data.db")

def database_init(directory, table_name):
    engine = db.create_engine("sqlite:///scraped_data.db")
    headers = db.Table(table_name, metadata=db.MetaData()).columns.keys()
    return engine, headers

# with engine.connect() as connection:
#     COMMAND = f'SELECT * FROM VolunteerOpportunities WHERE EventDate = "{date}"'
#     resultProxy = connection.execute(COMMAND)
#     resultFetch = resultProxy.fetchall()