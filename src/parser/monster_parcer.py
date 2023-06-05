# pip install fake_useragent, selenium, webdriver_manager


import argparse
import time
from typing import Tuple, List, Dict, Union
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import csv
import os
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent
from datetime import date
import logging
import warnings
import json
from utils import setup_logging, write_to_csv, get_driver


warnings.filterwarnings('ignore')

today = date.today()
test_junior = ['junior', 'jr', 'entry-level', 'intern', 'internship']
test_dads = ['analyst', 'scientist']


def web_driver_set(is_mobile):
    if is_mobile == True:
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
        mobile_emulation = {
            "deviceMetrics": {"width": 760, "height": 1640, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-US; \
            NEXUS 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) \
            Chrome/18.0.1025.166 Mobile Safari/535.19"
        }
        chrome_options = Options()
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        driver = webdriver.Chrome(chrome_options=chrome_options,
                                  desired_capabilities=desired_capabilities)
    else:
        chrome_options = Options()
        useragent = UserAgent()
        chrome_options.add_argument(f"user-agent={useragent.random}")
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(chrome_options=chrome_options)
    return driver


def jobtype(row):
    if 'hybrid' in row.lower():
        return 'Hybrid'
    elif 'remote' in row.lower():
        return 'Remote'
    elif 'full-time' in row.lower() or 'full time' in row.lower():
        return 'Full-time'
    elif 'contract' in row.lower():
        return 'Contract'
    else:
        return None


def country_url(json_url, set_driver):
    url_vacancy = []
    with open(json_url, 'r') as file:
        dictionary_url = json.load(file)
    driver = get_driver() # web_driver_set(set_driver)
    try:
        for key, value in dictionary_url.items():
            c_url = [value[0]]
            for c in c_url:
                driver.get(c)
                time.sleep(3)
                counter = 0
                while True:
                    win = driver.find_element(By.TAG_NAME, 'html')
                    win.send_keys(Keys.END)
                    time.sleep(2)
                    counter += 1
                    if f"<span>{value[1]}</span>" in driver.page_source or counter > 30:
                        break
                time.sleep(5)
                links = driver.find_elements(
                    By.CSS_SELECTOR,
                    "a.job-cardstyle__JobCardComponent-sc-1mbmxes-0"
                )
                for l in links:
                    url_vacancy.append(l.get_attribute("href") + ' ' + key)
            logging.info(f"End country {key}. Total vacancy {len(url_vacancy)}")
    except Exception as ex:
        logging.info(f"Something wrong in scrap country {key} : {ex}")
    finally:
        driver.close()
        driver.quit()
    return url_vacancy


def scrap_links(match_dads, match_junior, list_url_vacancy, set_driver):
    global today
    data = []
    cnt_vaсancy = 0
    cnt_fail = 0
    driver = get_driver()# web_driver_set(set_driver)
    for item in list_url_vacancy:
        if cnt_vaсancy % 10 == 0:
            logging.info(f"Viewed {cnt_vaсancy} vacancies")
        value, key = item.split()
        driver.get(value)
        time.sleep(5)
        try:
            test_title = driver.find_element(By.CLASS_NAME,
                                             'JobViewTitle').text.lower()
        except:
            cnt_fail += 1
            logging.info(f"Fail in title. Total fails {cnt_fail}")
            test_title = 'Not found'
        dads = False
        junior = False
        for x in match_dads:
            if test_title.find(x) != -1:
                dads = True
                break
        for y in match_junior:
            if test_title.find(y) != -1:
                junior = True
                break
        if dads == True and junior == True:
            try:
                title = driver.find_element(By.CLASS_NAME,
                                            'JobViewTitle').text
            except:
                title = ''
            try:
                company = driver.find_element(
                    By.CLASS_NAME,
                    'headerstyle__JobViewHeaderCompany-sc-1ijq9nh-6'
                ).text
            except:
                company = ''
            link = value
            country = key
            date = today
            source = "https://www.monster.com/"
            try:
                location = driver.find_element(
                    By.CLASS_NAME,
                    'headerstyle__JobViewHeaderLocation-sc-1ijq9nh-4'
                ).text
            except:
                location = ''
            try:
                company_field = (
                    driver
                    .find_element(
                        By.CLASS_NAME,
                        'jobview-containerstyles__CompanyInformation-sc-16af7k7-6'
                    )
                    .find_element(
                        By.CLASS_NAME,
                        'detailsstyles__DetailsTableDetailBody-sc-1deoovj-5'
                    )
                    .text
                )
            except:
                company_field = ''
            try:
                description = driver.find_element(
                    By.CLASS_NAME,
                    'descriptionstyles__DescriptionContainer-sc-13ve12b-0'
                ).text
            except:
                description = ''
            try:
                salary = driver.find_element(
                    By.CLASS_NAME,
                    'salarystyle__SalaryContainer-sc-1kub5et-7'
                ).text
            except:
                salary = ''
            skills = ''
            job_type = jobtype(title)
            data.append((title, company, country, location, salary, source, link,
                         date, company_field, description, skills, job_type))
            cnt_vaсancy += 1
        else:
            cnt_vaсancy += 1
    driver.close()
    driver.quit()
    return data


def parse_args() -> Dict[str, str]:
    parser = argparse.ArgumentParser(description='Scrapes job postings from monster.com')
    parser.add_argument('-f', '--filename', type=str, help='Name of output file', default="")
    return vars(parser.parse_args())


def main(filename: str = ""):
    url_vacancy = country_url('url_dict_today.json', True)
    data = scrap_links(test_dads, test_junior, url_vacancy, False)
    if filename == "":
        filename = f'monster_{date.today()}.csv';
    write_to_csv(data, filename)


if __name__ == "__main__":
    setup_logging("log.txt")
    args = parse_args()
    main(args["filename"])
