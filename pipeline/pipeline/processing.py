from data import load_json, save_json

from bs4 import BeautifulSoup as soup
import pandas as pd

def volunteering_gov_sg_detail_extract():
  print("Processing volunteering.gov.sg details")
  volunteer_gov_sg_details = load_json("volunteer_gov_sg_details.json")
  dfs = []

  for entry in volunteer_gov_sg_details['entries']:
    url = entry['url']
    page = soup(entry['html'], "lxml")
    page_details = page.select_one("#oppoRoleDetails")
    page_table = page_details.select_one("table.oppoRegistration")
    df = pd.read_html(str(page_table))[0]
    df['url'] = url
    dfs.append(df)

  all_df = pd.concat(dfs)
  all_df = all_df.reset_index(drop=True)
  all_df.to_csv("/srv/output/volunteer_gov_sg_details.csv")

def main():
  volunteering_gov_sg_detail_extract()