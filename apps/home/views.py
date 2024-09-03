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
import language_tool_python
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from deep_translator import GoogleTranslator
import yake
from .googleSuggetion import api_call
import undetected_chromedriver as uc
import traceback
from openpyxl import load_workbook
import io
from django.core.files.uploadedfile import InMemoryUploadedFile

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

def save_image(image_data, file_path):
    with open(file_path, 'wb') as file:
        file.write(image_data)

def getImageBase64(driver, id, image_url):
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
    array_buffer = driver.execute_script(js_code, image_url)
    
    # Convert the ArrayBuffer to bytes
    image_data = bytes(array_buffer)        

    url = 'https://www.icn.com/api/v1/image/upload'
    files=[
        ('image',(image_url.split('/')[-1],image_data,'image/png'))
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
            print('Response:', response.text)
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
                
                image = getImageUrl(request.data['id'],main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.mSSlideElement > li > img')
                images = [getImageUrl(request.data['id'],img['src'].replace('70x70', '1200x1200')) for img in image_elems]

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
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })
        index = index + 1

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})
   
class GameakScrapView(APIView):
    def post(self, request, *args, **kwargs):
        options = Options()
        driver = Chrome(options=options)
        driver.maximize_window()
        url = request.data['url']
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'&page='+str(index))
            sleep(3)
            isExist = check_if_exist(driver, "#CollectionLoop > .product-item", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, "#CollectionLoop > .product-item")
            for e in elements:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-link").get_attribute("href"))
            index = index + 1
        
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one('h1.product__title').get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    ".product__price > span:nth-child(1)"
                )
                price = price_elem.get_text().replace('JOD', '').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('zoom-images img')
                
                image = getImageUrl(request.data['id'],main_image_elem['src'].replace('//gameakjo', 'https://gameakjo')) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('zoom-images img')
                images = [getImageUrl(request.data['id'],img['src'].replace('//gameakjo', 'https://gameakjo')) for img in image_elems]

                # Get product attributes content
                description_elem = soup.select_one(
                    ".product-extended, "
                    ".toggle-ellipsis__content > .col:nth-child(1), "
                    ".toggle-ellipsis__content"
                )
                product_attributes_content = description_elem.get_text(strip=True) if description_elem else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one(".product__price--off > span")
                discount = discount_elem.get_text().replace('%', '').strip() if discount_elem and 'hidden' not in soup.select_one(".product__price--off")['class'] else '0'

                product_attributes_content_json = {}
                
                product_attributes = soup.select(".toggle-ellipsis__content > .col:nth-child(3)")
                for attr in product_attributes:
                    key = attr.select_one("td:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    product_attributes_content_json[key] = val

                driver.get(href.replace('https://gameakjo.com/', 'https://gameakjo.com/ar/'))
                sleep(1)
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one('h1.product__title').get_text(strip=True)
                ar_description_elem = ar_soup.select_one(
                    ".product-extended, "
                    ".toggle-ellipsis__content > .col:nth-child(1), "
                    ".toggle-ellipsis__content"
                )
                ar_product_attributes_content = ar_description_elem.get_text(strip=True) if description_elem else ''
                ar_key_words_elem = ar_soup.select_one("meta[property*='og:title']")
                ar_keyWords = ar_key_words_elem['content'] if ar_key_words_elem else ''

                # Create product dictionary
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content) > 3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": " ",
                    "English Brand": " ",
                    "Unit Price": price,
                    "Discount Type": "Percent" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": "3",
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": " ",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": ar_keyWords.replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})

class PalestinianScrapView(APIView):
    def post(self, request, *args, **kwargs):
        options = Options()
        driver = Chrome(options=options)
        driver.maximize_window()
        url = request.data['url']
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'&page='+str(index))
            sleep(3)
            isExist = check_if_exist(driver, ".products-grid .product", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".products-grid .product")
            for e in elements:
                if len(e.find_elements(By.CSS_SELECTOR, '.outofstock')) == 0:
                    hrefs.append(e.find_element(By.CSS_SELECTOR, "a").get_attribute("href"))
            index = index + 1
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                until_visible_click(driver, 'header .open-menu')
                if len(driver.find_elements(By.XPATH, '//*[contains(@class, "language")]/a[contains(text(),"English")]')) > 0:
                    until_visible_xpath_click(driver, '//*[contains(@class, "language")]/a[contains(text(),"English")]')
                    until_visible(driver, '.details_content .details_name')
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one('.details_content .details_name').get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    ".details_content .details_price .theprice"
                )
                price = price_elem.get_text().strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.slick-track picture img')
                
                image = getImageUrl(request.data['id'],main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.slick-track picture img')
                images = [getImageUrl(request.data['id'],img['src']) for img in image_elems]

                # Get product attributes content
                description_elem = soup.select_one(
                    ".details_content .details_text"
                )
                product_attributes_content = description_elem.get_text(strip=True) if description_elem else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                # discount_elem = soup.select_one(".product__price--off > span")
                # discount = discount_elem.get_text().replace('%', '').strip() if discount_elem and 'hidden' not in soup.select_one(".product__price--off")['class'] else '0'

                # product_attributes_content_json = {}
                
                # product_attributes = soup.select(".toggle-ellipsis__content > .col:nth-child(3)")
                # for attr in product_attributes:
                #     key = attr.select_one("td:nth-child(1)").get_text(strip=True)
                #     val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                #     product_attributes_content_json[key] = val
                until_visible_click(driver, 'header .open-menu')
                if len(driver.find_elements(By.XPATH, '//*[contains(@class, "language")]/a[contains(text(),"العربية")]')) > 0:
                    until_visible_xpath_click(driver, '//*[contains(@class, "language")]/a[contains(text(),"العربية")]')
                    until_visible(driver, '.details_content .details_name')
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one('.details_content .details_name').get_text(strip=True)
                ar_description_elem = ar_soup.select_one(
                    ".details_content .details_text"
                )
                ar_product_attributes_content = ar_description_elem.get_text(strip=True) if description_elem else ''
                ar_key_words_elem = ar_soup.select_one("meta[property*='og:title']")
                ar_keyWords = ar_key_words_elem['content'] if ar_key_words_elem else ''

                # Create product dictionary
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content) > 3 else '',
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else '',
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": " ",
                    "English Brand": " ",
                    "Unit Price": price,
                    "Discount Type": "",
                    "Discount": "",
                    "Unit": "PC",
                    "Current Stock": "3",
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": " ",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": ar_keyWords.replace('//', ','),
                    "features": '',
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})
    
class SecScrapView(APIView):
    def post(self, request, *args, **kwargs):
        options = Options()
        driver = Chrome(options=options)
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'/page/'+str(index))
            sleep(3)
            isExist = check_if_exist(driver, ".shop-container .products > .product-small", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".shop-container .products > .product-small")
            for e in elements:
                hrefs.append(e.find_element(By.CSS_SELECTOR, ".image-zoom_in a").get_attribute("href"))
            index = index + 1

        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one('.product-main .product_title').get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    ".product-main .price-wrapper bdi"
                )
                price = price_elem.get_text().replace('JOD', '').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.product-gallery .product-images img')
                
                image = getImageUrl(request.data['id'],main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.product-gallery .product-images img')
                images = [getImageUrl(request.data['id'],img['data-large_image']) for img in image_elems]

                # Check stock status
                
                in_stock = soup.select_one(".in-stock").get_text(strip=True).replace('in stock', '').strip()
                # in_stock = soup.select_one(".quantity > input.qty")['max']

                # Get product attributes content
                # description_elem = soup.select_one("#tab-description, .product-short-description")
                # product_attributes_content = correct_spelling(description_elem.get_text(strip=True), 'en-US') if description_elem else ''
                # product_attributes_content = description_elem.encode_contents() if description_elem else ''
                # until_visible_click(driver, '#tab-description')
                product_attributes_content = driver.find_element(By.CSS_SELECTOR, '#tab-description').get_attribute('innerHTML').strip() if len(driver.find_elements(By.CSS_SELECTOR, '#tab-description'))>0 else driver.find_element(By.CSS_SELECTOR, '.product-short-description').get_attribute('innerHTML').strip() if len(driver.find_elements(By.CSS_SELECTOR, '.product-short-description'))>0 else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one(".product-main .on-sale")
                discount = discount_elem.get_text().replace('-', '').replace('%', '').strip() if discount_elem else '0'

                product_attributes_content_json = {}
                
                product_attributes = soup.select("#tab-additional_information tbody > tr")
                for attr in product_attributes:
                    if 'woocommerce-product-attributes-item--weight' not in attr['class'] and 'woocommerce-product-attributes-item--dimensions' not in attr['class']: 
                        key = attr.select_one("th:nth-child(1)").get_text(strip=True)
                        val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                        product_attributes_content_json[key] = val

                driver.get(soup.select_one(".header-language-dropdown ul > li > a[hreflang*='ar']")['href'])
                sleep(1)
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one('.product-main .product_title').get_text(strip=True) if ar_soup.select_one('.product-main .product_title') else ''
                # ar_description_elem = ar_soup.select_one(
                #     "#tab-description, .product-short-description"
                # )
                # ar_product_attributes_content = correct_spelling(ar_description_elem.get_text(strip=True), 'ar') if ar_description_elem else ''
                # ar_product_attributes_content = ar_description_elem.encode_contents() if ar_description_elem else ''
                # until_visible_click(driver, '#tab-description, .product-short-description')
                ar_product_attributes_content = driver.find_element(By.CSS_SELECTOR, '#tab-description').get_attribute('innerHTML').strip() if len(driver.find_elements(By.CSS_SELECTOR, '#tab-description'))>0 else driver.find_element(By.CSS_SELECTOR, '.product-short-description').get_attribute('innerHTML').strip() if len(driver.find_elements(By.CSS_SELECTOR, '.product-short-description'))>0 else ''
                ar_key_words_elem = ar_soup.select_one("meta[property*='og:title']")
                ar_keyWords = ar_key_words_elem['content'] if ar_key_words_elem else ''

                ar_product_attributes_content_json = {}
                
                ar_product_attributes = ar_soup.select("#tab-additional_information tbody > tr")
                for attr in ar_product_attributes:
                    if 'woocommerce-product-attributes-item--weight' not in attr['class'] and 'woocommerce-product-attributes-item--dimensions' not in attr['class']: 
                        key = attr.select_one("th:nth-child(1)").get_text(strip=True)
                        val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                        ar_product_attributes_content_json[key] = val
                # Create product dictionary
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content) > 3 else '',
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else '',
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Percent" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": ar_keyWords.replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})

class VikushaScrapView(APIView):
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
        hrefs = []
        while(isExist):
            driver.get(url+'/page/'+str(index))
            sleep(3)
            isExist = check_if_exist(driver, ".products > .instock", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".products > .instock")
            for e in elements:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a.woocommerce-LoopProduct-link").get_attribute("href"))
            index = index + 1

        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one('#main .product_title').get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    ".summary .amount"
                )
                price = price_elem.get_text().replace('د.ا', '').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.zoomImg, .svi-mainsection img')
                
                image = getImageUrl(request.data['id'],main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.woocommerce-product-gallery__wrapper > .woocommerce-product-gallery__image > a')
                images = [getImageUrl(request.data['id'],img['href']) for img in image_elems]

                # Check stock status
                
                in_stock = soup.select_one(".quantity > input.qty")['size']

                # Get product attributes content
                description_elem = soup.select_one("#tab-description")
                product_attributes_content = description_elem.get_text(separator=' ',strip=True) if description_elem else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = float(soup.select(".summary .amount")[1].get_text().replace('د.ا', '').strip()) if len(soup.select(".summary .amount"))>1 else 0
                discount = float(price) - discount_elem

                product_attributes_content_json = {}
                
                product_attributes = soup.select("#tab-additional_information tbody > tr")
                for attr in product_attributes:
                    key = attr.select_one("th:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    product_attributes_content_json[key] = val

                # Create product dictionary
                product = {
                    "Arabic Name": translate(driver, title),
                    "English Name": title,
                    "Arabic Description": translate(driver, product_attributes_content) if len(product_attributes_content) > 3 else '',
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else '',
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if str(discount_elem) != "0" else "",
                    "Discount": str(discount) if str(discount_elem) != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": translate(driver, keyWords).replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
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
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})
    
class HighTechScrapView(APIView):
    def post(self, request, *args, **kwargs):
        options = Options()
        driver = Chrome(options=options)
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        driver.execute_script("window.open('https://www.freetranslations.org/english-to-arabic-translation.html');")
        driver.switch_to.window(driver.window_handles[0])
        index = 1
        data = []
        errors = []
        hrefs = []
        driver.get(url+'?per_page=10000000')
        sleep(3)
        elements = driver.find_elements(By.CSS_SELECTOR, "aside.col-lg-9 > div > div")
        for e in elements:
            if 'Out of stock' not in e.get_attribute('innerHTML'):
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a.card-img-top").get_attribute("href"))

        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one('.page-title-overlap h1').get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    ".product-details >div.h3"
                )
                price = price_elem.get_text().replace('JOD', '').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.product-gallery .image-zoom')
                
                image = getImageUrl(request.data['id'],main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.product-gallery .image-zoom')
                images = [getImageUrl(request.data['id'],img['src']) for img in image_elems]

                # Check stock status
                
                in_stock = '3' if soup.select_one(".product-available") else '0'

                # Get product attributes content
                description_elem = soup.select_one(".page-wrapper > div.container:nth-child(5)")
                product_attributes_content = description_elem.get_text(separator=' ',strip=True) if description_elem else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = float(soup.select(".summary .amount")[1].get_text().replace('د.ا', '').strip()) if len(soup.select(".summary .amount"))>1 else 0
                discount = float(price) - discount_elem

                product_attributes_content_json = {}
                
                product_attributes = soup.select(".accordion-body > div")
                for attr in product_attributes:
                    key = attr.select_one("div:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("div:nth-child(2)").get_text(strip=True)
                    product_attributes_content_json[key] = val

                # Create product dictionary
                product = {
                    "Arabic Name": translate(driver, title),
                    "English Name": title,
                    "Arabic Description": translate(driver, product_attributes_content) if len(product_attributes_content) > 3 else '',
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else '',
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if str(discount_elem) != "0" else "",
                    "Discount": str(discount) if str(discount_elem) != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": translate(driver, keyWords).replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
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
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)

        err_df = pd.DataFrame(errors)
        err_df.to_excel('errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})

class GTSScrapView(APIView):
    def post(self, request, *args, **kwargs):
        translateDriver = Chrome()
        translateDriver.maximize_window()
        translateDriver.get('https://www.freetranslations.org/english-to-arabic-translation.html')
        driver = Chrome()
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        data = []
        errors = []
        hrefs = []
        driver.get(url.replace('?dsf=stock-status-is-in-stock', '?limit=10000000&dsf=stock-status-is-in-stock'))
        sleep(3)
        elements = driver.find_elements(By.CSS_SELECTOR, ".tb_products > .product-layout")
        for e in elements:
            hrefs.append(e.find_element(By.CSS_SELECTOR, "h4 > a").get_attribute("href"))
        # driver.execute_script("window.open('https://www.freetranslations.org/english-to-arabic-translation.html');")
        # driver.switch_to.window(driver.window_handles[0])
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                title_selector = '.tb_system_page_title > h1'
                description_selector = '.tb_product_description'
                key_words_selector = "meta[property*='og:title']"
                product_attributes_selector = ".tb_product_attributes tbody > tr"
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector).get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    "meta[property*='product:price:amount']"
                )
                price = price_elem['content'].strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.tb_gallery .tb_zoom_box img')
                
                image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.tb_gallery .tb_listing img')
                images = [getImageUrl(request.data['id'], img['src'].replace('128x128', '1200x1200')) for img in image_elems if len(img['src'])>10]

                # Check stock status
                
                in_stock = '3' if 'In Stock' in soup.select_one("meta[property*='product:availability']")['content'] else '0'

                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                # print(unwrap_divs(str(soup.select_one(description_selector).contents)))
                product_attributes_content = description_elem if description_elem and 'Previous page' not in description_elem and 'From The Manufacturer' not in description_elem.lower() else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one(".price-savings > strong")
                discount = discount_elem.get_text().replace('JOD', '').strip() if discount_elem else '0'

                product_attributes_content_json = {}
                
                product_attributes = soup.select(product_attributes_selector)
                for attr in product_attributes:
                    key = attr.select_one("td:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    product_attributes_content_json[key] = val

                driver.get(soup.select_one(".tb_wt_header_language_menu_system a[data-language-code*='ar']")['href'])
                sleep(1)
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one(title_selector).get_text(strip=True) if ar_soup.select_one(title_selector) and 'الصفحة المطلوبة لا يمكن العثور عليها' not in ar_soup.select_one(title_selector).get_text(strip=True) else title
                ar_key_words_elem = ar_soup.select_one(key_words_selector)
                ar_keyWords = ar_key_words_elem['content'] if ar_key_words_elem and 'الصفحة المطلوبة لا يمكن العثور عليها' not in ar_key_words_elem['content'] else ''

                ar_product_attributes_content_json = {}
                
                ar_product_attributes = ar_soup.select(product_attributes_selector)
                for attr in ar_product_attributes:
                    key = attr.select_one("td:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    ar_product_attributes_content_json[key] = val
                # Create product dictionary
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": translate(translateDriver, product_attributes_content) if len(product_attributes_content) > 3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": ar_keyWords.replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)

        driver.quit()
        translateDriver.quit()
        return JsonResponse({})

class TXONScrapView(APIView):
    def post(self, request, *args, **kwargs):
        translateDriver = Chrome()
        translateDriver.maximize_window()
        translateDriver.get('https://www.freetranslations.org/english-to-arabic-translation.html')
        driver = Chrome()
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        data = []
        errors = []
        hrefs = []
        index = 1
        isExist = True
        while(isExist):
            driver.get(url+'#/pageNumber=' + str(index))
            sleep(3)
            isExist = False if len(driver.find_elements(By.XPATH, "//div[contains(@class, 'ajaxFilters') and contains(@style,'display: block')]"))>0 else True
            if isExist:
                elements = driver.find_elements(By.CSS_SELECTOR, ".product-grid .product-item")
                for e in elements:
                    hrefs.append(e.find_element(By.CSS_SELECTOR, ".picture > a").get_attribute("href"))
            index = index + 1
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                title_selector = '.product-name'
                description_selector = '.full-description'
                key_words_selector = "meta[property*='og:title']"
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                available = soup.select_one(".availability").get_text(strip=True) if soup.select_one(".availability") else 'In Stock'
                if 'in stock' in available.lower():
                    title = soup.select_one(title_selector).get_text(strip=True)

                    # Get the product price
                    old_price = soup.select_one(".old-product-price > span")
                    price_elem = soup.select_one("span[itemprop*='price']")
                    price = old_price.get_text(strip=True).replace('JOD', '').strip() if old_price else price_elem['content'].strip() if price_elem else ''
                    discount = str(float(old_price.get_text(strip=True).replace('JOD', '').strip()) - float(price_elem['content'].strip())) if old_price else '0'

                    main_image_elem = soup.select_one('img.cloudzoom')
                        
                    image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''

                    # Get additional images
                    image_elems = soup.select('.slick-track > div > a')
                    images = [getImageUrl(request.data['id'], img['data-full-image-url']) for img in image_elems]

                    # Check stock status
                    
                    in_stock = '3'

                    # Get product attributes content
                    # description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    # print(unwrap_divs(str(soup.select_one(description_selector).contents)))
                    # product_attributes_content = description_elem if description_elem else ''
                    product_attributes_content = driver.find_element(By.CSS_SELECTOR, description_selector).get_attribute('innerHTML').strip() if len(driver.find_elements(By.CSS_SELECTOR, description_selector))>0 else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'] if key_words_elem else ''

                    # Create product dictionary
                    product = {
                        "Arabic Name": title,
                        "English Name": title,
                        "Arabic Description": translate(translateDriver, product_attributes_content) if len(product_attributes_content) > 3 else request.data['arabic_description'],
                        "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": price,
                        "Discount Type": "Flat" if discount != "0" else "",
                        "Discount": discount if discount != "0" else "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": keyWords.replace('//', ','),
                        "Arabic Meta Tags": translate(translateDriver, keyWords).replace('//', ','),
                        "features": '',
                        "features_ar": '',
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)

        driver.quit()
        translateDriver.quit()
        return JsonResponse({})

class CityCenterScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = Chrome()
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        data = []
        errors = []
        hrefs = []
        driver.get(url+'&limit=1000000')
        sleep(3)
        elements = driver.find_elements(By.CSS_SELECTOR, ".tb_products > .product-layout")
        for e in elements:
            if len(e.find_elements(By.CSS_SELECTOR, ".tb_label_stock_status"))==0:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "h4 > a").get_attribute("href"))
        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                title_selector = '.tb_system_page_title > h1'
                description_selector = '.tb_wt_product_field_system'
                key_words_selector = "meta[property*='og:title']"
                product_attributes_selector = ".tb_product_attributes tbody > tr"
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector).get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(
                    "meta[property*='product:price:amount']"
                )
                price = price_elem['content'].strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.tb_gallery .tb_zoom_box img')
                
                image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select('.tb_gallery .tb_listing img')
                images = [getImageUrl(request.data['id'], replace_dimensions(img['src'])) for img in image_elems if len(img['src'])>10]

                # Check stock status
                
                in_stock = '3' if 'instock' in soup.select_one("meta[property*='product:availability']")['content'] else '0'

                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one(".price-savings > strong")
                discount = discount_elem.get_text().replace('JOD', '').strip() if discount_elem else '0'

                product_attributes_content_json = {}
                ar_product_attributes_content_json = {}
                
                product_attributes = soup.select(product_attributes_selector)
                for attr in product_attributes:
                    key = attr.select_one("td:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    ar_key = str(translate(key))
                    ar_val = str(translate(val))
                    product_attributes_content_json[key] = val
                    ar_product_attributes_content_json[ar_key] = ar_val

                # Create product dictionary
                product = {
                    "Arabic Name": translate(title),
                    "English Name": title,
                    "Arabic Description": translate(product_attributes_content) if len(product_attributes_content) > 3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": translate(keyWords).replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})

class BCIScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = Chrome()
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        data = []
        errors = []
        hrefs = []
        isExist = True
        index = 1
        while (isExist):
            driver.get(url+'?p='+str(index))
            sleep(3)
            isExist = True if len(driver.find_elements(By.CSS_SELECTOR, ".product-items > .product-item"))>0 else False
            if isExist:
                elements = driver.find_elements(By.CSS_SELECTOR, ".product-items > .product-item")
                for e in elements:
                    if len(e.find_elements(By.CSS_SELECTOR, ".stock.unavailable"))==0:
                        hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-item-link").get_attribute("href"))
            index = index + 1

        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                title_selector = '*[itemprop*="name"]'
                description_selector = '*[itemprop*="description"]'
                key_words_selector = "meta[property*='og:title']"
                product_attributes_selector = ".additional-attributes > tbody > tr"
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector).get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(".product-info-main .old-price").get_text(strip=True) if soup.select_one(".product-info-main .old-price") else soup.select_one("meta[property*='product:price:amount']")['content']
                price = price_elem.strip().replace('wasJOD','').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one('.fotorama__stage *[data-active*="true"]')
                
                image = getImageUrl(request.data['id'], main_image_elem['href']) if main_image_elem else ''
                # Get additional images
                image_elems = driver.find_elements(By.CSS_SELECTOR, '.fotorama__nav__shaft > .fotorama__nav__frame')
                images = []
                for indx, i in enumerate(image_elems):
                    try:
                        until_visible_click(driver, '.fotorama__nav__shaft > .fotorama__nav__frame:nth-child('+str(indx+2)+')')
                        sleep(1)
                        mainImg = driver.find_element(By.CSS_SELECTOR, '.fotorama__stage *[data-active*="true"]')
                        images.append(getImageUrl(request.data['id'], mainImg.get_attribute('href')))
                    except Exception as e:
                        print(e)

                # Check stock status
                in_stock = '3'
                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one(".product-info-main-content .discount-percent")
                discount = discount_elem.get_text().replace('-', '').replace('%', '').strip() if discount_elem else '0'

                product_attributes_content_json = {}
                product_attributes = soup.select(product_attributes_selector)
                for attr in product_attributes:
                    key = attr.select_one("th:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    product_attributes_content_json[key] = val
                driver.get(href.replace('/en/', '/ar/'))
                sleep(1)
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                ar_key_words_elem = ar_soup.select_one(key_words_selector)
                ar_keyWords = ar_key_words_elem['content'] if ar_key_words_elem else ''
                ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                ar_product_attributes_content_json = {}
                ar_product_attributes = ar_soup.select(product_attributes_selector)
                for attr in ar_product_attributes:
                    key = attr.select_one("th:nth-child(1)").get_text(strip=True)
                    val = attr.select_one("td:nth-child(2)").get_text(strip=True)
                    ar_product_attributes_content_json[key] = val
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content) > 3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": keyWords.replace('//', ','),
                    "Arabic Meta Tags": ar_keyWords.replace('//', ','),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })

        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)

        driver.quit()
        return JsonResponse({})

class RokonBaghdadScrapView(APIView):
    def post(self, request, *args, **kwargs):
        chrome_options = Options()
        # chrome_options.page_load_strategy = 'eager'
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
        driver = Chrome(options=chrome_options)
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        data = []
        errors = []
        hrefs = []
        until_visible_click(driver, '.cookie-bar-wrap.show .btn-accept')
        while (True):
            until_visible(driver, '.search-result-middle:not(.loading)')
            elements = driver.find_elements(By.CSS_SELECTOR, ".grid-view-products .product-card")
            for e in elements:
                if len(e.find_elements(By.CSS_SELECTOR, ".badge-danger"))==0:
                    hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-image").get_attribute("href"))
            if (len(driver.find_elements(By.CSS_SELECTOR,'.pagination >li:last-child > button:not(.disabled)'))>0):
                until_visible_click(driver, '.pagination >li:last-child > button:not(.disabled)')
            else:
                break
            
        for href in hrefs:
            try:
                driver.get(href.replace('/en/', '/ar/'))
                if len(driver.find_elements(By.CSS_SELECTOR, '.section-title'))>0 and 'Page Not Found.' in driver.find_element(By.CSS_SELECTOR, '.section-title').text:
                    continue
                title_selector = 'meta[name*="title"]'
                description_selector = '#description'
                key_words_selector = "meta[property*='og:title']"
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector)['content'].strip()
                # Get the main image URL
                main_image_elem = soup.select_one('img[alt*="Product image"]')
                image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''
                # Get additional images
                image_elems = soup.select('img[alt*="Product image"]')
                images = [getImageUrl(request.data['id'], img['src']) for img in image_elems if len(img['src'])>10]
                images = [i for i in images if len(i)>10]
                # Check stock status
                in_stock = '3'
                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                keyWords = key_words_elem['content'].replace('| baghdad corner jordan','').strip() if key_words_elem else ''
                driver.get(href.replace('/ar/','/en/'))
                en_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                en_soup = BeautifulSoup(en_href_res, 'html.parser')
                # Get the product price
                price_elem = en_soup.select_one(".product-price .previous-price").get_text(strip=True) if en_soup.select_one(".product-price .previous-price") else en_soup.select_one("meta[property*='product:price:amount']")['content']
                price = price_elem.strip().replace('JOD','').replace(',', '').strip() if price_elem else ''
                # Get discount
                discount_elem = en_soup.select_one("meta[property*='product:price:amount']")['content'] if en_soup.select_one(".product-price .previous-price") else None
                discount = float(price) - float(discount_elem.strip().replace('JOD','').replace(',', '').strip()) if discount_elem else '0'
                
                keywords = extract_top_keywords(translate(product_attributes_content, dest='en'))
                ar_keywords = []
                for k in keyWords.split('//'):
                    keywords.append(k)

                for keyW in keywords:
                    ar_keywords.append(translate(keyW))
                    
                product = {
                    "Arabic Name": title,
                    "English Name": translate(title, dest='en'),
                    "Arabic Description": product_attributes_content if len(product_attributes_content)>3 else request.data['arabic_description'],
                    "English Description": translate(product_attributes_content, dest='en') if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": ','.join(keywords),
                    "Arabic Meta Tags": ','.join(ar_keywords),
                    "features": '',
                    "features_ar": '',
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })
                break

        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'].split(' '))>5 else ''
                description = changed_product_attributes_content if len(changed_product_attributes_content)>0 else product_attributes_content if len(product_attributes_content) > 3 else ''
                d['English Description'] = description
                d['Arabic Description'] = translate(description)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})

class DadaGroupScrapView(APIView):
    def post(self, request, *args, **kwargs):
        chrome_options = Options()
        # chrome_options.page_load_strategy = 'eager'
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
        driver = Chrome(options=chrome_options)
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        data = []
        errors = []
        hrefs = []
        while (True):
            try:
                until_visible(driver, '.show-more')
            except:
                pass
            if (len(driver.find_elements(By.CSS_SELECTOR,'.show-more'))>0):
                until_visible_click(driver, '.show-more')
            else:
                break
        until_visible(driver, '.container-products > .custom-product')
        elements = driver.find_elements(By.CSS_SELECTOR, ".container-products > .custom-product")
        for e in elements:
            if len(e.find_elements(By.CSS_SELECTOR, ".out-of-stock"))==0:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a").get_attribute("href"))
            
            
        for href in hrefs:
            try:
                driver.get(href.replace('?lang=ar', '?lang=en'))
                title_selector = 'meta[name*="title"]'
                description_selector = '.div-description-span'
                key_words_selector = "meta[property*='og:title']"
                product_attributes_selector = ".container-2-single > div.row-specification.desktop-view  "
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector)['content'].strip()
                # Get the product price
                price_elem = soup.select_one(".price-span").get_text(strip=True)
                price = price_elem.strip().replace('JOD','').replace(',', '').strip() if price_elem else ''
                # Get discount
                discount_elem = soup.select_one(".discount-price-span").get_text(strip=True) if soup.select_one(".discount-price-span") else None
                discount = float(discount_elem.strip().replace('JOD','').replace(',', '').strip()) - float(price.split(' ')[0]) if discount_elem else '0'
                # Get the main image URL
                main_image_elem = soup.select_one('.slider > li.slide img')
                image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''
                # Get additional images
                image_elems = soup.select('.slider > li.slide img')
                images = [getImageUrl(request.data['id'], img['src']) for img in image_elems if len(img['src'])>10]
                # Check stock status
                in_stock = '3'
                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                keywords = keyWords.split('//')
                if len(product_attributes_content)>0:
                    keywords = extract_top_keywords(product_attributes_content)
                    ar_keywords = []
                    for k in keyWords.split('//'):
                        keywords.append(k)

                    for keyW in keywords:
                        ar_keywords.append(translate(keyW))
                else:
                    ar_keywords = []
                    for keyW in keywords:
                        ar_keywords.append(translate(keyW))
                product_attributes_content_json = {}                
                product_attributes = soup.select(product_attributes_selector)
                for attr in product_attributes:
                    key = attr.select_one(".col-3-s").get_text(strip=True)
                    val = attr.select_one(".col-4-s").get_text(strip=True)
                    product_attributes_content_json[key] = val
                driver.get(href.replace('?lang=en', '?lang=ar'))
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one(title_selector)['content'].strip()
                ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if ar_soup.select_one(description_selector) else ''
                ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                ar_product_attributes_content_json = {}
                ar_product_attributes = ar_soup.select(product_attributes_selector)
                for ar_attr in ar_product_attributes:
                    key = ar_attr.select_one(".col-3-s").get_text(strip=True)
                    val = ar_attr.select_one(".col-4-s").get_text(strip=True)
                    ar_product_attributes_content_json[key] = val
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content)>3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": ','.join(keywords),
                    "Arabic Meta Tags": ','.join(ar_keywords),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                print(e)
                errors.append({
                    "url": href
                })
                break

        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})

def create_browser():
    chrome_options = Options()
    # chrome_options.page_load_strategy = 'eager'
    # chrome_options.add_argument('--blink-settings=imagesEnabled=false')
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
    driver = Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

class BashitiScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        data = []
        errors = []
        hrefs = []
        isExist = True
        index = 1
        while (isExist):
            driver.get(url+'page/'+str(index)+'/')
            sleep(3)
            isExist = True if len(driver.find_elements(By.CSS_SELECTOR, ".products > .wd-product"))>0 else False
            if isExist:
                elements = driver.find_elements(By.CSS_SELECTOR, ".products > .wd-product")
                for e in elements:
                    if len(e.find_elements(By.CSS_SELECTOR, ".out-of-stock"))==0:
                        hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-image-link").get_attribute("href"))
            index = index + 1
        error = False
        def get_details(href):
            d = [d for d in drivers if d['working'] == False][0]
            d['working'] = True
            try:
                driver = d['driver']
                driver.get(href.replace('?lang=ar', '?lang=en'))
                title_selector = '.product_title'
                description_selector = '.woocommerce-Tabs-panel--description'
                key_words_selector = "meta[property*='og:title']"
                until_visible(driver, title_selector)
                if len(driver.find_elements(By.CSS_SELECTOR, ".summary .price .amount"))==0:
                    return
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector).get_text(strip=True)
                # Get the product price
                price_elem = soup.select_one(".summary .price .amount").get_text(strip=True)
                price = price_elem.strip().replace('JOD','').replace(',', '').strip() if price_elem else ''
                # Get discount
                discount_elem = soup.select_one(".onsale.product-label").get_text(strip=True) if soup.select_one(".onsale.product-label") else None
                discount = discount_elem.replace('-','').replace('%','').strip() if discount_elem else '0'
                # Get the main image URL
                main_image_elem = soup.select_one('.wd-carousel-wrap > .wd-carousel-item img')
                image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''
                # Get additional images
                image_elems = soup.select('.wd-carousel-wrap > .wd-carousel-item img')
                images = [getImageUrl(request.data['id'], img['src']) for img in image_elems if len(img['src'])>10]
                # Check stock status
                in_stock = '3'
                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                keywords = keyWords.split('//')
                if len(product_attributes_content)>0:
                    keywords = extract_top_keywords(product_attributes_content)
                    ar_keywords = []
                    for k in keyWords.split('//'):
                        keywords.append(k)

                    for keyW in keywords:
                        ar_keywords.append(translate(keyW))
                else:
                    ar_keywords = []
                    for keyW in keywords:
                        ar_keywords.append(translate(keyW))
                driver.get(href.replace('en/', ''))
                if len(driver.find_elements(By.CSS_SELECTOR,'.page-header h3.title'))>0:
                    ar_title = translate(title)
                    ar_product_attributes_content = translate(product_attributes_content)
                else:
                    until_visible(driver, title_selector)
                    ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                    ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                    ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if ar_soup.select_one(description_selector) else ''
                    ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content)>3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "",
                    "Discount": "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": ','.join(keywords),
                    "Arabic Meta Tags": ','.join(ar_keywords),
                    "features": '',
                    "features_ar": '',
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                error = True
                print(e)
                traceback.print_exc()
                errors.append({
                    "url": href
                })
            finally:
                d['working'] = False
        executor = ThreadPoolExecutor(max_workers=9)
        
        for href in hrefs:
            if not error:
                executor.submit(get_details, href)
        executor.shutdown(wait=True)
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})

class DarwishScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        data = []
        errors = []
        hrefs = []
        isExist = True
        index = 1
        while (isExist):
            driver.get(url+'?p='+str(index))
            sleep(3)
            isExist = True if len(driver.find_elements(By.CSS_SELECTOR, ".main .products.list > .product"))>0 else False
            if isExist:
                elements = driver.find_elements(By.CSS_SELECTOR, ".main .products.list > .product")
                for e in elements:
                    if len(e.find_elements(By.CSS_SELECTOR, ".stock.unavailable"))==0:
                        hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-item-link").get_attribute("href"))
            index = index + 1
        error = False
        def get_details(driver, href):
            try:
                driver.get(href)
                title_selector = '.page-title'
                description_selector = '.product.attribute.overview'
                key_words_selector = "meta[property*='og:title']"
                product_attributes_selector = ".additional-attributes > tbody > tr"
                try:
                    until_visible(driver, 'div[data-gallery-role*="stage-shaft"] > div[href]')
                except:
                    pass
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                # Get the product price
                price = soup.select_one(".old-price .price").get_text(strip=True).replace('JOD','').replace(',','').strip() if soup.select_one(".old-price .price") else soup.select_one('.price-final_price .price').get_text(strip=True).replace('JOD','').replace(',','').strip()
                # Get discount
                discount_elem = soup.select_one('.price-final_price .price').get_text(strip=True).replace('JOD','').replace(',','').strip() if soup.select_one(".old-price .price") else None
                discount = float(price) - float(discount_elem) if discount_elem else '0'
                # Get the main image URL
                main_image_elem = soup.select_one('div[data-gallery-role*="stage-shaft"] > div[href]')
                image = getImageUrl(request.data['id'], main_image_elem['href']) if main_image_elem else ''
                # Get additional images
                image_elems = soup.select('div[data-gallery-role*="stage-shaft"] > div[href]')
                images = [getImageUrl(request.data['id'], img['href']) for img in image_elems if len(img['href'])>10]
                # Check stock status
                in_stock = '3'
                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                keywords = keyWords.split('//')
                if len(product_attributes_content)>0:
                    keywords = extract_top_keywords(product_attributes_content)
                    ar_keywords = []
                    for k in keyWords.split('//'):
                        keywords.append(k)

                    for keyW in keywords:
                        ar_keywords.append(translate(keyW))
                else:
                    ar_keywords = []
                    for keyW in keywords:
                        ar_keywords.append(translate(keyW))
                
                product_attributes_content_json = {}                
                product_attributes = soup.select(product_attributes_selector)
                for attr in product_attributes:
                    key = attr.select_one("th").get_text(strip=True)
                    val = attr.select_one("td").get_text(strip=True)
                    product_attributes_content_json[key] = val

                driver.get(href.replace('/en/', '/ar/'))
                if len(driver.find_elements(By.CSS_SELECTOR,'.page-header h3.title'))>0:
                    ar_title = translate(title)
                    ar_product_attributes_content = translate(product_attributes_content)
                else:
                    until_visible(driver, title_selector)
                    ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                    ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                    ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if ar_soup.select_one(description_selector) else ''
                    ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                    ar_product_attributes_content_json = {}
                    ar_product_attributes = ar_soup.select(product_attributes_selector)
                    for attr in ar_product_attributes:
                        key = attr.select_one("th").get_text(strip=True)
                        val = attr.select_one("td").get_text(strip=True)
                        ar_product_attributes_content_json[key] = val
                product = {
                    "Arabic Name": ar_title,
                    "English Name": title,
                    "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content)>3 else request.data['arabic_description'],
                    "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                    "Category Id": request.data['db_category'],
                    "Arabic Brand": "",
                    "English Brand": "",
                    "Unit Price": price,
                    "Discount Type": "Flat" if discount != "0" else "",
                    "Discount": discount if discount != "0" else "",
                    "Unit": "PC",
                    "Current Stock": in_stock,
                    "Main Image URL": image,
                    "Photos URLs": str((",").join(images)) if images else image,
                    "Video Youtube URL": "",
                    "English Meta Tags": ','.join(keywords),
                    "Arabic Meta Tags": ','.join(ar_keywords),
                    "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                    "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                    "wholesale": "no",
                    "reference_link": href,
                }
                data.append(product)
            except Exception as e:
                error = True
                print(e)
                traceback.print_exc()
                errors.append({
                    "url": href
                })     
        for href in hrefs:
            if not error:
                get_details(driver, href)
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})
    
class SportEquipmentScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        data = []
        errors = []
        hrefs = []
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)

        elements = driver.find_elements(By.CSS_SELECTOR, ".products > .product")
        for e in elements:
            if len(e.find_elements(By.CSS_SELECTOR, ".stock.in-stock"))>0:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-image-link").get_attribute("href"))

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    title_selector = '.product_title'
                    description_selector = '#tab-description'
                    key_words_selector = "meta[property*='og:title']"
                    product_attributes_selector = ".woocommerce-product-attributes > tbody > tr"
                    until_visible(driver, title_selector)
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                    # Get the product price
                    price = soup.select_one('.summary .price .amount > bdi').get_text(strip=True).replace('د.ا','').replace('.','').replace(',','.').strip() if len(soup.select(".summary .price .amount > bdi"))>1 else soup.select_one("meta[property*='product:price:amount']")['content']
                    # Get discount
                    discount_elem = soup.select_one("meta[property*='product:price:amount']")['content'] if len(soup.select(".summary .price .amount > bdi"))>1 and ' – ' not in str(soup.select_one('.summary .price .amount > bdi').parent.parent) else None
                    discount = float(price) - float(discount_elem) if discount_elem else '0'
                    # Get the main image URL
                    main_image_elem = soup.select_one('.wd-carousel-wrap > div > figure > a')
                    image = getImageUrl(request.data['id'], main_image_elem['href']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.wd-carousel-wrap > div > figure > a')
                    images = []
                    for img in image_elems:
                        if len(img['href'])>10:
                            res = getImageUrl(request.data['id'], img['href'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        for k in keyWords.split('//'):
                            keywords.append(k)

                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    else:
                        ar_keywords = []
                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    
                    product_attributes_content_json = {}                
                    product_attributes = soup.select(product_attributes_selector)
                    for attr in product_attributes:
                        key = attr.select_one("th").get_text(strip=True)
                        val = attr.select_one("td").get_text(strip=True)
                        product_attributes_content_json[translate(key, dest='en')] = translate(val, dest='en')

                    driver.get(href.replace('/en/', '/'))
                    if len(driver.find_elements(By.CSS_SELECTOR,'.page-header h3.title'))>0:
                        ar_title = translate(title)
                        ar_product_attributes_content = translate(product_attributes_content)
                    else:
                        until_visible(driver, title_selector)
                        ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                        ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                        ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                        ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if ar_soup.select_one(description_selector) else ''
                        ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                        ar_product_attributes_content_json = {}
                        ar_product_attributes = ar_soup.select(product_attributes_selector)
                        for attr in ar_product_attributes:
                            key = attr.select_one("th").get_text(strip=True)
                            val = attr.select_one("td").get_text(strip=True)
                            ar_product_attributes_content_json[key] = val
                    product = {
                        "Arabic Name": ar_title,
                        "English Name": title,
                        "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content)>3 else request.data['arabic_description'],
                        "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": price,
                        "Discount Type": "Flat" if discount != "0" else "",
                        "Discount": discount if discount != "0" else "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": ','.join(keywords),
                        "Arabic Meta Tags": ','.join(ar_keywords),
                        "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                        "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})

class ACIScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'/page/'+str(index))
            sleep(5)
            isExist = check_if_exist(driver, ".products > .product", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".products > .product")
            for e in elements:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-image-link").get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    if len(driver.find_elements(By.CSS_SELECTOR, '.summary .out-of-stock'))==0:
                        title_selector = '.product_title'
                        description_selector = '#tab-description'
                        key_words_selector = "meta[property*='og:title']"
                        product_attributes_selector = ".woocommerce-product-attributes > tbody > tr"
                        until_visible(driver, title_selector)
                        href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                        soup = BeautifulSoup(href_res, 'html.parser')
                        title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                        # Get the product price
                        price = soup.select('.summary .price .amount > bdi')[1].get_text(strip=True).replace('JD','').replace(',','.').strip() if len(soup.select(".summary .price .amount > bdi"))>1 else soup.select_one('.summary .price .amount > bdi').get_text(strip=True).replace('JD','').replace(',','.').strip()
                        # Get discount
                        discount_elem = soup.select_one('.onsale').get_text(strip=True).replace('%','').replace('-','').strip() if len(soup.select(".onsale"))>1 else None
                        discount = discount_elem if discount_elem else '0'
                        # Get the main image URL
                        main_image_elem = soup.select_one('.owl-stage > div.owl-item > div > figure > a')
                        image = getImageBase64(driver, request.data['id'], main_image_elem['href']) if main_image_elem else ''
                        # Get additional images
                        image_elems = soup.select('.owl-stage > div.owl-item > div > figure > a')
                        images = []
                        for img in image_elems:
                            if len(img['href'])>10:
                                res = getImageBase64(driver, request.data['id'], img['href'])
                                if res:
                                    images.append(res)
                        # Check stock status
                        in_stock = '3'
                        # Get product attributes content
                        description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                        product_attributes_content = description_elem if description_elem else ''
                        # Get keywords
                        key_words_elem = soup.select_one(key_words_selector)
                        keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                        keywords = keyWords.split('//')
                        if len(product_attributes_content)>0:
                            keywords = extract_top_keywords(product_attributes_content)
                            ar_keywords = []
                            for k in keyWords.split('//'):
                                keywords.append(k)

                            for keyW in keywords:
                                ar_keywords.append(translate(keyW))
                        else:
                            ar_keywords = []
                            for keyW in keywords:
                                ar_keywords.append(translate(keyW))
                        
                        product_attributes_content_json = {}                
                        product_attributes = soup.select(product_attributes_selector)
                        for attr in product_attributes:
                            key = attr.select_one("th").get_text(strip=True)
                            val = attr.select_one("td").get_text(strip=True)
                            product_attributes_content_json[translate(key, dest='en')] = translate(val, dest='en')

                        driver.get(href.replace('/en/', '/'))
                        if len(driver.find_elements(By.CSS_SELECTOR,'.page-header h3.title'))>0:
                            ar_title = translate(title)
                            ar_product_attributes_content = translate(product_attributes_content)
                        else:
                            until_visible(driver, title_selector)
                            ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                            ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                            ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                            ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if ar_soup.select_one(description_selector) else ''
                            ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                            ar_product_attributes_content_json = {}
                            ar_product_attributes = ar_soup.select(product_attributes_selector)
                            for attr in ar_product_attributes:
                                key = attr.select_one("th").get_text(strip=True)
                                val = attr.select_one("td").get_text(strip=True)
                                ar_product_attributes_content_json[key] = val
                        product = {
                            "Arabic Name": ar_title,
                            "English Name": title,
                            "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content)>3 else request.data['arabic_description'],
                            "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                            "Category Id": request.data['db_category'],
                            "Arabic Brand": "",
                            "English Brand": "",
                            "Unit Price": price,
                            "Discount Type": "Flat" if discount != "0" else "",
                            "Discount": discount if discount != "0" else "",
                            "Unit": "PC",
                            "Current Stock": in_stock,
                            "Main Image URL": image,
                            "Photos URLs": str((",").join(images)) if images else image,
                            "Video Youtube URL": "",
                            "English Meta Tags": ','.join(keywords),
                            "Arabic Meta Tags": ','.join(ar_keywords),
                            "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                            "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                            "wholesale": "no",
                            "reference_link": href,
                        }
                        data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})

class DiamondStarScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'/page/'+str(index))
            sleep(5)
            isExist = check_if_exist(driver, ".products > .product", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".products > .product")
            for e in elements:
                if len(e.find_elements(By.CSS_SELECTOR, '.out-of-stock'))==0:
                    hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-image-link").get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    title_selector = '.product_title'
                    description_selector = '#tab-description'
                    key_words_selector = "meta[property*='og:title']"
                    product_attributes_selector = ".woocommerce-product-attributes > tbody > tr"
                    try: 
                        until_visible(driver, title_selector)
                    except: 
                        continue
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    if len(soup.select('.summary .price .amount > bdi'))==0:
                        continue
                    title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                    # Get the product price
                    price = soup.select('.summary .price .amount > bdi')[1].get_text(strip=True).replace('JD','').replace(',','').strip() if len(soup.select(".summary .price .amount > bdi"))>1 else soup.select_one('.summary .price .amount > bdi').get_text(strip=True).replace('JD','').replace(',','').strip()
                    # Get discount
                    discount_elem = soup.select_one('.summary .berocket_better_labels_position_left .berocket_better_labels_line .b_span_text').get_text(strip=True).replace('%','').replace('-','').strip() if len(soup.select(".summary .berocket_better_labels_position_left .berocket_better_labels_line .b_span_text"))>1 else None
                    discount = discount_elem if discount_elem else '0'
                    # Get the main image URL
                    main_image_elem = soup.select_one('.owl-stage > div.owl-item > div > figure > a')
                    image = getImageBase64(driver, request.data['id'], main_image_elem['href']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.owl-stage > div.owl-item > div > figure > a')
                    images = []
                    for img in image_elems:
                        if len(img['href'])>10:
                            res = getImageBase64(driver, request.data['id'], img['href'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        for k in keyWords.split('//'):
                            keywords.append(k)

                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    else:
                        ar_keywords = []
                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    
                    product_attributes_content_json = {}                
                    product_attributes = soup.select(product_attributes_selector)
                    for attr in product_attributes:
                        key = attr.select_one("th").get_text(strip=True)
                        val = attr.select_one("td").get_text(strip=True)
                        product_attributes_content_json[translate(key, dest='en')] = translate(val, dest='en')

                    driver.get(href.replace('/en/', '/'))
                    if len(driver.find_elements(By.CSS_SELECTOR,'.page-header h3.title'))>0:
                        ar_title = translate(title)
                        ar_product_attributes_content = translate(product_attributes_content)
                    else:
                        until_visible(driver, title_selector)
                        ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                        ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                        ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                        ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if ar_soup.select_one(description_selector) else ''
                        ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
                        ar_product_attributes_content_json = {}
                        ar_product_attributes = ar_soup.select(product_attributes_selector)
                        for attr in ar_product_attributes:
                            key = attr.select_one("th").get_text(strip=True)
                            val = attr.select_one("td").get_text(strip=True)
                            ar_product_attributes_content_json[key] = val
                    product = {
                        "Arabic Name": ar_title,
                        "English Name": title,
                        "Arabic Description": ar_product_attributes_content if len(ar_product_attributes_content)>3 else request.data['arabic_description'],
                        "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": price,
                        "Discount Type": "Percent" if discount != "0" else "",
                        "Discount": discount if discount != "0" else "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": ','.join(keywords),
                        "Arabic Meta Tags": ','.join(ar_keywords),
                        "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                        "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})  

class AlrefaiScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'&page='+str(index))
            sleep(3)
            isExist = check_if_exist(driver, ".products-grid .product", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".products-grid .product")
            for e in elements:
                if len(e.find_elements(By.CSS_SELECTOR, '.outofstock')) == 0:
                    hrefs.append(e.find_element(By.CSS_SELECTOR, "a").get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    until_visible_click(driver, 'header .open-menu')
                    if len(driver.find_elements(By.XPATH, '//*[contains(@class, "language")]/a[contains(text(),"English")]')) > 0:
                        until_visible_xpath_click(driver, '//*[contains(@class, "language")]/a[contains(text(),"English")]')
                        until_visible(driver, '.details_content .details_name')
                    title_selector = '.details_content .details_name'
                    description_selector = '.details_content .details_text'
                    key_words_selector = "meta[property*='og:title']"
                    until_visible(driver, title_selector)
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                    # Get the product price
                    price = soup.select_one('.details_content .details_discount .theoldprice').get_text(strip=True).replace('JD','').replace(',','').strip() if len(soup.select(".details_content .details_discount .theoldprice"))>0 and soup.select_one('.details_content .details_discount .theoldprice').get_text(strip=True).replace('JD','').replace(',','').strip() != '' else soup.select_one('.details_content .details_price .theprice').get_text(strip=True).replace('JD','').replace(',','').strip() if len(soup.select(".details_content .details_price .theprice"))>0 else ''
                    # Get discount
                    discount_elem = soup.select_one('.details_content .details_price .theprice').get_text(strip=True).replace('%','').replace('-','').strip() if len(soup.select(".details_content .details_discount .theoldprice"))>0 and soup.select_one('.details_content .details_discount .theoldprice').get_text(strip=True).replace('JD','').replace(',','.').strip() != '' and len(soup.select(".details_content .details_price .theprice"))>0 else None
                    discount = discount_elem if discount_elem else '0'
                    # Get the main image URL
                    main_image_elem = soup.select_one('.slick-track picture img')
                    image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.slick-track picture img')
                    images = []
                    for img in image_elems:
                        if len(img['src'])>10:
                            res = getImageUrl(request.data['id'], img['src'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        for k in keyWords.split('//'):
                            keywords.append(k)

                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    else:
                        ar_keywords = []
                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    
                    if len(soup.select('.additions .addition'))>0:
                        prices = soup.select('.additions .addition')
                        for pr in prices:
                            softfix = pr.select_one('.addition-name').get_text(strip=True)
                            price = pr.select_one('.addition-price').get_text(strip=True).replace('+','').replace('JOD','').strip()
                            new_title = title + ' - ' + softfix
                            product = {
                            "Arabic Name": new_title,
                            "English Name": translate(new_title, dest='en'),
                            "Arabic Description": product_attributes_content if len(product_attributes_content)>3 else request.data['arabic_description'],
                            "English Description": translate(product_attributes_content, dest='en') if len(product_attributes_content) > 3 else request.data['description'],
                            "Category Id": request.data['db_category'],
                            "Arabic Brand": "",
                            "English Brand": "",
                            "Unit Price": price,
                            "Discount Type": "Flat" if discount != "0" else "",
                            "Discount": discount if discount != "0" else "",
                            "Unit": "PC",
                            "Current Stock": in_stock,
                            "Main Image URL": image,
                            "Photos URLs": str((",").join(images)) if images else image,
                            "Video Youtube URL": "",
                            "English Meta Tags": ','.join(keywords),
                            "Arabic Meta Tags": ','.join(ar_keywords),
                            "features": '',
                            "features_ar": '',
                            "wholesale": "no",
                            "reference_link": href,
                            }
                            data.append(product)
                    else:
                        unit = soup.select_one('.details_price .unit').get_text(strip=True) if len(soup.select('.details_price .unit'))>0 else ''
                        product = {
                            "Arabic Name": f'{title} {' - ' +unit}',
                            "English Name": translate(f'{title} {' - ' +unit}', dest='en'),
                            "Arabic Description": product_attributes_content if len(product_attributes_content)>3 else request.data['arabic_description'],
                            "English Description": translate(product_attributes_content, dest='en') if len(product_attributes_content) > 3 else request.data['description'],
                            "Category Id": request.data['db_category'],
                            "Arabic Brand": "",
                            "English Brand": "",
                            "Unit Price": price,
                            "Discount Type": "Flat" if discount != "0" else "",
                            "Discount": discount if discount != "0" else "",
                            "Unit": "PC",
                            "Current Stock": in_stock,
                            "Main Image URL": image,
                            "Photos URLs": str((",").join(images)) if images else image,
                            "Video Youtube URL": "",
                            "English Meta Tags": ','.join(keywords),
                            "Arabic Meta Tags": ','.join(ar_keywords),
                            "features": '',
                            "features_ar": '',
                            "wholesale": "no",
                            "reference_link": href,
                        }
                        data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})  
    
class NumberOneScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            driver.get(url+'?page='+str(index))
            sleep(3)
            isExist = check_if_exist(driver, ".main-products > .product-layout", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".main-products > .product-layout:not(.out-of-stock)")
            for e in elements:
                hrefs.append(e.find_element(By.CSS_SELECTOR, "a.product-img").get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    title_selector = '.page-title'
                    description_selector = '.short_description'
                    key_words_selector = "meta[property*='og:title']"
                    until_visible(driver, title_selector)
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                    # Get the product price
                    price = soup.select_one('.product-price-old').get_text(strip=True).replace('JOD','').replace(',','').strip() if len(soup.select(".product-info .product-labels > span:last-child > b"))>0 and soup.select_one('.product-info .product-labels > span:last-child > b').get_text(strip=True).replace('%','').replace('-','.').strip() != '' else soup.select_one('.product-price').get_text(strip=True).replace('JOD','').replace(',','').strip() if len(soup.select(".product-price"))>0 else ''
                    # Get discount
                    discount_elem = soup.select_one('.product-info .product-labels > span:last-child > b').get_text(strip=True).replace('%','').replace('-','').strip() if len(soup.select(".product-info .product-labels > span:last-child > b"))>0 else None
                    discount = discount_elem if discount_elem else '0'
                    # Get the main image URL
                    main_image_elem = soup.select_one('.product-info .main-image .swiper-wrapper .swiper-slide img')
                    image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.product-info .main-image .swiper-wrapper .swiper-slide img')
                    images = []
                    for img in image_elems:
                        if len(img['src'])>10:
                            res = getImageUrl(request.data['id'], img['src'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        for k in keyWords.split('//'):
                            keywords.append(k)

                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    else:
                        ar_keywords = []
                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    
                    product = {
                        "Arabic Name": translate(title),
                        "English Name": title,
                        "Arabic Description": translate(product_attributes_content) if len(product_attributes_content)>3 else request.data['arabic_description'],
                        "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": price,
                        "Discount Type": "Percent" if discount != "0" else "",
                        "Discount": discount if discount != "0" else "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": ','.join(keywords),
                        "Arabic Meta Tags": ','.join(ar_keywords),
                        "features": '',
                        "features_ar": '',
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})  

class DermacolScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            if index != 1:
                driver.get(url+str(index)+'/')
            sleep(3)
            isExist = check_if_exist(driver, ".c-products__list > .c-products__item a", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".c-products__list > .c-products__item a")
            for e in elements:
                hrefs.append(e.get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    title_selector = '.h2.b-detail-desc__title'
                    key_words_selector = "meta[property*='og:title']"
                    if len(driver.find_elements(By.CSS_SELECTOR, title_selector))==0:
                        continue
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    title = translate(soup.select_one(title_selector).get_text(strip=True), dest='en')
                    if 'ml' not in title and len(soup.select('.b-detail-desc__unit strong'))>0:
                        title += ' ' + soup.select_one('.b-detail-desc__unit strong').get_text(strip=True)
                    # Get the main image URL
                    main_image_elem = soup.select_one('.slick-track > li > a')
                    image = getImageUrl(request.data['id'], 'https://www.dermacol.com.ar/'+main_image_elem['href']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.slick-track > li > a')
                    images = []
                    for img in image_elems:
                        if len(img['href'])>10:
                            res = getImageUrl(request.data['id'], 'https://www.dermacol.com.ar/'+img['href'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    descs = soup.select('.grid:nth-child(2) > .grid__cell > .b-content:not(.hide-mobile-up)')
                    product_attributes_content = '<div class="row">'
                    for desc in descs:
                        product_attributes_content += '<div class="col-6">'
                        product_attributes_content += '<h2 style="font-weight: bold;">' + desc.select_one('h2').get_text(strip=True) + '</h2>'
                        product_attributes_content += '<p>' + desc.get_text(strip=True).replace(desc.select_one('h2').get_text(strip=True), '') + '</p>'
                        product_attributes_content += '</div>'
                    product_attributes_content += '</div>'
                    # description_elem = soup.select_one(description_selector).get_text("\n",strip=True) if soup.select_one(description_selector) else ''
                    # product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    ar_keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        ar_keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        keywords = []
                        for k in keyWords.split('//'):
                            ar_keywords.append(k)

                        for keyW in ar_keywords:
                            keywords.append(translate(keyW, dest='en'))
                    else:
                        keywords = []
                        for keyW in keywords:
                            keywords.append(translate(keyW, dest='en'))
                    
                    product = {
                        "Arabic Name": 'Dermacol - ' + translate(title),
                        "English Name": 'Dermacol - ' + title,
                        "Arabic Description": product_attributes_content if len(product_attributes_content)>3 else request.data['arabic_description'],
                        "English Description": translate(product_attributes_content,dest='en') if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": "0",
                        "Discount Type": "",
                        "Discount": "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": ','.join(keywords),
                        "Arabic Meta Tags": ','.join(ar_keywords),
                        "features": '',
                        "features_ar": '',
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            
        driver.quit()
        return JsonResponse({})  
  
class UpdateStoreScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            if index != 1:
                driver.get(url+'page/'+str(index)+'/')
            sleep(3)
            isExist = check_if_exist(driver, ".products > .wd-product a.product-image-link", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".products > .wd-product a.product-image-link")
            for e in elements:
                hrefs.append(e.get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    title_selector = '.product_title'
                    key_words_selector = "meta[property*='og:title']"
                    description_selector = 'div.single-product-page > div > section:nth-child(4) .elementor-widget-wrap'
                    if len(driver.find_elements(By.CSS_SELECTOR, title_selector))==0:
                        continue
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    title = soup.select_one(title_selector).get_text(strip=True)
                    # Get the product price
                    price = soup.select_one('meta[property*="product:price:amount"]')['content'] if len(soup.select('meta[property*="product:price:amount"]'))>0 else ''
                    # Get discount
                    discount_elem = soup.select_one('div.single-product-page > div > section:nth-child(2) .onsale').get_text(strip=True).replace('%','').replace('-','').strip() if len(soup.select("div.single-product-page > div > section:nth-child(2) .onsale"))>0 else None
                    discount = discount_elem if discount_elem else '0'
                    # Get the main image URL
                    main_image_elem = soup.select_one('.woocommerce-product-gallery__wrapper > .wd-carousel-wrap > div > figure > a')
                    image = getImageUrl(request.data['id'], main_image_elem['href']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.woocommerce-product-gallery__wrapper > .wd-carousel-wrap > div > figure > a')
                    images = []
                    for img in image_elems:
                        if len(img['href'])>10:
                            res = getImageUrl(request.data['id'], img['href'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        for k in keyWords.split('//'):
                            keywords.append(k)

                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    else:
                        ar_keywords = []
                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    
                    product_attributes_content_json = {}                
                    ar_product_attributes_content_json = {}                
                    product_attributes = soup.select('div.single-product-page > div > section:nth-child(5) .elementor-widget-wrap table > tbody > tr')
                    for attr in product_attributes:
                        key = attr.select_one("th").get_text(strip=True)
                        val = attr.select_one("td").get_text(strip=True)
                        ar_product_attributes_content_json[translate(key)] = translate(val)
                        product_attributes_content_json[key] = val
                    product = {
                        "Arabic Name": translate(title),
                        "English Name": title,
                        "Arabic Description": translate(product_attributes_content) if len(product_attributes_content)>3 else request.data['arabic_description'],
                        "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": price,
                        "Discount Type": "Percent" if discount != "0" else "",
                        "Discount": discount if discount != "0" else "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": ','.join(keywords),
                        "Arabic Meta Tags": ','.join(ar_keywords),
                        "features": '' if not product_attributes_content_json else json.dumps(product_attributes_content_json),
                        "features_ar": '' if not ar_product_attributes_content_json else json.dumps(ar_product_attributes_content_json),
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
            
        driver.quit()
        return JsonResponse({})  

class TahboubScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = create_browser()
        url = request.data['url']
        driver.get(url)
        sleep(1)
        isExist = True
        index = 1
        data = []
        errors = []
        hrefs = []
        while(isExist):
            if index != 1:
                driver.get(url+'?page='+str(index))
            sleep(3)
            isExist = check_if_exist(driver, ".product-list > .product-item a.product-item__title.link", "products")
            elements = driver.find_elements(By.CSS_SELECTOR, ".product-list > .product-item a.product-item__title.link")
            for e in elements:
                hrefs.append(e.get_attribute("href"))
            index = index + 1

        error = False
        for href in hrefs:
            if not error:
                try:
                    driver.get(href)
                    sleep(1)
                    title_selector = '.product-meta__title '
                    key_words_selector = "meta[property*='og:title']"
                    description_selector = '.product-block-list__item--description .card__section'
                    until_visible(driver, '.product-gallery__carousel .product-gallery__carousel-item img')
                    if len(driver.find_elements(By.CSS_SELECTOR, title_selector))==0:
                        continue
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    title = soup.select_one(title_selector).get_text(strip=True)
                    # Get the product price
                    price = soup.select_one('.product-block-list__item--info .price-list > .price.price--compare').get_text(strip=True).replace('JD','').replace(',','').strip() if len(soup.select('.product-block-list__item--info .price-list > .price.price--compare'))>0 else ''
                    # Get discount
                    discount_elem = soup.select_one('.product-block-list__item--info .product-label--on-sale > span').get_text(strip=True).replace('JD','').replace('-','').strip() if len(soup.select(".product-block-list__item--info .product-label--on-sale > span"))>0 else None
                    discount = discount_elem if discount_elem else '0'
                    # Get the main image URL
                    main_image_elem = soup.select_one('.product-gallery__carousel .product-gallery__carousel-item >div > div > img')
                    image = getImageUrl(request.data['id'], 'https:'+main_image_elem['data-zoom']) if main_image_elem else ''
                    # Get additional images
                    image_elems = soup.select('.product-gallery__carousel .product-gallery__carousel-item >div > div > img')
                    images = []
                    for img in image_elems:
                        print(img)
                        if len(img['data-zoom'])>10:
                            res = getImageUrl(request.data['id'], 'https:'+img['data-zoom'])
                            if res:
                                images.append(res)
                    # Check stock status
                    in_stock = '3'
                    # Get product attributes content
                    description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                    product_attributes_content = description_elem if description_elem else ''
                    # Get keywords
                    key_words_elem = soup.select_one(key_words_selector)
                    keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                    keywords = keyWords.split('//')
                    if len(product_attributes_content)>0:
                        keywords = extract_top_keywords(product_attributes_content)
                        ar_keywords = []
                        for k in keyWords.split('//'):
                            keywords.append(k)

                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    else:
                        ar_keywords = []
                        for keyW in keywords:
                            ar_keywords.append(translate(keyW))
                    
                    # product_attributes_content_json = {}                
                    # ar_product_attributes_content_json = {}                
                    # product_attributes = soup.select('div.single-product-page > div > section:nth-child(5) .elementor-widget-wrap table > tbody > tr')
                    # for attr in product_attributes:
                    #     key = attr.select_one("th").get_text(strip=True)
                    #     val = attr.select_one("td").get_text(strip=True)
                    #     ar_product_attributes_content_json[translate(key)] = translate(val)
                    #     product_attributes_content_json[key] = val
                    product = {
                        "Arabic Name": translate(title),
                        "English Name": title,
                        "Arabic Description": translate(product_attributes_content) if len(product_attributes_content)>3 else request.data['arabic_description'],
                        "English Description": product_attributes_content if len(product_attributes_content) > 3 else request.data['description'],
                        "Category Id": request.data['db_category'],
                        "Arabic Brand": "",
                        "English Brand": "",
                        "Unit Price": price,
                        "Discount Type": "Flat" if discount != "0" else "",
                        "Discount": discount if discount != "0" else "",
                        "Unit": "PC",
                        "Current Stock": in_stock,
                        "Main Image URL": image,
                        "Photos URLs": str((",").join(images)) if images else image,
                        "Video Youtube URL": "",
                        "English Meta Tags": ','.join(keywords),
                        "Arabic Meta Tags": ','.join(ar_keywords),
                        "features": '',
                        "features_ar": '',
                        "wholesale": "no",
                        "reference_link": href,
                    }
                    data.append(product)
                except Exception as e:
                    error = True
                    print(e)
                    traceback.print_exc()
                    errors.append({
                        "url": href
                    })   
        if len(errors)>0:
            err_df = pd.DataFrame(errors)
            err_df.to_excel('excel/'+request.data['db_category']+'_errors.xlsx', index=False)
        else:
            df = pd.DataFrame(data)
            df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
            driver.get('https://www.scribbr.com/paraphrasing-tool/')
            until_visible(driver, '#QuillBotPphrIframe')
            iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
            driver.get(iframe.get_attribute('src'))
            for d in data:
                changed_product_attributes_content = change_text(driver, d['English Description']) if len(d['English Description'])>5 and d['English Description'] != request.data['description'] else ''
                if len(changed_product_attributes_content)>5:
                    d['English Description'] = changed_product_attributes_content
                    d['Arabic Description'] = translate(changed_product_attributes_content)
            df = pd.DataFrame(data)
            df.to_excel('excel/new_'+request.data['db_category']+'_products.xlsx', index=False)
            
        driver.quit()
        return JsonResponse({})  
  
class DelfyScrapView(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        brand = request.data['brand']
        title_selector = request.data['title_selector']
        description_selector = request.data['description_selector']
        image_selector = request.data['image_selector']
        image_attr = request.data['image_attr']
        store_id = request.data['id']
        key_words_selector = "meta[property*='og:title']"
        if not file or not isinstance(file, InMemoryUploadedFile):
            return JsonResponse({"error": "No file provided or invalid file"})
        
        try:
            # Read the file and load it into openpyxl
            file_content = file.read()
            file_name = file.name
            wb = load_workbook(filename=io.BytesIO(file_content))
            sheet = wb.active
            
            # Process the Excel file (example: read cell values)
            headers = [str(cell.value).strip() for cell in sheet[1]]
            
            # Process the Excel file and format data as an array of objects
            excel_data = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if all(cell is None for cell in row):
                    continue  # Skip empty rows
                row_data = {headers[i]: row[i] for i in range(len(headers))}
                excel_data.append(row_data)

            # You can process or save the data as needed
            driver = create_browser()
            sleep(1)
            data = []
            errors = []
            error = False
            for d in excel_data:
                href = d['LINK']
                price = d['price']
                category = d['category  ID']
                if not error:
                    try:
                        driver.get(href)
                        sleep(1)
                        until_visible(driver, image_selector)
                        href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                        soup = BeautifulSoup(href_res, 'html.parser')
                        title = soup.select_one(title_selector).get_text(strip=True)
                        # Get the main image URL
                        main_image_elem = soup.select_one(image_selector)
                        image = getImageUrl(store_id, main_image_elem[image_attr]) if main_image_elem else ''
                        # Get additional images
                        image_elems = soup.select(image_selector)
                        images = []
                        for img in image_elems:
                            if len(img[image_attr])>10:
                                res = getImageUrl(store_id, img[image_attr])
                                print(img[image_attr])
                                print(res)
                                if res:
                                    images.append(res)
                        description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                        product_attributes_content = description_elem if description_elem else ''
                        # Get keywords
                        key_words_elem = soup.select_one(key_words_selector)
                        keyWords = key_words_elem['content'].strip() if key_words_elem else ''
                        keywords = keyWords.split('//')
                        if len(product_attributes_content)>0:
                            keywords = extract_top_keywords(product_attributes_content)
                            ar_keywords = []
                            for k in keyWords.split('//'):
                                keywords.append(k)

                            for keyW in keywords:
                                ar_keywords.append(translate(keyW))
                        else:
                            ar_keywords = []
                            for keyW in keywords:
                                ar_keywords.append(translate(keyW))
                        
                        product = {
                            "Arabic Name": brand + ' ' + translate(title),
                            "English Name": brand + ' ' + title,
                            "Arabic Description": translate(product_attributes_content) if len(product_attributes_content)>3 else '',
                            "English Description": product_attributes_content if len(product_attributes_content) > 3 else '',
                            "Category Id": category,
                            "Arabic Brand": "",
                            "English Brand": "",
                            "Unit Price": price,
                            "Discount Type": "",
                            "Discount": "",
                            "Unit": "PC",
                            "Current Stock": '3',
                            "Main Image URL": image,
                            "Photos URLs": str((",").join(images)) if images else image,
                            "Video Youtube URL": "",
                            "English Meta Tags": ','.join(keywords),
                            "Arabic Meta Tags": ','.join(ar_keywords),
                            "features": '',
                            "features_ar": '',
                            "wholesale": "no",
                            "reference_link": href,
                        }
                        data.append(product)
                    except Exception as e:
                        error = True
                        print(e)
                        traceback.print_exc()
                        errors.append({
                            "url": href
                        })   
            if len(errors)>0:
                err_df = pd.DataFrame(errors)
                err_df.to_excel('excel/'+file_name+'_errors.xlsx', index=False)
            else:
                df = pd.DataFrame(data)
                df.to_excel('excel/'+file_name+'_products.xlsx', index=False)
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
                df.to_excel('excel/new_'+file_name+'_products.xlsx', index=False)
                
            driver.quit()
            return JsonResponse({})  
        except Exception as e:
            return JsonResponse({"error": str(e)})
  
class TemuScrapView(APIView):
    def post(self, request, *args, **kwargs):
        driver = uc.Chrome(use_subprocess=False)
        url = request.data['url']
        driver.get(url)
        sleep(1)
        data = []
        errors = []
        hrefs = []
        until_visible(driver, '.js-goods-list > div > div a')
        elements = driver.find_elements(By.CSS_SELECTOR, ".js-goods-list > div > div")
        for e in elements:
            if len(e.find_elements(By.CSS_SELECTOR, "a"))>0:
                e.click()
                sleep(5)
                try:
                    driver.switch_to.window(driver.window_handles[1])
                    until_visible_with_xpath(driver, "//div[contains(@aria-label, 'reviews from Jordan')]")
                    href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                    soup = BeautifulSoup(href_res, 'html.parser')
                    if len(soup.select("div[aria-label*='reviews from Jordan'] span")) == 0:
                        return
                    title = soup.select_one("meta[name*='title']")['content']
                    desc = soup.select_one("meta[name*='description']")['content']
                    in_stock = soup.select_one("div[aria-label*='reviews from Jordan'] span").get_text(strip=True).replace('(','').replace(')','').strip()

                    product = {
                        "Name": title,
                        "Description": desc,
                        "Sells": in_stock,
                        "reference_link": driver.current_url,
                    }
                    data.append(product)
                except Exception as e:
                    traceback.print_exc()
                    errors.append({
                        "url": driver.current_url,
                    })
                finally:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
        data.sort(key=lambda x: int(x['Sells']), reverse=True)
        df = pd.DataFrame(data)
        df.to_excel('excel/'+request.data['db_category']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})
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
    return emoji_pattern.sub(r'', string)
class ChangeText(APIView):
    def post(self, request, *args, **kwargs):
        chrome_options = Options()
        # chrome_options.page_load_strategy = 'eager'
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
        # chrome_options.add_argument('--headless')
        driver = Chrome(options=chrome_options)
        driver.maximize_window()
        driver.get('https://www.scribbr.com/paraphrasing-tool/')
        until_visible(driver, '#QuillBotPphrIframe')
        iframe = driver.find_element(By.CSS_SELECTOR, "#QuillBotPphrIframe")
        driver.get(iframe.get_attribute('src'))
        dataframe1 = pd.read_excel('excel/'+request.data['id']+'_products.xlsx')
        products = []
        for index, row in dataframe1.iterrows():
            data = row.to_dict()
            if data['English Description'] != ' ':
                new_desc = change_text(driver, translate(remove_emoji(data['English Description']), dest='en'))
                ar_new_desc = translate(new_desc)
                products.append({
                    "Arabic Name": data['Arabic Name'],
                    "English Name": data['English Name'],
                    "Arabic Description": ar_new_desc if len(ar_new_desc)>0 else data['Arabic Description'],
                    "English Description": new_desc if len(new_desc)>0 else data['English Description'],
                    "Category Id": data['Category Id'],
                    "Arabic Brand": data['Arabic Brand'],
                    "English Brand": data['English Brand'],
                    "Unit Price": data['Unit Price'],
                    "Discount Type": data['Discount Type'],
                    "Discount": data['Discount'],
                    "Unit": data['Unit'],
                    "Current Stock": data['Current Stock'],
                    "Main Image URL": data['Main Image URL'],
                    "Photos URLs": data['Photos URLs'],
                    "Video Youtube URL": data['Video Youtube URL'],
                    "English Meta Tags": data['English Meta Tags'],
                    "Arabic Meta Tags": data['Arabic Meta Tags'],
                    "features": data['features'],
                    "features_ar": data['features_ar'],
                    "wholesale": data['wholesale'],
                    "reference_link": data['reference_link'],
                })
            else: 
                products.append({
                    "Arabic Name": data['Arabic Name'],
                    "English Name": data['English Name'],
                    "Arabic Description": data['Arabic Description'],
                    "English Description": data['English Description'],
                    "Category Id": data['Category Id'],
                    "Arabic Brand": data['Arabic Brand'],
                    "English Brand": data['English Brand'],
                    "Unit Price": data['Unit Price'],
                    "Discount Type": data['Discount Type'],
                    "Discount": data['Discount'],
                    "Unit": data['Unit'],
                    "Current Stock": data['Current Stock'],
                    "Main Image URL": data['Main Image URL'],
                    "Photos URLs": data['Photos URLs'],
                    "Video Youtube URL": data['Video Youtube URL'],
                    "English Meta Tags": data['English Meta Tags'],
                    "Arabic Meta Tags": data['Arabic Meta Tags'],
                    "features": data['features'],
                    "features_ar": data['features_ar'],
                    "wholesale": data['wholesale'],
                    "reference_link": data['reference_link'],
                })

        df = pd.DataFrame(products)
        df.to_excel('excel/new_'+request.data['id']+'_products.xlsx', index=False)
        driver.quit()
        return JsonResponse({})

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
    print(soup.select_one('#paraphraser-output-box').get_text(" ",strip=True))
    return soup.select_one('#paraphraser-output-box').get_text(" ",strip=True)

def replace_dimensions(url):
    pattern = r'\d+x\d+.webp'
    return re.sub(pattern, '1200x1200.webp', url)

def translate(text, dest='ar'):
    try:
        translation = GoogleTranslator(source='auto', target=dest).translate(text)
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

class GenerateBlog(APIView):
    def post(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        options = Options()
        options.add_experimental_option('detach', True)
        # options.headless = True

        # Create an instance of Chrome WebDriver
        driver = webdriver.Chrome(options=options)

        # Open the webpage
        driver.get('https://katteb.com/ar/sign-in/')
        driver.maximize_window()

        email_element = driver.find_element(By.ID, 'username')
        email_element.send_keys("icnnobar@gmail.com")
        password_element = driver.find_element(By.ID, 'password')
        password_element.send_keys("Icn@nobar123")

        # Find and click the login button
        login_button = driver.find_element(By.CSS_SELECTOR, 'button.validation-submit-btn')
        login_button.click()

        wait = WebDriverWait(driver, 15)
        wait.until(EC.url_contains('/dashboard/'))

        headline = request.data['headline']
        driver.get('https://katteb.com/ar/dashboard/generate-full-article/')
        until_visible_click(driver, 'multistep-form-body-field:nth-child(1)')
        until_visible_send_keys(driver, 'multistep-form-body-field:nth-child(1) input', headline)
        until_visible_click(driver, '.-step-excerpt')
        sleep(2)
        # until_visible_click(driver, 'multistep-form-body-field:nth-child(2)')
        # until_visible_click(driver, f'multistep-form-body-field:nth-child(2) multistep-form-body-field-fill-selectbox-item[data-value="{configs["language_code"]}"]')
        # until_visible_click(driver, '.-step-excerpt')
        # sleep(2)
        # until_visible_click(driver, 'multistep-form-body-field:nth-child(3)')
        # until_visible_send_keys(driver, 'multistep-form-body-field:nth-child(3) input.-multistep-selectbox-search', configs['audience_full_country_name'])
        # search = driver.find_elements(By.CSS_SELECTOR, 'input.-multistep-selectbox-search')[-1]
        # search.send_keys(Keys.ENTER)
        # until_visible_click(driver, f'multistep-form-body-field-fill-selectbox-item[data-value="{configs["audience_country_code"]}"')
        # until_visible_click(driver, '.-step-excerpt')
        # sleep(2)
        until_visible_click(driver, 'multistep-form-body-field:nth-child(4)')
        # numbers_of_lines = driver.find_element(By.ID, 'topic_numberofwords')
        # driver.execute_script(f"arguments[0].value = {configs['length_of_article']}", numbers_of_lines)
        until_visible_click(driver, '.-step-excerpt')
        sleep(2)
        until_visible_click(driver, 'multistep-form-next')
        until_visible_click(driver, '.-step-excerpt')
        sleep(2)
        until_visible_click(driver, 'div.-start-generating-button.hoverable.activable')

        show_article = WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'عرض المقال'))
        )

        show_article.click()

        articles_holder = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            'div.fr-element.fr-view'))
        )

        ar_output = articles_holder.get_attribute('outerHTML')
        soup = BeautifulSoup(ar_output, 'html.parser')
        headers_components = soup.select('streaming-area')
        res = []
        en_res = []
        for comp in headers_components:
            title = comp.select_one('h2').get_text(strip=True)
            comp.select_one('h2').extract()
            content = comp.get_text(" ", strip=True)
            res.append({
                'title': title,
                'description': content,
            })
            en_res.append({
                'title': translate(title, dest='en'),
                'description': translate(content, dest='en'),
            })
        keywords = extract_top_keywords(en_res[0]['description'])
        ar_keywords = []
        for keyW in keywords:
            ar_keywords.append(translate(keyW))
            
        data = {'data': json.dumps({
            "category_id": request.data['category'],
            "author": {
            "en": "ICN",
            "sa": "ICN"
            },
            "title": {
                "en": translate(headline, dest='en'),
                "sa": headline
            },
            "short_description": {
                "en": en_res[0]['description'],
                "sa": res[0]['description']
            },
            'description': {
                "en": [e['description'] for e in en_res],
                "sa": [e['description'] for e in res]
            },
            'bookmark': {
                "en": [e['title'] for e in en_res],
                "sa": [e['title'] for e in res]
            },
            "meta_description": {
                "en": en_res[0]['description'],
                "sa": res[0]['description']
            },
            "meta_keywords": {
                "en": ','.join(keywords),
                "sa": ','.join(ar_keywords)
            },
            "meta_title": {
                "en": translate(headline, dest='en'),
                "sa": headline
            }
        })}
        try:
            # Send the POST request and wait for the response
            response = requests.post('https://www.icn.com/api/v1/blog/store', data=data, files=[('image',image)])
            
            # Check if the request was successful
            if response.status_code == 200:
                print('Request was successful!')
                print('Response:', response.text)  # If the response contains JSON data
            else:
                print('Request failed with status code:', response.status_code)
                print('Response:', response.text)
        except requests.exceptions.RequestException as e:
            print('An error occurred:', e)
        driver.quit()
        return JsonResponse({})
