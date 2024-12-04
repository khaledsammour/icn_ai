import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/content"]

def getProducts(page, lang):
    url = f'https://www.icn.com/api/v1/products/updated-after/2024-12-3?page={page}'
    response = requests.request("GET", url, headers={
        'App-Language': lang
    })

    return response.json()['products']

def addToGoogle(service, lang, product):
    googleApisPayload = {
    "kind": "content#product",
    "offerId": str(product['id']),
    "title": product['product_translations']['name'],
    "description": product['product_translations']['description'],
    "link": "https://icn.com/product/"+product['slug'],
    "imageLink": product['thumbnail_img'],
    "additionalImageLinks": product['photos'],
    "contentLanguage": lang,
    "targetCountry": "JO",
    "feedLabel": "JO",
    "channel": "online",
    "availability": "in stock" if product['product_in_stock'] == 1  else "out of stock",
    "condition": "new",
    "price": {
        "value": product['unit_price'],
        "currency": "JOD"
    },
    "salePrice": {
        "currency": "JOD",
        "value": product['after_discount']['lowest_price']
    } if product['after_discount']['lowest_price'] < product['unit_price'] else None,
    "shipping": [
        {
        "country": "JO"
        }
    ]
    }
    try:
        request = service.products().insert(
            merchantId='5455777362', body=googleApisPayload)
        response = request.execute()
        # print(f"Product added: {json.dumps(response, indent=2)}")
    except HttpError as err:
        print(err)

def main():
  """Shows basic usage of the Docs API.
  Prints the title of a sample document.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "apps/home/client.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("content", "v2.1", credentials=creds)
  except HttpError as err:
    print(err)
  
    # Retrieve the documents contents from the Docs service.
    # document = service.products().list(merchantId='5455777362', maxResults=50).execute()
  url = f'https://www.icn.com/api/v1/products/updated-after/2024-12-3?page=1'
  response = requests.request("GET", url, headers={
    'App-Language': 'sa'
  })

  ar_last_page =  response.json()['last_page']
  print('-'*50)
  for i in range(ar_last_page):
    print(str(i+1)+'/'+str(ar_last_page))
    ar_products = getProducts(str(i+1), 'sa')
    for product in ar_products:
        addToGoogle(service, 'ar', product)
  print('-'*50)

  url = f'https://www.icn.com/api/v1/products/updated-after/2024-12-3?page=1'
  response = requests.request("GET", url, headers={
    'App-Language': 'en'
  })

  en_last_page =  response.json()['last_page']
  print('+'*50)
  for i in range(en_last_page):
    print(str(i+1)+'/'+str(en_last_page))
    en_products = getProducts(str(i+1), 'en')
    for product in en_products:
        addToGoogle(service, 'en', product)
  print('+'*50)

if __name__ == "__main__":
  main()