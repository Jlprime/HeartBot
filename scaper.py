from urllib.request import Request,urlopen
import requests, json
from bs4 import BeautifulSoup

with requests.session():
    req = "https://www.giving.sg/search?p_p_id=search_WAR_givingsgportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=search&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1"
    #sess = requests.Session()
    #myObj = {'_search_WAR_givingsgportlet_data':'{"category":["adHoc","regular"],"cause":[],"sortOrder":"Relevance","tdr":[],"opening":[],"suitability":[],"skill":[],"organizationId":[""]}'}
    payload = {
        "_search_WAR_givingsgportlet_data":"{\"category\":[\"adHoc\",\"regular\"],\"cause\":[],\"sortOrder\":\"Relevance\",\"tdr\":[],\"opening\":[],\"suitability\":[],\"skill\":[],\"organizationId\":[\"\"]}",
        "p_auth":"hAg3vL6P", 
        "_search_WAR_givingsgportlet_count":"0",
        "_search_WAR_givingsgportlet_q":""
        }
    payload_json = json.dumps(payload)

    header = {
        "User-Agent":"Mozilla/5.0",
        'X-Requested-With': 'XMLHttpRequest'
        }
    page = requests.post(req, data=payload_json, headers=header)

if page:
    print("2")
else:
    print("no")

print(page.text)

print(page.status_code)
"""soup = BeautifulSoup(page.content, "html.parser")
print(soup.title) """

""" html_bytes = page.read()
html = html_bytes.decode("utf-8")
print("html") """