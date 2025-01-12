from flask import Flask, request
import cloudscraper
import time
import urllib.parse
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, parse_qs

from supabase import Client, create_client

import threading
app = Flask(__name__)

#db = SQLAlchemy()
##app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:KkS0HxF3s6AAwo4n@db.oyprygmqmtgdysbopzcn.supabase.co:5432/postgres"
#db.init_app(app)

supabase_client: Client = create_client("https://oyprygmqmtgdysbopzcn.supabase.co","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im95cHJ5Z21xbXRnZHlzYm9wemNuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjYwOTYwOSwiZXhwIjoyMDUyMTg1NjA5fQ.q03eizLiEQykh30rXWoBFKViJ1UjM_FHJv51iAUdlEw")


@app.route("/")
def hello_world():
    return "<p>Hello, George!</p>"

# Function to run in a new thread every 30 minutes
def task_to_run(url, userID):
    while True:
        print("Task executed")
        already_scraped = supabase_client.table("oglasi").select("avtonet_id").eq("user_id", userID).execute()
        scraper  = cloudscraper.create_scraper()
        headers = {
            "User-Agent": "george agent",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "gzip, deflate, br",
            'Referer': 'https://www.avto.net/',
            "Connection": "keep-alive",
        }
        scraper.get("https://www.avto.net/", headers=headers)

        cookies = scraper.cookies.items()
        cookie_str = ""
        for x in cookies[1:]:
            cookie_str += x[0]+"="+x[1]+";"

        new_headers = {
            "User-Agent": "george from albania",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "gzip, deflate, br",
            'Referer': 'https://www.avto.net/',
            "Connection": "keep-alive",
            "Cookie" : cookie_str
        }
        resp = scraper.get(url,headers=headers)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Find all car result containers
            car_ads = soup.find_all("div", class_="row bg-white position-relative GO-Results-Row GO-Shadow-B")

            # Extract and print the name, price, table values, photo URL, and detail URL for each ad
            base_url = "https://www.avto.net"  # Base URL for relative paths
            for idx, ad in enumerate(car_ads, 1):
                # Extract car name
                name_div = ad.find("div", class_="GO-Results-Naziv bg-dark px-3 py-2 font-weight-bold text-truncate text-white text-decoration-none")
                car_name = name_div.find("span").text.strip() if name_div else "N/A"
                
                # Extract car price
                price_div = ad.find("div", class_="GO-Results-Price-TXT-Regular")
                car_price = price_div.text.strip() if price_div else "N/A"
                
                # Extract values from the table
                details_table = ad.find("table", class_="table table-striped table-sm table-borderless font-weight-normal mb-0")
                table_values = []
                if details_table:
                    rows = details_table.find_all("tr")
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) == 2:
                            table_values.append(cols[1].text.strip())
                
                # Extract full photo URL
                photo_div = ad.find("div", class_="GO-Results-Photo")
                photo_img = photo_div.find("img") if photo_div else None
                photo_url = photo_img["src"] if photo_img else "N/A"
                
                # Extract URL linking to more details
                detail_link = ad.find("a", class_="stretched-link")
                detail_url = os.path.join(base_url, detail_link["href"]) if detail_link else "N/A"

                # Extract ID from the details URL
                detail_id = "N/A"
                if detail_url != "N/A":
                    parsed_url = urlparse(detail_url)
                    query_params = parse_qs(parsed_url.query)
                    detail_id = query_params.get("id", ["N/A"])[0]  # Extract `id` from query params
                
                if(True):
                    print("nigger")
                    print(car_price)
                    insert = (
                        supabase_client.table("oglasi")
                        .insert({"user_id": userID, "avtonet_id": int(detail_id), "name": car_name, "price":car_price, "photo_url":photo_url, "ad_url":detail_url})
                        .execute()
                    )

                # Print extracted information
                print(f"Ad {idx}:")
                print(f"Name: {car_name}")
                print(f"Price: {car_price}")
                print("Details:")
                for value in table_values:
                    print(f"  {value}")
                print(f"Photo URL: {photo_url}")
                print(f"Details URL: {detail_url}")
                print(f"Ad ID: {detail_id}")
                print("-" * 40)
            time.sleep(30 * 60)  # Sleep for 30 minutes
        else:
            print("GOERGE FLOYD - OXYGEN")
            f = open("file.html", "w", encoding="utf-8")
            f.write("GOERGE FLOYD - OXYGEN")
            f.close()
        

@app.route("/add-scraper", methods=['GET'])
def add_scraper():
    userID = request.args.get('userID')
    znamka = request.args.get('znamka', '')
    model = request.args.get('model', '')
    cenaMin = request.args.get('cenaMin', '')
    cenaMax = request.args.get('cenaMax', '')
    letnikMin = request.args.get('letnikMin', '')
    letnikMax = request.args.get('letnikMax', '')
    bencin = request.args.get('bencin', '')
    prevozeniMax = request.args.get('prevozeniMax', '')
    # Default values or fallback
    url_base = "https://www.avto.net/Ads/results.asp?"
    
    # Default values for the parameters that should always exist in the URL
    params = {
        'znamka': znamka,
        'model': model,
        'modelID': '',
        'tip': 'katerikoli tip',
        'znamka2': '',
        'model2': '',
        'tip2': 'katerikoli tip',
        'znamka3': '',
        'model3': '',
        'tip3': 'katerikoli tip',
        'cenaMin': cenaMin,
        'cenaMax': cenaMax,
        'letnikMin': letnikMin,
        'letnikMax': letnikMax,
        'bencin': bencin,
        'starost2': '999',
        'oblika': '0',
        'ccmMin': '0',
        'ccmMax': '99999',
        'mocMin': '',
        'mocMax': '',
        'kmMin': '0',
        'kmMax': prevozeniMax,
        'kwMin': '0',
        'kwMax': '999',
        'motortakt': '',
        'motorvalji': '',
        'lokacija': '0',
        'sirina': '',
        'dolzina': '',
        'dolzinaMIN': '',
        'dolzinaMAX': '',
        'nosilnostMIN': '',
        'nosilnostMAX': '',
        'sedezevMIN': '',
        'sedezevMAX': '',
        'lezisc': '',
        'presek': '',
        'premer': '',
        'col': '',
        'vijakov': '',
        'EToznaka': '',
        'vozilo': '',
        'airbag': '',
        'barva': '',
        'barvaint': '',
        'doseg': '',
        'EQ1': '1000000000',
        'EQ2': '1000000000',
        'EQ3': '1000000000',
        'EQ4': '100000000',
        'EQ5': '1000000000',
        'EQ6': '1000000000',
        'EQ7': '1000000120',
        'EQ8': '101000000',
        'EQ9': '1000000020',
        'KAT': '1010000000',
        'PIA': '',
        'PIAzero': '',
        'PIAOut': '',
        'PSLO': '',
        'akcija': '',
        'paketgarancije': '',
        'broker': '',
        'prikazkategorije': '',
        'kategorija': '',
        'ONLvid': '',
        'ONLnak': '',
        'zaloga': '',
        'arhiv': '',
        'presort': '',
        'tipsort': '',
        'stran': ''
    }

    # Generate the final URL with all parameters, including empty ones
    final_url = "https://www.avto.net/Ads/results.asp?" + urllib.parse.urlencode(params)
    print(final_url)
    thread = threading.Thread(target=task_to_run(final_url, userID), daemon=True)
    thread.start()
    return "Task started!", 200

if __name__ == 'main':
    app.run(debug=True, port=3000)