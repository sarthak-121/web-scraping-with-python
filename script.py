from bs4 import BeautifulSoup
from bs4.builder import FAST
from mysql.connector.utils import print_buffer
import requests
import urllib.parse
import json
import mysql.connector


try:
    db = mysql.connector.connect(
        host='localhost',
        user="root",
        password="root",
        auth_plugin='mysql_native_password',
        database="store_database"
    )
except:
    print('could not connect to database')
    exit()

mycursor = db.cursor()


try:
    mycursor.execute('''create table new_store_info (
        Id int primary key,
        Store_Name varchar(50), 
        Phone varchar(20),
        street varchar(50),
        suburb varchar(50), 
        state varchar(10), 
        postcode int,
        Latitude float(25),
        Longitude float(25), 
        Store_URL varchar(100),
        opening_hours_current_week text,
        opening_hours_next_week text
        
    )''')
except:
    print('table already created')


def timing_in_json(timings):
    week = {}

    for timing in timings:
        week[timing.find('span', class_='day').text] = timing.find('span', class_='hours').text

    return json.dumps(week)


def getStoreLink(suburb):
    coordinates_url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(suburb) +'?format=json'
    try:
        response = requests.get(coordinates_url).json()
        Lat, Long = response[0]["lat"] , response[0]["lon"] 
    except Exception as e:
        print(e)
        return[0, 0]
    return [Lat, Long]


def scrape_data(store_url, id):
    try:
        storeInfo = requests.get(store_url).text
    except:
        print('could not get data.')
        return False

    storeContent = BeautifulSoup(storeInfo,'lxml')
    mainSection = storeContent.find('div',class_='StoreDetail')
    storeDetail = mainSection.find('div',class_='store-detail-content')
    address = storeDetail.find('address').find_all('div')    
    address_list = address[1].text.split()

    name = mainSection.h1.text    
    street = address[0].text
    suburb, state, postcode = ' '.join(address_list[0:-2]), address_list[-2], int(address_list[-1])
    phone = storeDetail.find('div',class_='phone').div.text
    timing_current_week = timing_in_json(storeDetail.find_all('ul',class_='StoreHours')[0].find_all('li', class_='opening-hours'))
    timing_next_week = timing_in_json(storeDetail.find_all('ul',class_='StoreHours')[1].find_all('li', class_='opening-hours'))
    coordinate = getStoreLink(suburb)
    latitude = coordinate[0]
    longitude = coordinate[1]

    mycursor.execute('insert into new_store_info (Id,Store_Name, Phone, street, suburb, state, postcode, Latitude, Longitude, Store_URL, opening_hours_current_week, opening_hours_next_week) value (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
    (id, name, phone, street, suburb, state, postcode, latitude, longitude, store_url, timing_current_week, timing_next_week))
    db.commit()
  
    


def generate_hiffened_name(name, id):
    hiffened_name = ''

    for char in name:
        if char.isspace():
            hiffened_name = hiffened_name + '-'
        else:
            hiffened_name = hiffened_name + char

    return f'https://www.bigw.com.au/store/{id}/{hiffened_name}'    


try:
    response = requests.get('https://api.bigw.com.au/api/stores/v0/list')
    data = response.json()

    for key in data:
        id = data[key]['id']
        name = data[key]['name']
        
        store_url = generate_hiffened_name(name, id)
        scrape_data(store_url, id)

except Exception as e:
    print(e)





