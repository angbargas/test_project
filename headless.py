from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pathlib import Path
import os.path
from time import sleep
from random import sample, uniform

base_dir = str(Path().absolute())
chrome_driver_path = os.path.join(base_dir, 'chromedriver')
prefs = {"download.default_directory": base_dir}
backoff = [10, 30, 60]

def run():
	chrome_opt = webdriver.ChromeOptions()
	chrome_opt.headless = True
	chrome_opt.add_experimental_option("prefs", prefs)
	with webdriver.Chrome(executable_path=chrome_driver_path,
						  chrome_options=chrome_opt) as wd:

		for delay in backoff:
			try:
				wd.get('https://viz.ogp-mgmt.fcs.gsa.gov/agency-analysis') # go directly
				click_elem(wd, 'a.usa-select')
				dpts = wd.find_elements_by_css_selector('li[data-dept-name]')
				for dpt in dpts[:6]:
					dpt.click()
					sleep(uniform(0.5, 1))
				click_elem(wd, '.done')
				click_elem(wd, 'a[data-activate=cost-variance]')
				click_elem(wd, '#cost-variance').screenshot(os.path.join(base_dir, 'chart.png'))
				click_elem(wd, '#cost-variance .download a')
				wait_for_dl()
				return
			except Exception as e:
				print(e)
				sleep(delay)

	raise Exception('Maximum retries reached')

def file_check(fn):
	return os.path.isfile(os.path.join(base_dir, fn))

def ensure_chart():
	if not file_check('chart.png'):
		raise Exception("Chart screenshot failed")

def wait_for_dl():
	for i in range(20):
		if file_check('agency-analysis-cost-variance.csv'):
			return
		else:
			sleep(1)
	raise Exception("No downloaded file")

def click_elem(wd, selector):
	"""
	Convenience function for wait+search+scroll+click elements
	"""
	el = WebDriverWait(wd, 20).until(
		 EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
	wd.execute_script("arguments[0].scrollIntoView();", el)
	el.click()
	return el

if __name__ == '__main__':
	run()