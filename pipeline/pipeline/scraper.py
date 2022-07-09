from asyncio import wait_for
from time import sleep
import json

from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gc

from timeout import timeout, TimeoutError

from data import load_json, save_json

_original_print = print
def eager_print(*args, **kwargs):
  _original_print(*args, **kwargs, flush=True)
print = eager_print

driver = None
def setup_driver():
  global driver
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--disable-gpu')
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument("--window-size=1920,1080")
  driver = webdriver.Chrome(options=chrome_options)
  driver.implicitly_wait(10)

def teardown_driver():
  global driver
  driver.quit()
  gc.collect()
  driver = None

def scrape_html(url, wait=2.5, retry=3, wait_for_selector=None):
  print(f"Scraping {url}")

  @timeout(seconds=wait)
  def inner():
    driver.get(url)
    if wait_for_selector:
      WebDriverWait(driver, 10).until(EC.visibility_of(driver.find_element_by_css_selector(wait_for_selector)))
    return driver.find_element_by_xpath('/html').get_attribute('outerHTML')

  html = None
  for i in range(retry):
    try:
      html = inner()
      sleep(wait)
    except TimeoutError as e:
      if i < retry - 1:
        print("Timeout, retrying...")
      else:
        print("Timeout, skipping")
        print("Reloading driver")
        teardown_driver()
        setup_driver()
  
  return {
    "url": url,
    "html": html
  }

def scrape_many_html(urls, wait=2.5, wait_for_selector=None):
  ress = []
  for url in urls:
    res = scrape_html(url, wait, wait_for_selector=wait_for_selector)
    ress.append(res)
  return ress

def scrape_giving_sg_index(pages=3, wait=2.5):
  print("Scraping giving.sg index")
  print(f"Page 1/{pages}")
  driver.get("https://www.giving.sg/search?type=volunteer")
  sleep(wait)

  fetched_pages = 1
  last_height = 0
  for i in range(pages - 1):
    print(f"Page {i + 2}/{pages}")
    height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    fetched_pages += 1
    sleep(wait)
    if height - last_height < 100:
      print("Reached end of pages")
      break
    last_height = height

  all_entries = []
  for request in driver.requests:
    if not request.response:
      continue
    if not request.url.startswith("https://www.giving.sg/search?") or not request.response.headers.get('Content-Type', "").startswith("application/json"):
      continue

    print(
      "Scraped",
      request.url,
      request.response.status_code
    )
    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
    json_data = json.loads(body)
    entries = json_data['resultList']
    all_entries.extend(entries)

  res = {
    "source": "giving-sg",
    "pages": fetched_pages,
    "entries": all_entries
  }

  return res

def scrape_volunteer_gov_sg_index(pages=3, wait=2.5):
  print("Scraping volunteer.gov.sg index")
  print(f"Page 1/{pages}")
  driver.get("https://www.volunteer.gov.sg/")
  sleep(wait)
  driver.find_element_by_css_selector('a#showListView').click()
  sleep(wait)

  fetched_pages = 1
  for i in range(pages-1):
    print(f"Page {i + 2}/{pages}")
    try:
      driver.find_element_by_css_selector('#gridFindoppo .k-grid-pager a[title="Go to the next page"]').click()
      fetched_pages += 1
      sleep(3)
    except ElementClickInterceptedException as e:
      print("Reached end of pages")
      break

  all_entries = []
  for request in driver.requests:
    if not request.response:
      continue
    if not request.url.startswith("https://www.volunteer.gov.sg/opportunities/listlistviewoppotunity/") or not request.response.headers.get('Content-Type', "").startswith("application/json"):
      continue

    print(
      "Scraped",
      request.url,
      request.response.status_code
    )
    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
    json_data = json.loads(body)
    entries = json_data['Data']
    all_entries.extend(entries)

  res = {
    "source": "volunteer-gov-sg",
    "pages": fetched_pages,
    "entries": all_entries
  }

  return res

def scrape_volunteer_gov_sg_details(opportunity_ids):
  urls = [
    "https://www.volunteer.gov.sg/volunteer/opportunity/details/?id=" + opportunity_id
    for opportunity_id in opportunity_ids
  ]
  return {
    "source": "volunteer-gov-sg:details",
    "pages": len(urls),
    "entries": scrape_many_html(urls, wait=5, wait_for_selector="#oppoRoleDetails")
  }

def main():
  print("Starting scraper")

  setup_driver()
  giving_sg_index = scrape_giving_sg_index(999)
  save_json("giving_sg_index.json", giving_sg_index)
  volunteer_gov_sg_index = scrape_volunteer_gov_sg_index(999)
  save_json("volunteer_gov_sg_index.json", volunteer_gov_sg_index)
  teardown_driver()

  giving_sg_index = load_json("giving_sg_index.json")
  volunteer_gov_sg_index = load_json("volunteer_gov_sg_index.json")

  setup_driver()
  volunteer_gov_sg_opportunity_ids = [
    i["OpportunityID"]
    for i in volunteer_gov_sg_index["entries"]
  ]
  volunteer_gov_sg_details = scrape_volunteer_gov_sg_details(volunteer_gov_sg_opportunity_ids)
  save_json("volunteer_gov_sg_details.json", volunteer_gov_sg_details)
  teardown_driver()

  volunteer_gov_sg_details = load_json("volunteer_gov_sg_details.json")

  print("End scraper")