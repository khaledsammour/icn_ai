# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pandas as pd
import requests
import json
from time import sleep
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from rest_framework.views import APIView
from django.http import JsonResponse
from bs4 import BeautifulSoup

def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))



def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        if request.path.split('/')[-1] == 'scrap':
            scrap()
        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))



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

def getImageUrl(image_url):
    url = 'https://www.icn.com/api/v1/image/upload'
    data = {
        'image_url': image_url
    }

    try:
        # Send the POST request and wait for the response
        response = requests.post(url, data=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print('Request was successful!')
            print('Response:', response.text)  # If the response contains JSON data
            return response.text
        else:
            print('Request failed with status code:', response.status_code)
            print('Response:', response.text)
    except requests.exceptions.RequestException as e:
        print('An error occurred:', e)
jsons = [
    {
        "id": 1,
        "Name": "Oriental",
        "steps": [
            {
                "is_loop": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            }
        ],
        "attr": {
            "Arabic Name ":{
                "translate": True,
                "path": ".tb_wt_page_title_system",
                "type_type": "css"
            },
            "English Name":{
                "translate": False,
                "path": ".tb_wt_page_title_system",
                "type_type": "css"
            },
            "Arabic Description":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "English Description":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Category Id":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Arabic Brand":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "English Brand":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Unit Price":{
                "translate": False,
                "path": "//*[@id='content']/div/div/div/div/div[2][contains(@class, 'col-lg-6')]//div[contains(@class, 'price')]/*[contains(@class, 'price-regular') or contains(@class, 'price-new')]",
                "type_type": "xpath"
            },
            "Discount Type":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Discount":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Unit":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Current Stock":{
                "translate": False,
                "path": ".tb_system_product_info .tb_stock_status_in_stock",
                "type_type": "css"
            },
            "Main Image URL":{
                "translate": False,
                "path": "img.zoomImg",
                "type_type": "css",
                "is_text": False,
                "attr": "src"
            },
            "Photos URLs":{
                "translate": False,
                "path": ".mSSlideElement > li > img",
                "type_type": "css",
                "is_text": False,
                "attr": "src"
            },
            "Video Youtube URL":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "English Meta Tags":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "Arabic Meta Tags":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "features":{
                "translate": True,
                "path": ".tb_system_products .product-thumb",
                "type_type": "css"
            },
            "wholesale":{
                "translate": False,
                "path": "",
                "type_type": "",
                "value": "no"
            },
        }
    }
]

class ScrapView(APIView):
    def post(self, request, *args, **kwargs):
        # id = request.data['id']
        options = Options()
        # options.add_argument('--headless=new')
        driver = Chrome(options=options)
        driver.maximize_window()
        url = 'https://os-jo.com/product/search?category_id='+request.data['category']+'&limit=1000000000'
        driver.get(url)
        driver.execute_script("window.open('https://www.freetranslations.org/english-to-arabic-translation.html');")
        driver.switch_to.window(driver.window_handles[0])
        isExist = True
        index = 1
        data = []
        errors = []
        # while(isExist):
            # driver.get(url+'&page='+str(index))
        driver.get(url+'&page='+str(index))
        sleep(3)
        # isExist = check_if_exist(driver, ".tb_system_products .product-thumb", "products")
        elements = driver.find_elements(By.CSS_SELECTOR, ".tb_system_products .product-thumb")
        hrefs = []
        for e in elements:
            if len(e.find_elements(By.CSS_SELECTOR, '.tb_label_stock_status')) == 0:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "h4 > a").get_attribute("href"))
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one('.tb_wt_page_title_system').get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    "#content > div > div > div > div > div:nth-of-type(2) .price .price-regular, "
                    "#content > div > div > div > div > div:nth-of-type(2) .price .price-old"
                )
                price = price_elem.get_text().replace('JOD', '').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('img.zoomImg')
                
                image = getImageUrl(main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.mSSlideElement > li > img')
                images = [getImageUrl(img['src'].replace('70x70', '1200x1200')) for img in image_elems]

                # Check stock status
                in_stock = bool(soup.select(".tb_system_product_info .tb_stock_status_in_stock"))

                # Get product attributes content
                description_elem = soup.select_one(".tb_wt_product_description_system")
                product_attributes_content = description_elem.get_text(strip=True) if description_elem else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one("#content .price-savings strong")
                discount = discount_elem.get_text().replace('JOD', '').strip() if discount_elem else '0'

                product_attributes_content_json = {}
                
                product_attributes = soup.select(".tb_wt_product_attributes_system tbody > tr")
                for attr in product_attributes:
                    key = attr.select_one("td:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    product_attributes_content_json[key] = val

                # Create product dictionary
                product = {
                    "Arabic Name": translate(driver, title),
                    "English Name": title,
                    "Arabic Description": translate(driver, product_attributes_content) if len(product_attributes_content) > 3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": "5" if in_stock else "0",
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": translate(driver, keyWords).replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                # driver.get(href)
                # sleep(1)
                # # if checkProduct(href):
                # until_visible(driver, ".tb_wt_page_title_system")
                # title = driver.find_element(By.CSS_SELECTOR, ".tb_wt_page_title_system").text.strip()
                # price = driver.find_element(By.XPATH, "//*[@id='content']/div/div/div/div/div[2][contains(@class, 'col-lg-6')]//div[contains(@class, 'price')]/*[contains(@class, 'price-regular') or contains(@class, 'price-old')]").text.replace('JOD', '').strip()
                # image = getImageUrl(driver.find_element(By.CSS_SELECTOR, 'img.zoomImg').get_attribute("src"))
                # print(driver.find_element(By.CSS_SELECTOR, 'img.zoomImg'))
                # print(image)
                # images = [getImageUrl(s.get_attribute("src").replace('70x70', '1200x1200')) for s in driver.find_elements(By.CSS_SELECTOR, '.mSSlideElement > li > img')]
                # in_stock = driver.find_elements(By.CSS_SELECTOR, ".tb_system_product_info .tb_stock_status_in_stock")
                # product_attributes_content = driver.find_element(By.CSS_SELECTOR, ".tb_wt_product_description_system").text if len(driver.find_element(By.CSS_SELECTOR, ".tb_wt_product_description_system"))>0 else ''
                # keyWords = driver.find_element(By.CSS_SELECTOR, "meta[property*='og:title']").get_attribute("content")
                # discount = driver.find_element(By.XPATH, "//*[@id='content']//*[contains(@class, 'price-savings')]/strong").text.replace('JOD', '').strip() if len(driver.find_elements(By.XPATH, "//*[@id='content']//*[contains(@class, 'price-savings')]/strong"))>0 else "0"
                # product_attributes_content_json = {}
                # if len(driver.find_elements(By.XPATH,'//div/ul/li/a/span[text()="Product Specifications"]'))>0:
                #     driver.find_element(By.XPATH,'//div/ul/li/a/span[text()="Product Specifications"]').click()
                # sleep(1)
                # product_attributes = driver.find_elements(By.CSS_SELECTOR, ".tb_wt_product_attributes_system tbody > tr")
                # print(len(product_attributes))
                # for s in product_attributes:
                #     key = s.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
                #     val = s.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                #     product_attributes_content_json[key] = val


                # product = {
                #     "Arabic Name ": translate(driver, title),
                #     "English Name": title,
                #     "Arabic Description": translate(driver, product_attributes_content) if len(product_attributes_content) >3 else "يعد هذا الكمبيوتر الخيار الأمثل لأي محترف يتطلع إلى تحقيق أقصى قدر من الأداء.  مع ألواح زجاجية من الجانب والأمام لعرض أجهزتك وإضاءة RGB. يتضمن معالجًا قويًا، مما يجعله مثاليًا لتعدد المهام والألعاب. توفر ذاكرة الوصول العشوائي (RAM) تشغيلاً سلسًا وسرعات تحميل فائقة السرعة. إنه مزيج من القوة والكفاءة..",
                #     "English Description": product_attributes_content if len(product_attributes_content) >3 else "This pc is the perfect choice for any professional looking to maximize their performance.  With glass panels from the side and front to showcase your hardware and RGB lighting. Including a powerful processor, making it ideal for multitasking and gaming. The RAM provides smooth operation and lightning-fast loading speeds. It's a combination of power and efficiency..",
                #     "Category Id": request.data['db_category'],
                #     "Arabic Brand": "",
                #     "English Brand": "",
                #     "Unit Price": price,
                #     "Discount Type": "Flat" if discount != "0" else "",
                #     "Discount ": discount if discount != "0" else "",
                #     "Unit": "PC",
                #     "Current Stock": "5" if len(in_stock) > 0 else "0",
                #     "Main Image URL": image,
                #     "Photos URLs": str((",").join(images)) if len(images)>0 else image,
                #     "Video Youtube URL": "",
                #     "English Meta Tags": keyWords.replace('//',','),
                #     "Arabic Meta Tags": translate(driver, keyWords).replace('//',','),
                #     "features": '' if product_attributes_content_json == {} else json.dumps(product_attributes_content_json),
                #     "wholesale": "no",
                #     "reference_link": href,
                # }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })
        index = index + 1

        df = pd.DataFrame(data)
        df.to_excel(request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})
    

class SecScrapView(APIView):
    def post(self, request, *args, **kwargs):
        # id = request.data['id']
        options = Options()
        # options.add_argument('--headless=new')
        driver = Chrome(options=options)
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        driver.execute_script("window.open('https://www.freetranslations.org/english-to-arabic-translation.html');")
        driver.switch_to.window(driver.window_handles[0])
        isExist = True
        index = 1
        data = []
        errors = []
        # while(isExist):
            # driver.get(url+'&page='+str(index))
        driver.get(url)
        sleep(3)
        # isExist = check_if_exist(driver, ".tb_system_products .product-thumb", "products")
        elements = driver.find_elements(By.CSS_SELECTOR, ".products > div")
        hrefs = []
        for e in elements:
            hrefs.append(e.find_element(By.CSS_SELECTOR, ".image-zoom_in > a").get_attribute("href"))
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                # if checkProduct(href):
                until_visible(driver, ".product-title")
                title = driver.find_element(By.CSS_SELECTOR, ".product-title").text.strip()
                discount = driver.find_element(By.XPATH, "//div[contains(@class, 'price-wrapper')]/p/del").text.replace('JOD', '').strip() if len(driver.find_elements(By.XPATH, "//div[contains(@class, 'price-wrapper')]/p/del"))>0 else "0"
                price = driver.find_element(By.XPATH, "//div[contains(@class, 'price-wrapper')]/p/ins").text.replace('JOD', '').strip() if discount!="0" else driver.find_element(By.XPATH, "//div[contains(@class, 'price-wrapper')]/p/span/bdi").text.replace('JOD', '').strip()
                image = getImageUrl(driver.find_element(By.CSS_SELECTOR, 'figure .wp-post-image').get_attribute("src"))
                images = [getImageUrl(s.get_attribute("src").replace('-300x300', '')) for s in driver.find_elements(By.CSS_SELECTOR, '.product-thumbnails .flickity-slider > div img')]
                in_stock = driver.find_element(By.CSS_SELECTOR, ".input-text.qty.text").get_attribute("max")
                product_attributes = driver.find_elements(By.CSS_SELECTOR, ".woocommerce-product-attributes tbody > tr")
                product_attributes_content = driver.find_element(By.CSS_SELECTOR, ".woocommerce-Tabs-panel--description").text
                keyWords = driver.find_element(By.CSS_SELECTOR, "meta[property*='og:title']").get_attribute("content")
                product_attributes_content_json = {}
                for s in product_attributes:
                    if 'woocommerce-product-attributes-item--weight' not in s.get_attribute('class'):
                        key = s.find_element(By.CSS_SELECTOR, "th").text.strip()
                        val = s.find_element(By.CSS_SELECTOR, "td").text.strip()
                        product_attributes_content_json[key] = val


                product = {
                    "Arabic Name ": translate(driver, title),
                    "English Name": title,
                    "Arabic Description": translate(driver, product_attributes_content) if type(product_attributes_content) == str else "",
                    "English Description": product_attributes_content if type(product_attributes_content) == str else "",
                    "Category Id": "0",
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount ": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if len(images)>0 else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//',','),
                    "Arabic Meta Tags": translate(driver, keyWords).replace('//',','),
                    "features": json.dumps(product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })
        index = index + 1

        df = pd.DataFrame(data)
        df.to_excel('cashmere_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})

def translate(driver, text):
    driver.switch_to.window(driver.window_handles[1])
    driver.execute_script('''
        document.getElementById("InputText").value = "";
                        ''')
    until_visible_send_keys(driver, "#InputText", text)
    until_visible_click(driver, ".translate-form-control")
    sleep(3)
    # until_visible(driver, ".mttextarea")
    res = driver.find_element(By.XPATH, "//*[@id='TranslationOutput']").text
    driver.switch_to.window(driver.window_handles[0])
    return res


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


def until_visible_with_xpath(driver, element):
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

        if counter > 10:
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


def take_screen_shot(driver, name):
    # TODO: assign proper permission to the directory
    a = name
    # screenshot = driver.get_screenshot_as_png()
    # with open(name + '.png', 'wb') as f:
    #     f.write(screenshot)

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
        ActionChains(driver).move_to_element(element).pause(1).click().perform()
    except Exception as e:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            driver.execute_script("arguments[0].scrollIntoView({ block: 'end' });", element)
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

class Translator:
    def __init__(self, headless=False):
        options = Options()
        if headless: options.headless = True
        self._br = Chrome(options=options)
        self._br.get("https://www.freetranslations.org/english-to-arabic-translation.html")
        # self._br.set_page_load_timeout(25)

    def translate(self, string):
        print('string: ', string)
        if not string: return "Done"
        for i in range(3):
            try: return self._translate(string.replace("\\", ''))
            except Exception as e:
                print(e)
                sleep(2)
        raise ConnectionAbortedError

    def _translate(self, string):
        tag = self._br.find_element(By.CSS_SELECTOR,"#InputText")
        # tag.send_keys(Keys.CONTROL + "a")
        # tag.send_keys(Keys.DELETE)
        self._br.execute_script('''
            document.getElementById("InputText").value = "";
                               ''')
        tag.send_keys(string)
        self._br.find_element(By.CSS_SELECTOR, ".translate-form-control").click()
        WebDriverWait(self._br, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".mttextarea")))
        return self._br.find_element(By.XPATH, "//*[@id='TranslationOutput']").text

    def close(self):
        self._br.close()