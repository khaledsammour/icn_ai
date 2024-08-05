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
from googletrans import Translator
# from transformers import *
# model = PegasusForConditionalGeneration.from_pretrained("tuner007/pegasus_paraphrase")
# tokenizer = PegasusTokenizerFast.from_pretrained("tuner007/pegasus_paraphrase")

# def get_paraphrased_sentences(model, tokenizer, sentence, num_return_sequences=5, num_beams=5):
#   # tokenize the text to be form of a list of token IDs
#   inputs = tokenizer([sentence], truncation=True, padding="longest", return_tensors="pt")
#   # generate the paraphrased sentences
#   outputs = model.generate(
#     **inputs,
#     num_beams=num_beams,
#     num_return_sequences=num_return_sequences,
#   )
#   # decode the generated sentences using the tokenizer to get them back to text
#   return tokenizer.batch_decode(outputs, skip_special_tokens=True)
# sentence = 'Redmi A3 features an all-new Premium Halo Design that is eye-catching and makes you look great in a sea of boring designs. Choose from three beautiful colours that will always make you stand out.'
# print(get_paraphrased_sentences(model, tokenizer, sentence))


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

jsons = [
    {
        "id": 1,
        "Name": "Oriental",
        "products": {
            "path": ".tb_system_products .product-thumb",
            "type": "css",
            "execute": ".tb_label_stock_status",
            "link": {
                "path": "h4 > a",
                "type": "css"
            }
        },
        "attr": {
            "title":{
                "path": ".tb_wt_page_title_system",
                "type_type": "css"
            },
            "price":{
                "path": "#content > div > div > div > div > div:nth-of-type(2) .price .price-regular, #content > div > div > div > div > div:nth-of-type(2) .price .price-old",
                "type_type": "css"
            },
            "main_image":{
                "path": "img.zoomImg",
                "type_type": "css"
            },
            "images":{
                "path": ".mSSlideElement > li > img",
                "type_type": "css"
            },
            "description":{
                "path": ".mSSlideElement > li > img",
                "type_type": "css"
            },
            "discount":{
                "path": ".mSSlideElement > li > img",
                "type_type": "css"
            },
            "attributes":{
                "path": ".mSSlideElement > li > img",
                "type_type": "css"
            },
        }
    }
]

class DynamicScrapView(APIView):
    def post(self, request, *args, **kwargs):
        options = Options()
        driver = Chrome(options=options)
        driver.maximize_window()
        url = jsons[0]
        driver.get(url)
        driver.execute_script("window.open('https://www.freetranslations.org/english-to-arabic-translation.html');")
        driver.switch_to.window(driver.window_handles[0])
        isExist = True
        index = 1
        data = []
        errors = []
        while(isExist):
            driver.get(url+'&page='+str(index))
            sleep(3)
            isExist = check_if_exist(driver, jsons[0]['products']['path'], "products")
            elements = driver.find_elements(By.CSS_SELECTOR, jsons[0]['products']['path'])
            hrefs = []
            for e in elements:
                if 'execute' in jsons[0]['products'] and len(e.find_elements(By.CSS_SELECTOR, jsons[0]['products']['execute'])) == 0 or 'execute' not in jsons[0]['products']:
                    hrefs.append(e.find_element(By.CSS_SELECTOR, jsons[0]['products']['link']['path']).get_attribute("href"))


        for href in hrefs:
            try:
                driver.get(href)
                sleep(1)
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(jsons[0]['attr']['title']['path']).get_text(strip=True)

                # Get the product price
                price_elem = soup.select_one(jsons[0]['attr']['price']['path'])
                price = price_elem.get_text().replace('JOD', '').strip() if price_elem else ''

                # Get the main image URL
                main_image_elem = soup.select_one(jsons[0]['attr']['main_image']['path'])
                
                image = getImageUrl(request.data['id'],main_image_elem['src']) if main_image_elem else ''

                # Get additional images
                image_elems = soup.select(jsons[0]['attr']['images']['path'])
                images = [getImageUrl(request.data['id'],img['src'].replace('70x70', '1200x1200')) for img in image_elems]

                # Check stock status
                in_stock = soup.select_one(jsons[0]['attr']['in_stock']['path'])['max'] if jsons[0]['attr']['in_stock']['path'] != '' else '3'

                # Get product attributes content
                description_elem = soup.select_one(jsons[0]['attr']['description']['path'])
                product_attributes_content = description_elem.get_text(strip=True) if description_elem else ''

                # Get keywords
                key_words_elem = soup.select_one("meta[property*='og:title']")
                keyWords = key_words_elem['content'] if key_words_elem else ''

                # Get discount
                discount_elem = soup.select_one(jsons[0]['attr']['discount']['path'])
                discount = discount_elem.get_text().replace('JOD', '').strip() if discount_elem else '0'

                product_attributes_content_json = {}
                
                product_attributes = soup.select(jsons[0]['attr']['attributes']['path'])
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
        # change_driver = Chrome()
        # change_driver.maximize_window()
        url = request.data['url']
        driver.get(url)
        # change_driver.get('https://www.paraphrase-online.com/')
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
                    until_visible_click(driver, '.fotorama__nav__shaft > .fotorama__nav__frame:nth-child('+str(indx+2)+')')
                    sleep(1)
                    mainImg = driver.find_element(By.CSS_SELECTOR, '.fotorama__stage *[data-active*="true"]')
                    images.append(getImageUrl(request.data['id'], mainImg.get_attribute('href')))

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
                # changed_title = change_text(change_driver, title) if len(title.split(' '))>5 else ''
                # changed_product_attributes_content = change_text(change_driver, product_attributes_content) if len(product_attributes_content.split(' '))>5 else ''
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
        driver = Chrome()
        driver.maximize_window()
        url = request.data['url']
        driver.get(url)
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
        print(len(hrefs))
        for href in hrefs[:5]:
            try:
                driver.get(href)
                title_selector = 'meta[name*="title"]'
                description_selector = '#description'
                key_words_selector = "meta[property*='og:title']"
                href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                soup = BeautifulSoup(href_res, 'html.parser')
                title = soup.select_one(title_selector).get_text(strip=True)
                # Get the product price
                price_elem = soup.select_one(".product-price .previous-price").get_text(strip=True) if soup.select_one(".product-price .previous-price") else soup.select_one("meta[property*='product:price:amount']")['content']
                price = price_elem.strip().replace('JOD','').strip() if price_elem else ''
                # Get discount
                discount_elem = soup.select_one("meta[property*='product:price:amount']")['content'] if soup.select_one(".product-price .previous-price").get_text(strip=True) else None
                discount = discount_elem.strip().replace('JOD','').strip() if discount_elem else '0'
                # Get the main image URL
                main_image_elem = soup.select_one('img[alt*="Product image"]')
                image = getImageUrl(request.data['id'], main_image_elem['src']) if main_image_elem else ''
                # Get additional images
                image_elems = soup.select('img[alt*="Product image"]')
                images = [getImageUrl(request.data['id'], img['src']) for img in image_elems if len(img['src'])>10]
                # Check stock status
                in_stock = '3'
                # Get product attributes content
                description_elem = soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                product_attributes_content = description_elem if description_elem else ''
                # Get keywords
                key_words_elem = soup.select_one(key_words_selector)
                keyWords = key_words_elem['content'].replace('| baghdad corner jordan','').strip() if key_words_elem else ''
                driver.get(href.replace('/en/', '/ar/'))
                ar_href_res = driver.find_element(By.CSS_SELECTOR, 'html').get_attribute('outerHTML')
                ar_soup = BeautifulSoup(ar_href_res, 'html.parser')
                ar_title = ar_soup.select_one(title_selector).get_text(strip=True)
                ar_key_words_elem = ar_soup.select_one(key_words_selector)
                ar_keyWords = ar_key_words_elem['content'].replace('| baghdad corner jordan','').strip() if ar_key_words_elem else ''
                ar_description_elem = ar_soup.select_one(description_selector).get_text(" ",strip=True) if soup.select_one(description_selector) else ''
                ar_product_attributes_content = ar_description_elem if ar_description_elem else ''
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
        return JsonResponse({})
    
def change_text(driver, text):
    driver.refresh()
    driver.switch_to.window(driver.window_handles[0])
    until_visible_click(driver, "button[tooltip*='Rephrase and change the structure of your sentence']")
    driver.switch_to.window(driver.window_handles[0])
    driver.find_element(By.CSS_SELECTOR, '#input-data').clear()
    until_visible_send_keys(driver, '#input-data', text)
    driver.switch_to.window(driver.window_handles[0])
    until_visible_click(driver, '.phraseit')
    driver.switch_to.window(driver.window_handles[0])
    try: 
        until_visible(driver, '#output-data > span')
    except:
        until_visible_click(driver, '.phraseit')
        driver.switch_to.window(driver.window_handles[0])
        until_visible(driver, '#output-data > span')
    driver.switch_to.window(driver.window_handles[0])
    return driver.find_element(By.CSS_SELECTOR, '#output-data').text
    
def replace_dimensions(url):
    pattern = r'\d+x\d+.webp'
    return re.sub(pattern, '1200x1200.webp', url)

def translate(text):
    try:
        translator = Translator()
        translator.translate(text)
        translation = translator.translate(text, dest='ar').text
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
