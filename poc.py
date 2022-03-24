from requests import request
from lxml import html
from operator import itemgetter
from time import sleep
from pathlib import Path
import os.path
import json
import re
import csv

HEADERS = ['numberOfProjects', 'costVariance', 'fiscalYear', 'agencyCode', 'agencyName', 'DataAsOf']

def run():
	r = request('GET',
				'https://viz.ogp-mgmt.fcs.gsa.gov/agency-analysis',
				timeout=30)
	r.raise_for_status()
	tree = html.fromstring(r.text)
	raw_data = json.loads(tree.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()')[0])
	var_data, fiscal_year, data_as_of = find_variance_data(raw_data['itportfoliodashboard'])
	agency_mapping = get_agency_mapping(tree)
	abbr_mapping = get_abbr_mapping(var_data[0])
	var_data = parse_variance_data(var_data)
	aggregated_data = aggregate_data(var_data, agency_mapping, fiscal_year, data_as_of)	
	save_as_csv(aggregated_data)

def save_as_csv(data):
	with open(os.path.join(Path().absolute(), 'data.csv'), 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerow(HEADERS)
		writer.writerows(data)

def parse_variance_data(var_data):
	return {parse_name(d['name']): parse_var_data(d) 
			for d 
			in var_data}

def parse_name(name):
	return name.partition('(')[0]

def parse_var_data(dataset):
	return {code: n_proj 
			for code, n_proj 
			in zip(*itemgetter('customdata', 'text')(dataset))}

def find_variance_data(data):
	for k in data.keys():
		s = json.dumps(data[k]).lower()
		if 'variance' in s:
			return data[k]['dataset'], get_fiscal_year(s), get_data_as_of(s)

def get_fiscal_year(s):
	return re.search(r'year<\/b>: (\d+)', s).group(1)

def get_data_as_of(s):
	return re.search(r'data as of: (\S+)', s).group(1)

def get_agency_mapping(tree):
	return {agency.get('value'): agency.text 
			for agency 
			in tree.xpath('//select/option')}

def get_abbr_mapping(data):
	return {code: abbr 
			for code, abbr 
			in zip(*itemgetter('customdata', 'y')(data))}

def aggregate_data(data, agency_mapping, fiscal_year, data_as_of):
	aggregated_data = []
	for code, agency in agency_mapping.items():
		for cost_var in ('Low', 'Medium', 'High'):
			aggregated_data.append([data[cost_var][code], 
				cost_var, fiscal_year, code, agency, data_as_of])
	return aggregated_data			

if __name__ == '__main__':
	run()