from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import requests
from time import sleep
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup
import language_tool_python
import re
from deep_translator import GoogleTranslator
import yake
from langdetect import detect
import os 
from django.conf import settings  # Import project settings
from airtable import Airtable
from random import *

API_KEY='patKfzGeYSaMEflNh.436aae2a5ffa7285045f29714bddfcee86ae9ff624a1748533231aaede505715'
def get_hrefs(driver, url, pagination, selector, attr="href", not_contains_class=None, inner_selector=None, should_not_exist='', index=1, max_index=None, start_pagination=False, no_pagination=False, pagination_click=False):
    isExist = True
    hrefs = []
    fitst_index = index
    if start_pagination:
        driver.get(url+pagination+str(index)+('/' if 'page=' not in pagination and 'pageNumber=' not in pagination and pagination != 'p=' else ''))
    while(isExist):
        if index != fitst_index:
            if pagination_click:
                if len(driver.find_elements(By.CSS_SELECTOR, pagination_click))==0:
                    break
                until_visible_click(driver, pagination_click)
            else:
                driver.get(url+pagination+str(index)+('/' if 'page=' not in pagination and 'pageNumber=' not in pagination and pagination != 'p=' else ''))

        # if url not in driver.current_url:
        #     break

        sleep(5)
        if should_not_exist:
            isExist = check_if_not_exist(driver, should_not_exist, "products")
        else:
            isExist = check_if_exist(driver, selector, "products")
        
        if max_index:
            if index == max_index:
                isExist=False
        
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for e in elements:
            if not_contains_class != None:
                if len(e.find_elements(By.CSS_SELECTOR, not_contains_class)) == 0:
                    if inner_selector != None:
                        href = e.find_element(By.CSS_SELECTOR, inner_selector).get_attribute(attr)
                        if href not in hrefs:
                            hrefs.append(href)
                    else:
                        href = e.get_attribute(attr)
                        if href not in hrefs:
                            hrefs.append(href)
            else:
                if inner_selector != None:
                    href = e.find_element(By.CSS_SELECTOR, inner_selector).get_attribute(attr)
                    if href not in hrefs:
                        hrefs.append(href)
                else:
                    href = e.get_attribute(attr)
                    if href not in hrefs:
                        hrefs.append(href)
        index = index + 1
        
        if no_pagination:
            isExist = False
    return hrefs

def create_browser(page_load_strategy='normal'):
    chrome_options = Options()
    # none, eager, normal
    chrome_options.page_load_strategy = page_load_strategy
    # chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--no-sandbox') 
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-features=NetworkService')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-features=IsolateOrigins')
    chrome_options.add_argument('--disable-features=AutofillCreditCardSignin')
    # chrome_options.add_argument('--headless')
    driver = Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def checkProduct(url):
    url = 'https://www.icn.com/api/v1/check/product'
    data = {
        'link': url
    }

    try:
        # Send the POST request and wait for the response
        response = requests.post(url, data=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print('Request was successful!')
            print('Response:', response.text)  # If the response contains JSON data
            return True if response.text == "1" else False
        else:
            print('Request failed with status code:', response.status_code)
            print('Response:', response.text)
    except requests.exceptions.RequestException as e:
        print('An error occurred:', e)

def save_image(image_data, file_path):
    with open(file_path, 'wb') as file:
        file.write(image_data)

def sendRequest(driver, url, body):
    js_code = """
    function getResponse(url, body) {
    return new Promise((resolve, reject) => {
        var xhr = new XMLHttpRequest();
        xhr.onload = function() {
            resolve(xhr.response);  // resolve the promise when the response is loaded
        };
        xhr.onerror = function() {
            reject('Error occurred while fetching the data');  // reject the promise on error
        };
        
        xhr.open('POST', url, true);  // Make sure the request is asynchronous
        xhr.setRequestHeader('Content-Type', 'application/json');  // Set the content type for JSON body
        xhr.responseType = 'json';  // Set the response type to JSON
        
        // Send the body as a JSON string
        xhr.send(JSON.stringify(body));
    });
}

// Example of usage:
function fetchSynonym(url, body) {
    return getResponse(url, body);
}

// Call the function to fetch synonyms and handle the response
return fetchSynonym(arguments[0], arguments[1]);
    """
    array_buffer = driver.execute_script(js_code, url, body)
    return array_buffer
    

def getImageBase64(driver, id, image_url):
    if 'youtube.com' in image_url:
        return ''
    image_url = image_url.replace('_60x.', '.').replace('/xs/','/lg/')
    js_code = """
    function getImageBlob(url) {
        return new Promise((resolve, reject) => {
            var xhr = new XMLHttpRequest();
            xhr.onload = function() {
                var reader = new FileReader();
                reader.onloadend = function() {
                    resolve(new Uint8Array(reader.result));
                };
                reader.readAsArrayBuffer(xhr.response);
            };
            xhr.open('GET', url);
            xhr.responseType = 'blob';
            xhr.send();
        });
    }

    return getImageBlob(arguments[0]);
    """
    # Execute the JavaScript code to get the ArrayBuffer
    if '?' in image_url:
        image_url = image_url.split('?')[0]
        if 'https:' not in image_url and 'http:' not in image_url:
            image_url = 'https:' + image_url
    print(image_url)
    array_buffer = driver.execute_script(js_code, image_url)
    
    # Convert the ArrayBuffer to bytes
    image_data = bytes(array_buffer)    

    url = 'https://www.icn.com/api/v1/image/upload'
    file_name = ''
    if '?' in image_url:
        file_name = image_url.split('?')[0].split('/')[-1]
    else:
        file_name = image_url.split('/')[-1]
    if '.' not in file_name:
        file_name = file_name + '.png'
    files=[
        ('image',(file_name,image_data,'image/png'))
    ]
    data = {
        'user_id': id,
    }

    try:
        # Send the POST request and wait for the response
        response = requests.post(url, data=data, files=files)
        # Check if the request was successful
        if response.status_code == 200:
            # print('Request was successful!')
            # print('Response:', response.text)  # If the response contains JSON data
            return response.text
        else:
            print('Request failed with status code:', response.status_code)
            # print('Response:', response.text)
            return ''
    except requests.exceptions.RequestException as e:
        print('An error occurred:', e)

def getImageUrl(id, image_url):
    url = 'https://www.icn.com/api/v1/image/upload'
    data = {
        'user_id': id,
        'image_url': image_url
    }

    try:
        # Send the POST request and wait for the response
        response = requests.post(url, data=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            # print('Request was successful!')
            # print('Response:', response.text)  # If the response contains JSON data
            return response.text
        else:
            print('Request failed with status code:', response.status_code)
            print('Response:', response.text)
            return ''
    except requests.exceptions.RequestException as e:
        print('An error occurred:', e)

def checkImageUrl(image_url):
    try:
        response = requests.get(image_url)
        
        if response.status_code == 200:
            return image_url
        else:
            raise Exception("status: "+response.status_code)
    except requests.exceptions.RequestException as e:
        print('An error occurred:', e)

def change_content(driver, data, id, withoutReset=True):
    if withoutReset:
        driver.get('https://www.scribbr.com/paraphrasing-tool/')
        until_visible(driver, '#QuillBotPphrIframe')
        iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
        driver.get(iframe.get_attribute('src'))
    for d in data:
        changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 else ''
        if len(changed_product_attributes_content)>5:
            d['English Description'] = changed_product_attributes_content
            d['Arabic Description'] = translate(changed_product_attributes_content)
    df = pd.DataFrame(data)
    df.to_excel('excel/new_'+id+'_products.xlsx', index=False)

def extract_top_keywords(text, language="en", max_ngram_size=2, deduplication_threshold=0.1, deduplication_algo='seqm', window_size=1, num_of_keywords=5):
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    try:
        custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, dedupFunc=deduplication_algo, windowsSize=window_size, top=num_of_keywords, features=None)
    except ModuleNotFoundError:
        raise ModuleNotFoundError("YAKE library not installed")

    keywords = custom_kw_extractor.extract_keywords(text)

    top_keywords = [kw[0] for kw in keywords]

    return top_keywords

def change_text(driver, text):
    driver.refresh()
    # switch to selected iframe
    until_visible(driver, '#paraphraser-input-box')
    # driver.execute_script('''document.querySelectorAll('.MuiDialog-root').forEach(function (e){e.remove()})''')
    driver.find_element(By.CSS_SELECTOR, '#paraphraser-input-box').clear()
    until_visible_send_keys(driver, '#paraphraser-input-box', text)
    driver.switch_to.window(driver.window_handles[0])
    until_visible_xpath_click(driver, "//button/*[contains(text(), 'Paraphrase')]")
    driver.switch_to.window(driver.window_handles[0])
    try: 
        until_visible_with_xpath(driver, "//button/*[contains(text(), 'Rephrase')]")
    except:
        driver.refresh()
        until_visible(driver, '#paraphraser-input-box')
        # driver.execute_script('''document.querySelectorAll('.MuiDialog-root').forEach(function (e){e.remove()})''')
        driver.find_element(By.CSS_SELECTOR, '#paraphraser-input-box').clear()
        until_visible_send_keys(driver, '#paraphraser-input-box', text)
        driver.switch_to.window(driver.window_handles[0])
        until_visible_xpath_click(driver, "//button/*[contains(text(), 'Paraphrase')]")
        driver.switch_to.window(driver.window_handles[0])
        until_visible_with_xpath(driver, "//button/*[contains(text(), 'Rephrase')]")

    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
    soup = BeautifulSoup(href_res, 'html.parser')
    return soup.select_one('#paraphraser-output-box').get_text(" ",strip=True)

def replace_dimensions(url):
    pattern = r'\d+x\d+.webp'
    return re.sub(pattern, '1200x1200.webp', url)

def translate(text, dest='ar', source='auto'):
    try:
        # lang = detect(text)
        # detected_lang = 'en' if lang == 'en' else 'ar'
        # print(text, detected_lang)
        # if detected_lang == dest:
        #     return text
        translation = GoogleTranslator(source=source, target=dest).translate(text)
        return translation
    except Exception as e:
        print(e)
        print(text)
        return text

def unwrap_divs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Unwrap divs, figures, and images
    for tag in soup.find_all(['div', 'figure', 'img']):
        tag.unwrap()
    
    # Remove all style attributes and classes
    for tag in soup.find_all(True):  # True matches all tags
        if tag.has_attr('style'):
            del tag['style']
        if tag.has_attr('class'):
            del tag['class']
    
    return soup.prettify()

def correct_spelling(text, lang):
    tool = language_tool_python.LanguageTool(lang)
    matches = tool.check(text)
    corrected_text = language_tool_python.utils.correct(text, matches)
    return corrected_text

def remove_emoji(string):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', str(string))

def until_visible(driver, element, max_counter=10,refresh=False,refresh_wait_element=None, secound_element=None):
    counter=0
    run = True
    while run:
        try:
            if len(driver.find_elements(By.CSS_SELECTOR, element)) > 0 or (len(driver.find_elements(By.CSS_SELECTOR, secound_element)) > 0 if secound_element else False):
                return
            else:
                if refresh:
                    driver.refresh()
                    if refresh_wait_element:
                        until_visible(driver, refresh_wait_element)
        except Exception as e:
            print(f"Error while checking for element visibility: {e}")

        counter += 1

        if counter > max_counter:
            print("Timed out waiting for element {}".format(element))
            raise ValueError("Timed out waiting for element {}".format(element))
        sleep(1)

def until_visible_with_xpath(driver, element, max_counter=10):
    counter = 0
    run = True
    while run:
        sleep(1)
        try:
            if len(driver.find_elements(By.XPATH, element)) > 0:
                break
        except Exception as e:
            pass

        counter += 1

        if counter > max_counter:
            print("Timed out waiting for element {}".format(element))
            raise ValueError("Timed out waiting for element {}".format(element))

def until_not_visible(driver, element, counterAmount=10):
    counter = 0
    run = True
    while run:
        sleep(1)
        try:
            if len(driver.find_elements(By.CSS_SELECTOR, element)) == 0:
                break
        except Exception as e:
            pass

        counter += 1

        if counter > counterAmount:
            raise Exception

def check_if_exist(driver, selector, name, secound_selector=None):
    try:
        until_visible(driver, selector, secound_element=secound_selector)
        if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0 or (len(driver.find_elements(By.CSS_SELECTOR, secound_selector)) > 0 if secound_selector else False):
            print('{} is shown'.format(name))
            return True
        else:
            print('{} is not shown'.format(name))
            return False
    except Exception as e:
        print('{} is not shown'.format(name))
        return False

def check_if_not_exist(driver, selector, name, secound_selector=None):
    try:
        until_visible(driver, selector, secound_element=secound_selector)
        if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0 or (len(driver.find_elements(By.CSS_SELECTOR, secound_selector)) > 0 if secound_selector else False):
            print('{} is shown'.format(name))
            return False
        else:
            print('{} is not shown'.format(name))
            return True
    except Exception as e:
        print('{} is not shown'.format(name))
        return False
    
def until_visible_xpath_click(driver, selector):
    until_visible_with_xpath(driver, selector)
    if '.v-overlay--active' in selector:
        overlay = driver.find_elements(By.CSS_SELECTOR, '.v-overlay--active .v-overlay__scrim')
        if len(overlay)>0:
            driver.execute_script("arguments[0].style.display = 'none';", overlay[0])
    element = driver.find_element(By.XPATH, selector)
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, selector))
        )
    except:
        pass
    try:
        ActionChains(driver).move_to_element(element).pause(1).click().perform()
    except Exception as e:
        try:
            element = driver.find_element(By.XPATH, selector)
            driver.execute_script("arguments[0].scrollIntoView({ block: 'end' });", element)
            ActionChains(driver).move_to_element(element).pause(1).click().perform()
        except:
            driver.find_element(By.XPATH, selector).click()

def until_visible_click(driver, selector):
    until_visible(driver, selector)
    if '.v-overlay--active' in selector:
        overlay = driver.find_elements(By.CSS_SELECTOR, '.v-overlay--active .v-overlay__scrim')
        if len(overlay)>0:
            driver.execute_script("arguments[0].style.display = 'none';", overlay[0])
    element = driver.find_element(By.CSS_SELECTOR, selector)
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
    except:
        pass
    try:
        driver.execute_script("""
            arguments[0].scrollIntoView({ block: 'center', inline: 'nearest' });
        """, element)
        ActionChains(driver).move_to_element(element).pause(1).click().perform()
    except Exception as e:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            driver.execute_script("""
            arguments[0].scrollIntoView({ block: 'center', inline: 'nearest' });
        """, element)
            # driver.execute_script("arguments[0].scrollIntoView({ block: 'end' });", element)
            ActionChains(driver).move_to_element(element).pause(1).click().perform()
        except:
            driver.find_element(By.CSS_SELECTOR, selector).click()
    
def until_visible_send_keys(driver, selector, key):
    until_visible(driver, selector)
    element = driver.find_element(By.CSS_SELECTOR, selector)
    try:
        ActionChains(driver).move_to_element(element).pause(1).perform()
    except Exception as e:
        try:
            driver.execute_script("arguments[0].scrollIntoView({ block: 'end' });", element)
            ActionChains(driver).move_to_element(element).pause(1).perform()
        except:
            pass
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    driver.find_element(By.CSS_SELECTOR, selector).send_keys(key)

def click_on_overlay(driver, name):
    until_visible(driver, '.v-overlay--active.v-menu .v-list-item')
    overlay = driver.find_elements(By.CSS_SELECTOR, '.v-overlay--active .v-overlay__scrim')
    if len(overlay)>0:
        driver.execute_script("arguments[0].style.display = 'none';", overlay[0])
    elements = driver.find_elements(By.CSS_SELECTOR, '.v-overlay--active.v-menu .v-list-item')
    for element in elements:
        if name in element.get_attribute('innerHTML'):
            try:
                ActionChains(driver).move_to_element(element).perform()
            except Exception as e:
                pass
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(element)
            )
            try:
                ActionChains(driver).move_to_element(element).pause(1).click().perform()
            except:
                element.click()
            break

def click_with_mouse(driver, selector):
    import pyautogui
    
    until_visible(driver, selector)
    elementToClick = driver.find_element(By.CSS_SELECTOR, selector)
    element_location = elementToClick.location
    element_size = elementToClick.size
    center_x = element_location['x'] + element_size['width'] / 2 + 5
    center_y = element_location['y'] + element_size['height'] / 2 + 5
    panel_height = driver.execute_script('return window.outerHeight - window.innerHeight;')
    abs_x = center_x
    y = center_y
    abs_y = y + panel_height
    pyautogui.moveTo(abs_x, abs_y, uniform(0.6, 1.7), pyautogui.easeOutQuad)
    pyautogui.click(abs_x, abs_y)

def upload_file(file, base_id, table_id, record_id):
    try:
        image_data = file
        image_name = image_data.name  # You can adjust the image format if needed
        image_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_images')
        print('1')
        # Create the directory if it doesn't exist
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, image_name)
        print(image_name)
        print(image_dir)
        print('2')
        if os.path.exists(image_path):
            os.remove(image_path)
        with open(image_path, 'wb+') as destination:
            for chunk in image_data.chunks():
                destination.write(chunk)
        print(image_path)
        print('3')
        image_url = os.path.join(settings.MEDIA_URL, 'uploaded_images', image_name).replace("\\", "/")
        airtable = Airtable(base_id, API_KEY)

        # Fetch the existing record data
        existing_record = airtable.get(table_id, record_id)
        # critical_logger.critical('existing_record')
        # Extract the existing attachments if they exist
        existing_attachments = existing_record['fields'].get('Attachment', [])
        # Define the URL of the new image you want to add
        new_image_url = 'https://ai.icn.com' + image_url
        # critical_logger.critical('url:'+new_image_url)
        # Append the new image URL to the existing attachments
        existing_attachments.append({'url': new_image_url})

        # Update the record with the combined list of attachments
        data = {
            'excel': existing_attachments
        }
        print(new_image_url)
        print('4')
        # Data to update (replace with your fields)
        print('5')
        # Update the record
        airtable.update(table_id, record_id, data)
        includes = False
        for i in range(10):
            print('try ', i)
            rec = airtable.get(table_id, record_id)
            for recImg in rec['fields'].get('Attachment', []):
                if recImg['filename'] == image_name:
                    includes = True
                    break
            if includes:
                break
            sleep(1)
        if includes:
            print('successfully')
            os.remove(image_path)
            return True
        else:
            print('failed')
            return False
    except Exception as e:
        print(e)
        print('failed2')
        return False