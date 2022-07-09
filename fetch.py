import string
import sqlalchemy as db

def database_init(directory, table_name):
    engine = db.create_engine(directory)
    headers = db.Table(table_name, db.MetaData(), autoload=True, autoload_with=engine).columns.keys()
    return engine, headers

def fetch(engine, table_name, header, operator, val, qty='*'):
    with engine.connect() as connection:
        COMMAND = f'SELECT {qty} FROM {table_name} WHERE {header} {operator} {val}'
        resultProxy = connection.execute(COMMAND)
        resultFetch = resultProxy.fetchall()
        return resultFetch