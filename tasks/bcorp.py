import requests
import requests
from bs4 import BeautifulSoup
import re
import math
import itertools
from jinja2 import Environment
import pprint

def build_company_urls(soup):
	path = soup.find('a')['href']	
	return BASE_URL + path

def find_links(soup):
	return soup.findAll('div', attrs={"class":"company-logo"})

def find_company_reports(soup):
	return soup.find('div', text=re.compile("full\s+reports")).findNext('div').findAll('a')

def build_report_urls(soup):
	path = soup['href']	
	return BASE_URL + path

# BASE_URL = 'https://www.bcorporation.net'
# URL = 'https://www.bcorporation.net/community/find-a-b-corp?search=%2A&field_state=&field_city=&field_country=&field_industry='
# markup = requests.get(URL).text.encode('utf-8')
# soup = BeautifulSoup(markup)
# results = soup.find(attrs={"class":"bcorp-count"}).contents[0]
# num_results = results.strip().split(' ')[3]
# num_pages = math.ceil(float(num_results) / 21)

# for page in pages:
# 	companies = find_links(soup)
# 	company_urls = [build_company_urls(s) for s in companies]
# 	for company in company_urls:
# 		company_markup = requests.get(company_urls[0]).text.encode('utf-8')
# 		company_soup = BeautifulSoup(company_markup)
# 		reports = find_company_reports(company_soup)
# 		report_urls = [build_report_urls(report) for report in reports]

# companies = find_links(soup)
# company_urls = [build_company_urls(s) for s in companies]
# company_markup = requests.get(company_urls[0]).text.encode('utf-8')
# company_soup = BeautifulSoup(company_markup)
# reports = find_company_reports(company_soup)
# report_urls = [build_report_urls(report) for report in reports]

test_url = 'https://www.bcorporation.net/community/exygy/impact-report/2012-06-26-000000'

def get_section_score(section, soup):
	try:
		parent = soup.find('div', 
			attrs={"class": section})
		score_div = parent.find('div',
			attrs={"class":"field-item even"})
		score = score_div.contents[0]
		return int(score)
	except:
		return 0

def get_score(url):
	markup = requests.get(url).text
	soup = BeautifulSoup(markup)
	score_dict = {
		'overall': get_section_score('field-name-field-overall-b-score', soup),
		'environment': {
			'overall': get_section_score('field-name-field-environment', soup),
			'products_services': get_section_score('field-name-field-environmental-products-ser', soup),
			'practices': get_section_score('field-name-field-environmental-practices', soup),
			'land_office_plant': get_section_score('field-name-field-land-office-plant', soup),
			'energy_water_materials': get_section_score('field-name-field-inputs', soup),
			'emissions_water_waste': get_section_score('field-name-field-outputs', soup),
			'suppliers_transportation': get_section_score('field-name-field-suppliers-transportation', soup)
		},
		'workers': {
			'overall': get_section_score('field-name-field-workers', soup),
			'comp_benefits_training': get_section_score('field-name-field-compensation-benefits-trai', soup),
			'ownershp': get_section_score('field-name-field-worker-ownership', soup),
			'environment': get_section_score('field-name-field-work-environment', soup)
		},
		'community': {
			'overall': get_section_score('field-name-field-community', soup),
			'community_products_services': get_section_score('field-name-field-community-products-service', soup),
			'community_practices': get_section_score('field-name-field-community-practices', soup),
			'suppliers_destributors': get_section_score('field-name-field-suppliers-distributors', soup),
			'local_involvement': get_section_score('field-name-field-local-involvement', soup),
			'diversity': get_section_score('field-name-field-diversity', soup),
			'job_creation': get_section_score('field-name-field-job-creation', soup),
			'civic_engagement_giving': get_section_score('field-name-field-civic-engagement-giving', soup) 
		},
		'governance': {
			'overall': get_section_score('field-name-field-governance', soup),
			'accountability': get_section_score('field-name-field-corporate-accountability', soup),
			'transparency': get_section_score('field-name-field-transparency', soup)
		}
	}
	print pprint.pprint(score_dict)

get_score(test_url)




