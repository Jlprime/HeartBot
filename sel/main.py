#!/usr/bin/env python3

print("Scraper starting...")

from time import sleep
import json

from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.common.exceptions import ElementClickInterceptedException

_original_print = print
def eager_print(*args, **kwargs):
  _original_print(*args, **kwargs, flush=True)
print = eager_print

driver = None
def setup():
  global driver
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--disable-gpu')
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument("--window-size=1920,1080")
  driver = webdriver.Chrome(options=chrome_options)
  driver.implicitly_wait(5)

def scrape_url(url):
  print(f"Scraping {url}")
  driver.get(url)
  sleep(3)
  body = driver.find_element_by_xpath('/html')
  code = body.get_attribute('outerHTML')
  return code

def giving_sg_index(pages=2):
  print("Scraping giving.sg")
  driver.get("https://www.giving.sg/search?type=volunteer")
  sleep(2)
  last_height = 0
  for i in range(pages - 1):
    print(f"Next page {i + 2}")
    height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(2)
    if height - last_height < 100:
      break
    last_height = height

  all_entries = []
  for request in driver.requests:
    if not request.response:
      continue
    if not request.url.startswith("https://www.giving.sg/search?") or not request.response.headers.get('Content-Type', "").startswith("application/json"):
      continue

    print(
      request.url,
      request.response.status_code
    )
    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
    json_data = json.loads(body)
    entries = json_data['resultList']
    all_entries.extend(entries)

  res = {
    "source": "giving-sg",
    "pages": pages,
    "entries": all_entries
  }
  # print(json.dumps(res))
  return res

def volunteer_gov_sg_index(pages=2):
  print("Scraping volunteer.gov.sg")
  driver.get("https://www.volunteer.gov.sg/")
  sleep(3)
  driver.find_element_by_css_selector('a#showListView').click()
  sleep(3)
  for i in range(pages-1):
    print(f"Next page {i + 2}")
    try:
      driver.find_element_by_css_selector('#gridFindoppo .k-grid-pager a[title="Go to the next page"]').click()
      sleep(3)
    except ElementClickInterceptedException as e:
      break

  all_entries = []
  for request in driver.requests:
    if not request.response:
      continue
    if not request.url.startswith("https://www.volunteer.gov.sg/opportunities/listlistviewoppotunity/") or not request.response.headers.get('Content-Type', "").startswith("application/json"):
      continue

    print(
      request.url,
      request.response.status_code
    )
    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
    json_data = json.loads(body)
    entries = json_data['Data']
    all_entries.extend(entries)

  res = {
    "source": "volunteer-gov-sg",
    "pages": pages,
    "entries": all_entries
  }
  # print(json.dumps(res))
  return res

def teardown():
  global driver
  driver.quit()
  driver = None

setup()

# giving_sg_data = giving_sg_index(999)
# with open("/srv/output/giving_sg_data.json", "w") as f:
#   json.dump(giving_sg_data, f)

# volunteer_gov_sg_data = volunteer_gov_sg_index(999)
# with open("/srv/output/volunteer_gov_sg_data.json", "w") as f:
#   json.dump(volunteer_gov_sg_data, f)

with open("/srv/output/volunteer_gov_sg_data.json", "r") as f:
  volunteer_gov_sg_data = json.load(f)

volunter_gov_sg_detail_data = []
for idx, entry in enumerate(volunteer_gov_sg_data['entries'][150:]):
  print(idx)
  url = "https://www.volunteer.gov.sg" + entry['RedirectionURL']
  res = scrape_url(url)
  volunter_gov_sg_detail_data.append({
    "url": url,
    "html": res
  })

with open("/srv/output/volunteer_gov_sg_detail_data_4.json", "w") as f:
  json.dump({
    "source": "volunteer-gov-sg-detail",
    "pages": len(volunter_gov_sg_detail_data),
    "entries": volunter_gov_sg_detail_data
  }, f)

teardown()

print("Scraper done.")