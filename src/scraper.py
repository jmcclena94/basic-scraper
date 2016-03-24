import requests
import io
from bs4 import BeautifulSoup
import sys
import re


INSPECTION_DOMAIN = 'http://info.kingcounty.gov'
INSPECTION_URI = '/health/ehs/foodsafety/inspections/Results.aspx'
INSPECTION_PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '98101',
    'Inspection_Type': 'All',
    'Inspection_Start': '3/23/2015',
    'Inspection_End': '3/23/2016',
    'Inspection_Closed_Business': 'A',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'B',
}


def get_inspection_page(**search_params):
    url = INSPECTION_DOMAIN + INSPECTION_URI
    payload = INSPECTION_PARAMS.copy()
    for key, val in search_params.items():
        if key in INSPECTION_PARAMS:
            payload[key] = val
    resp = requests.get(url, params=payload)
    resp.raise_for_status()
    html_file = io.open('inspection_page.html', 'wb')
    html_file.write(resp.content)
    html_file.close()
    return resp.content


def load_inspection_page(filename):
    open_file = io.open(filename, 'rb')
    html_body = open_file.read()
    open_file.close()
    return html_body


def parse_source(html):
    soup = BeautifulSoup(html)
    return soup


def extract_data_listings(html_parsed):
    div_regex = re.compile(r'PR[\d]+~')
    return html_parsed.find_all('div', id=div_regex)


def has_two_tds(element):
    el_name = element.name
    el_children = element.find_all('td', recursive=False)
    if el_name == 'tr' and len(el_children) == 2:
        return True
    else:
        return False


def clean_data(cell):
    cell_str = cell.string
    try:
        return cell_str.strip().strip('- ').strip(':')
    except:
        return u'Address 2:'


def extract_restaurant_metadata(listing):
    metadata = {}
    business_data = listing.find('table'
                                 ).find_all(has_two_tds, recursive=False)
    for data in business_data:
        tds = data.find_all('td', recursive=False)
        clean_key = clean_data(tds[0])
        clean_val = clean_data(tds[1])
        metadata[clean_key] = clean_val
    return metadata


def is_inspection_row(element):
    el_children = element.find_all('td', recursive=False)
    if len(el_children) == 0:
        return False
    is_tr = element.name == 'tr'
    has_4 = len(el_children) == 4
    clean_text = clean_data(el_children[0]).lower()
    inspect_in = 'inspection' in clean_text
    first_word = not clean_text.startswith('inspection')
    return is_tr and has_4 and inspect_in and first_word


def extract_score_data(listing):
    inspection_rows = listing.find_all(is_inspection_row)
    if len(inspection_rows) == 0:
        return 'No Data'
    total_score = 0
    inspections = 0
    highest_score = 0
    for row in inspection_rows:
        inspection_score = int(row.find_all('td')[2].text)
        inspections += 1
        total_score += inspection_score
        if inspection_score > highest_score:
            highest_score = inspection_score
    average_score = total_score/inspections
    score_dict = {u'Average': average_score,
                  u'High': highest_score, u'Inspections': inspections}
    return score_dict


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        html = load_inspection_page('inspection_page.html')
    else:
        html = get_inspection_page(sys.argv[1])
    html_parsed = parse_source(html)
    listings = extract_data_listings(html_parsed)
    data_dict = {}
    for listing in listings:
        metadata = extract_restaurant_metadata(listing)
        score_data = extract_score_data(listing)
        data_dict[metadata['Business Name']] = [metadata, score_data]
    print(data_dict['VEGGIE GRILL'])
