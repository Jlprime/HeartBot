# Care-ggregate

_For the willing volunteer: why download so many apps to search for volunteering opportunities when you can have opportunities sent to you through a service you already have?_

Built with Python, JSON and SQLite

**Preprocessing**
Input of scraped data (pipeline/output folders) into JSON files for later processing. Scraped (raw) data may come from a variety of platforms and sources; for this hackathon, giving.sg and volunteer.gov.sg were used.

A main Care-ggregate channel will then utilize `flask.py` to generate the database required to populate it. The SQLite database `scraped_data.db` will be refreshed with cleaned data, as `flask.py` utilizes functions from `datacleaning.py` to remove data oddities and errors. Cleaned data will be easily accessible by `main.py` later.

**First Initialisation**
When user first activates Care-ggregate, `main.py` will be initialized. The user will be led to subscribe to the announcements channel, through which they may access the main 'stream' of volunteering opportunities. Users will not be able to proceed with further use unless channel has been subscribed to.

Upon subscription, the user will be allowed to use the search function to get the data they required; the functions are found in `main.py`. Currently, users can search based on platform and date range.
