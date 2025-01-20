from flask import Flask, request
import cloudscraper
import time
import urllib.parse
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, parse_qs

from supabase import Client, create_client
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import threading
app = Flask(__name__)

#db = SQLAlchemy()
##app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:KkS0HxF3s6AAwo4n@db.oyprygmqmtgdysbopzcn.supabase.co:5432/postgres"
#db.init_app(app)

supabase_client: Client = create_client("https://oyprygmqmtgdysbopzcn.supabase.co","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im95cHJ5Z21xbXRnZHlzYm9wemNuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjYwOTYwOSwiZXhwIjoyMDUyMTg1NjA5fQ.q03eizLiEQykh30rXWoBFKViJ1UjM_FHJv51iAUdlEw")
cred = credentials.Certificate("fcm.json")
firebase_admin.initialize_app(cred)

@app.route("/")
def hello_world():
    already_scraped = supabase_client.table("oglasi").select("avtonet_id").or_("and(user_id.eq.188c689c-3a02-4115-9dc1-08a37c48f6c6,avtonet_id.eq.20472272)").execute()
    print(already_scraped)
    return "<p>Hello, EMP!</p>"

@app.route("/delete-tracker", methods=['GET'])
def delete_tracker():
    trackerID = request.args.get('trackerID')
    response = supabase_client.table('oglasi').delete().eq('trackerID', trackerID).execute()
    return "<p>DELETE, EMP!</p>"

# Function to run in a new thread every 30 minutes
def task_to_run(url, userID, notificationToken, trackerID):
    
    
    while True:
        print("Task executed")
        scraper  = cloudscraper.create_scraper()
        proxy = {
            'https': 'http://Z6LyjqVSnKVUncl-res-al:KHcnCdRYlAIf1WK@geo.beyondproxy.io:5959'
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "gzip, deflate, br",
            'Referer': 'https://www.avto.net/',
            "Connection": "keep-alive",
        }
        scraper.get("https://www.avto.net/", headers=headers, proxies=proxy)

        cookies = scraper.cookies.items()
        cookie_str = ""
        for x in cookies[1:]:
            cookie_str += x[0]+"="+x[1]+";"

        new_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "gzip, deflate, br",
            'Referer': 'https://www.avto.net/',
            "Connection": "keep-alive",
            "Cookie" : cookie_str
        }
        resp = scraper.get(url,headers=headers, proxies=proxy)
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
                letnik = ""
                kilometri = ""
                tip_goriva = ""
                menjalnik = ""
                prostornina_motorja = ""
                try:
                    letnik = table_values[0]
                    kilometri = table_values[1]
                    tip_goriva = table_values[2]
                    menjalnik = table_values[3]
                    prostornina_motorja = table_values[4]
                except:
                    pass
                
                if(True):
                    print(car_price)
                    already_scraped = supabase_client.table("oglasi").select("avtonet_id").or_("and(user_id.eq."+userID+",avtonet_id.eq."+detail_id+")").execute()
                    print(already_scraped)
                    if(len(already_scraped.data)) == 0:

                        insert = (
                            supabase_client.table("oglasi")
                            .insert({"user_id": userID, "avtonet_id": int(detail_id), "trackerID":trackerID, "name": car_name, "price":car_price, "letnik":letnik, "motor":tip_goriva, "menjalnik": menjalnik, "moc_motorja":prostornina_motorja, "photo_url":photo_url, "ad_url":detail_url})
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
                        registration_token = 'ctPqT0DPS4-SIV-iF9vt2k:APA91bHuk1h_1GtBk1gMteg7cO1w6oq-O1sQ4pu5arEYBSfjmFYIu7K-ZdqYt4o_MGz2opd6pb-6cbrpxLkSAnZLpVHhvBcv305bnwOn0vAySCvpGA_81jQ'
                        # See documentation on defining a message payload.
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title='AVTOTRACKER - NOV OGLAS',
                                body='Nov oglas je bil objavljen',
                            ),
                            token=notificationToken,
                        )
                        #response = messaging.send(message)
                        #print('Successfully sent message:', response)
                    else:
                        print("AVTO ŽE V BAZI")

                    # Send a message to the device corresponding to the provided
                    # registration token.
                        #response = messaging.send(message)
                    # Response is a message ID string.
                        #print('Successfully sent message:', response)
                    

                
            time.sleep(30 * 60)  # Sleep for 30 minutes
        else:
            print("EMP - SAD")
            
        

@app.route("/add-scraper", methods=['GET'])
def add_scraper():
    userID = request.args.get('userID')
    trackerID = request.args.get('trackerID')
    notificationToken = request.args.get('notificationToken')
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
    thread = threading.Thread(target=task_to_run, args=(final_url, userID, notificationToken, trackerID), daemon=True)
    thread.start()
    print("nnnnnnnnnn")
    return "<p>Hello, requester EMP!</p>"

if __name__ == '__main___':
    app.run()