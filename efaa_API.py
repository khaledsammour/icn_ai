import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
import os
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor

requests.packages.urllib3.disable_warnings()
LOGGER.setLevel(logging.WARNING)
logging.basicConfig(level=logging.ERROR)


def create_browser():
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-features=NetworkService')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-features=IsolateOrigins')
    chrome_options.add_argument('--disable-features=AutofillCreditCardSignin')
    # chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://efaa.sa/')
    return driver

def get_arabic_day_name(day_name):
    day_name_mapping = {
        'Sunday': 'الاحد',
        'Monday': 'الاثنين',
        'Tuesday': 'الثلاثاء',
        'Wednesday': 'الاربعاء',
        'Thursday': 'الخميس',
        'Friday': 'الجمعة',
        'Saturday': 'السبت'
    }
    return day_name_mapping[day_name]


def extract_variables(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Define regular expressions for extracting variables
    url_pattern = re.compile(r'url: (.+)')
    workers_pattern = re.compile(r'max_workers: (.+)')

    # Search for matches using regular expressions
    url_match = url_pattern.search(content)
    workers_match = workers_pattern.search(content)

    # Extract values from matches
    URL = url_match.group(1) if url_match else None
    max_workers = workers_match.group(1) if workers_match else 100


    return URL, max_workers

# Function to fetch the page and extract res_num and ticket_num
def fetch_violation_details(URL):
    url = f'{URL}/violations-list'
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error fetching violation details: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    violations = []
    table = soup.find('table', class_='table-hover')

    if table:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 5:
                try:
                    violation_id = int(cols[0].text.strip())  # Ensure this is converted to an integer
                except ValueError:
                    continue  # Skip this row if conversion fails

                violation_date = cols[1].text.strip()
                res_num = cols[3].text.strip()
                ticket_num = cols[2].text.strip()
                violations.append((violation_id, violation_date, res_num, ticket_num))

    return violations


# Function to use Selenium to get details
def get_details(driver, res_num, ticket_num, violation_id):
    try:
        wait = WebDriverWait(driver, 10)
        try:
            element_to_delete = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="form1"]/div[3]/div/div[2]/div/div/div[2]/div[2]/div[1]')))
            element_to_delete.click()
        except:
            pass
        
        wait = WebDriverWait(driver, 10)

        res_num_input_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                           "input[placeholder='رقم الهوية أو رقم الحدود']")))
        res_num_input_field.send_keys(res_num)

        ticket_input_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                          "input[placeholder='رقم المخالفة'")))
        ticket_input_field.send_keys(ticket_num)

        last_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                             '#home > button')))
        last_button.click()
        main_container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#CustomModalBodyCard > div.popupDetails.DivDetailsToPrint'))
        )

        # Get all labels and corresponding values in one go using XPath
        content = main_container.get_attribute('innerHTML')
        soup = BeautifulSoup(content, 'html.parser')
        detail_elements = soup.select("div.detailsGroup")
        # detail_elements = main_container.find_elements(By.XPATH, ".//div[contains(@class, 'detailsGroup')]")

        details = {}
        # Use a dictionary to map Arabic labels to English keys
        label_map = {
            'هوية المخالف': 'num_person',
            'رقم المخالفة': 'num_infringement',
            'الجهة للمخالفة': 'from_infringement',
            'نوع المخالفة': 'kind_infringement',
            'تاريخ المخالفة': 'data_infringement',
            'وقت المخالفة': 'time_infringement',
            'مدينة المخالفة': 'city_infringement',
            'الشارع': 'street_infringement',
            'سرعة الشارع': 'street_speed',
            'سرعة المركبة': 'vehicle_speed',
            'رقم المسار': 'lane_number',
            'الرقم التسلسلي للمركبة الأجنبية': 'num_vehicle1',
            'إتجاه المركبة': 'diriction_vehicle',
            'الرقم التسلسلي للمركبة': 'num_vehicle2',
            'نوع تسجيل المركبة': 'kind_registration',
            'ماركة المركبة': 'marka',
            'طراز المركبة': 'vehicle_Taraz',
            'رقم اللوحة': 'plate_number',
            'حالة المخالفة': 'violation_case',
            'تاريخ سداد المخالفة': 'data_pay',
            'إجمالي مبلغ المخالفة': 'amount'
        }

        for element in detail_elements:
            try:
                label = element.select_one('label').get_text(strip=True)
                # label = element.find_element(By.TAG_NAME, 'label').text.strip()
                value = element.select_one('.detailsValue').get_text(strip=True)
                # value = element.find_element(By.CLASS_NAME, 'detailsValue').text.strip()

                if label in label_map:
                    details[label_map[label]] = value
            except Exception as e:
                print(f"An error occurred while processing element: {e}")

        try:
            # Extract explanation
            explane = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     '#CustomModalBodyCard > div.popupDetails.DivDetailsToPrint > div > div.col-12.popupDetailsBody > div > div > div > div > div > div.col-12.col-md-9 .detailsValue')
                )
            ).text.strip()
            details["explane"] = explane
        except Exception as e:
            print(f"An error occurred while extracting the explanation: {e}")
        
    except Exception as e:
        details = {}

    update_violation(URL, violation_id, details)


def get_details_by_date(driver, res_num, violator_date, violation_id):
    year, month, day = violator_date.split('-')

    details = {}

    try:
        wait = WebDriverWait(driver, 10)
        try:
            element_to_delete = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="form1"]/div[3]/div/div[2]/div/div/div[2]/div[2]/div[1]')))
            element_to_delete.click()
        except:
            pass
        wait = WebDriverWait(driver, 10)

        res_num_input_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                           "input[placeholder='رقم الهوية أو رقم الحدود']")))
        res_num_input_field.send_keys(res_num)

        date_input_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                        "i.BtnToG.css-icon > span")))
        date_input_field.click()

        date_input_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                        "div.GregorianDate > input.hasCalendarsPicker")))
        date_input_field.click()

        month_without_zeros = month.lstrip('0')
        day_without_zeros = day.lstrip('0')

        year_selector = f"select.calendars-month-year option[value*='{year}']"
        month_selector = f'select.calendars-month-year option[value="{month_without_zeros}/{year}"]'

        year_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, year_selector)))
        year_element.click()
        month_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, month_selector)))
        month_element.click()

        target_date = datetime.datetime(int(year), int(month), int(day))
        day_name = target_date.strftime("%A")
        arabic_day_name = get_arabic_day_name(day_name)
        month_name = target_date.strftime("%b")

        # Construct a dynamic selector based on the day name and date
        day_selector = f"//a[@title='Select {arabic_day_name}, {month_name} {day_without_zeros}, {year}']"

        try:
            day_element = wait.until(EC.element_to_be_clickable((By.XPATH, day_selector)))
            day_element.click()
        except Exception as e:
            print(f"Failed to select the day: {e}")

        last_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                             '#home > button')))
        last_button.click()

        # Obtain OTP from user
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@id='CustomModalBodyCard' and .//h4[text()='أدخل الرقم المرسل إلى جوالك']]")))

        requests.get(f'https://u7l.ff7.mytemp.website/violations-list/{violation_id}/RequestOTP', verify=False, )

        for i in range(12):
            url = f'https://u7l.ff7.mytemp.website/violations-list/{violation_id}/edit'

            response = requests.get(url, verify=False)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                userOTP_input = soup.find('input', {'name': 'userOTP'})
                if userOTP_input:
                    userOTP_value = userOTP_input.get('value', '')
                    if userOTP_value:
                        print("UserOTP Value:", userOTP_value)
                        break
                    else:
                        time.sleep(5)
                        continue
            else:
                print("Failed to fetch the page. Status code:", response.status_code)
                time.sleep(5)
        if not userOTP_value:
            return details

        for i, digit in enumerate(userOTP_value):
            input_field = driver.find_element(By.CLASS_NAME, f"InputIndex-{i + 1}")
            input_field.send_keys(digit)

        confirm_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "#CustomModalBodyCard > div > div.OTPBtns > button.btn.btn-primary.py-1.px-3.otpSend")))
        confirm_button.click()

        main_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#CustomModalBodyCard > div.popupDetails.DivDetailsToPrint'))
        )

        # Get all labels and corresponding values in one go using XPath
        detail_elements = main_container.find_elements(By.XPATH, ".//div[contains(@class, 'detailsGroup')]")

        # Use a dictionary to map Arabic labels to English keys
        label_map = {
            'هوية المخالف': 'num_person',
            'رقم المخالفة': 'num_infringement',
            'الجهة للمخالفة': 'from_infringement',
            'نوع المخالفة': 'kind_infringement',
            'تاريخ المخالفة': 'data_infringement',
            'وقت المخالفة': 'time_infringement',
            'مدينة المخالفة': 'city_infringement',
            'الشارع': 'street_infringement',
            'سرعة الشارع': 'street_speed',
            'سرعة المركبة': 'vehicle_speed',
            'رقم المسار': 'lane_number',
            'الرقم التسلسلي للمركبة الأجنبية': 'num_vehicle1',
            'إتجاه المركبة': 'diriction_vehicle',
            'الرقم التسلسلي للمركبة': 'num_vehicle2',
            'نوع تسجيل المركبة': 'kind_registration',
            'ماركة المركبة': 'marka',
            'طراز المركبة': 'vehicle_Taraz',
            'رقم اللوحة': 'plate_number',
            'حالة المخالفة': 'violation_case',
            'تاريخ سداد المخالفة': 'data_pay',
            'إجمالي مبلغ المخالفة': 'amount'
        }

        for element in detail_elements:
            try:
                label = element.find_element(By.TAG_NAME, 'label').text.strip()
                value = element.find_element(By.CLASS_NAME, 'detailsValue').text.strip()

                if label in label_map:
                    details[label_map[label]] = value
            except Exception as e:
                print(f"An error occurred while processing element: {e}")

        try:
            # Extract explanation
            explane = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     '#CustomModalBodyCard > div.popupDetails.DivDetailsToPrint > div > div.col-12.popupDetailsBody > div > div > div > div > div > div.col-12.col-md-9 .detailsValue')
                )
            ).text.strip()
            details["explane"] = explane
        except Exception as e:
            print(f"An error occurred while extracting the explanation: {e}")

    except Exception as e:
        details = {}

    update_violation(URL, violation_id, details)


def update_violation(URL, violation_id, details):
    url = f'{URL}/violations-list/{violation_id}/update'

    if not details:
        # Details is empty, construct payload with empty fields and status 'rejected'
        payload = {
            '_token': 'OAx6RhDoPOXj6CLEOgFJP8NZELn8egatT4iatmNL',
            'structure_name': '',
            'fine_group_description': '',
            'violation_number': '',
            'violation_date': '',
            'violation_status_code': '',
            'violation_status_desc_ar': '',
            'violation_status_desc_en': '',
            'violator_id': '',
            'vehicle_serial_number': '',
            'vehicle_plate': '',
            'vehicle_type_code': '',
            'vehicle_type_desc_ar': '',
            'vehicle_type_desc_en': '',
            'vehicle_make': '',
            'vehicle_model': '',
            'violation_string_h': '',
            'violation_string_g': '',
            'violation_time': '',
            'violation_city': '',
            'place_happend': '',
            'payment_string': '',
            'payment_string_g': '',
            'warning_ind': '',
            'accident_ind': '',
            'fine_damage': '',
            'clearance_ind': '',
            'clearance_string_h': '',
            'detection_center_code': '',
            'detection_center_name': '',
            'gis_longitude': '',
            'gis_latitude': '',
            'foreign_vehicle_number': '',
            'foreign_vehicle_crossing_seq': '',
            'total_fine_items_amount': '',
            'street_speed': '',
            'vehicle_speed': '',
            'lane_number': '',
            'vehicle_direction': '',
            'street_name': '',
            'violation_type_desc_ar': '',
            'lk_pay_type': '',
            'lk_pay_type_desc_ar': '',
            'lk_pay_type_desc': '',
            'status': 'rejected'  # Set status to 'rejected'
        }
    else:
        # Details is provided, populate payload with details
        payload = {
            '_token': 'OAx6RhDoPOXj6CLEOgFJP8NZELn8egatT4iatmNL',
            'structure_name': details.get("from_infringement", ''),
            'fine_group_description': details.get("kind_infringement", ''),
            'violation_number': details.get("num_infringement", ''),
            'violation_date': details.get("data_infringement", ''),
            'violation_status_code': '',
            'violation_status_desc_ar': details.get("violation_case", ''),
            'violation_status_desc_en': '',
            'violator_id': details.get("num_person", ''),
            'vehicle_serial_number': details.get("num_vehicle2", ''),
            'vehicle_plate': details.get("plate_number", ''),
            'vehicle_type_code': '',
            'vehicle_type_desc_ar': details.get("kind_registration", ''),
            'vehicle_type_desc_en': '',
            'vehicle_make': details.get("marka", ''),
            'vehicle_model': details.get("vehicle_Taraz", ''),
            'violation_string_h': '',
            'violation_string_g': '',
            'violation_time': details.get("time_infringement", ''),
            'violation_city': details.get("city_infringement", ''),
            'place_happend': '',
            'payment_string': '',
            'payment_string_g': '',
            'warning_ind': '',
            'accident_ind': '',
            'fine_damage': details.get("amount", ''),
            'clearance_ind': '',
            'clearance_string_h': '',
            'detection_center_code': '',
            'detection_center_name': '',
            'gis_longitude': '',
            'gis_latitude': '',
            'foreign_vehicle_number': details.get("num_vehicle1", ''),
            'foreign_vehicle_crossing_seq': '',
            'total_fine_items_amount': details.get("amount", ''),
            'street_speed': details.get("street_speed", ''),
            'vehicle_speed': details.get("vehicle_speed", ''),
            'lane_number': details.get("lane_number", ''),
            'vehicle_direction': details.get("diriction_vehicle", ''),
            'street_name': details.get("street_infringement", ''),
            'violation_type_desc_ar': details.get("explane", ''),
            'lk_pay_type': '',
            'lk_pay_type_desc_ar': '',
            'lk_pay_type_desc': '',
            'paymentDateG': details.get("data_pay", ''),
            'status': 'founded' if not "error" in details else 'rejected'
        }
    print(payload)
    response = requests.post(url, data=payload, verify=False)
    print(f"Updated violation ID {violation_id} with response: {response.status_code}")


# Main function to check for new requests and fetch details
def main_loop():
    executor = ThreadPoolExecutor(max_workers=int(max_workers))
    max_violation_id = 0  # Variable to store the highest violation ID
    print(f"[+] Fetching new requests from {URL} ...")
    drivers = []
    for i in range(100):
        drivers.append({"working": False, "browser": create_browser()})
    while True:
        violations = fetch_violation_details(URL)
        new_violations = [v for v in violations if v[0] > max_violation_id]

        for violation_id, violator_date, res_num, ticket_num in new_violations:
            driver = None 
            for d in drivers:
                if d['working'] == False:
                    d['working'] = True
                    driver = d
                    break
            if not ticket_num:  # Check if both are not empty
                executor.submit(get_details_by_date, driver['browser'], res_num, violator_date, violation_id)

            else:
                executor.submit(get_details, driver['browser'], res_num, ticket_num, violation_id)
            # Update max_violation_id
            if violation_id > max_violation_id:
                max_violation_id = violation_id
            driver['working'] = False
            driver['browser'].get('https://efaa.sa/')

        time.sleep(1)


if __name__ == '__main__':
    URL, max_workers = extract_variables('Settings.txt')
    main_loop()
