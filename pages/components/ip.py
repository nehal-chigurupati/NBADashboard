import streamlit as st
import requests
import pandas as pd
from streamlit_javascript import st_javascript
from datetime import datetime
import pytz

def get_location(ip_address):
    try:
        # Use a third-party API to get the location based on IP address
        response = requests.get(f'https://api.ipgeolocation.io/ipgeo?apiKey=58c2deb9216c4e4fba2fc6b48a53a1ee&ip={ip_address}')
        data = response.json()
        
        # Extract relevant information from the response
        city = data.get('city')
        country = data.get('country_name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        return city, country, latitude, longitude
    
    except Exception as e:
        
        return None, None, None, None

def request_ip_address():
    url = 'https://api.ipify.org?format=json'
    script = (f'await fetch("{url}").then('
                'function(response) {'
                    'return response.json();'
                '})')
    try:
        result = st_javascript(script)
        if isinstance(result, dict) and 'ip' in result:
            return result['ip']
        else: 
            return None
    except: 
        return None
    
def get_est_time_and_date():
    # Set the time zone to Eastern Standard Time (EST)
    est_timezone = pytz.timezone('US/Eastern')

    # Get the current time in UTC
    utc_now = datetime.utcnow()

    # Convert UTC time to EST
    est_now = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

    # Extract day, month, and year
    day = est_now.day
    month = est_now.strftime('%B')  # Full month name
    year = est_now.year

    # Format time in HH:MM:SS
    time = est_now.strftime('%H:%M:%S')

    return time, day, month, year

def loc(page):
    user_ip = request_ip_address()
    time, day, month, year = get_est_time_and_date()

    if user_ip != None:
        city, country, lat, long = get_location(user_ip)
        access_log = pd.read_csv("pages/components/ips_v2.csv")

        all_ips = access_log["ip"].tolist()
        all_ips.append(user_ip)

        all_cities = access_log["city"].tolist()
        all_cities.append(city)

        all_lats = access_log["lat"].tolist()
        all_lats.append(lat)

        all_longs = access_log["lon"].tolist()
        all_longs.append(long)
        
        all_times = access_log["time"].tolist()
        all_times.append(time)

        all_days = access_log["day"].tolist()
        all_days.append(day)

        all_months = access_log["month"].tolist()
        all_months.append(month)

        all_years = access_log["year"].tolist()
        all_years.append(year)

        all_pages = access_log["page"].tolist()
        all_pages.append(page)

        new_log = {
            'ip': all_ips,
            'city': all_cities,
            'lat': all_lats,
            'lon': all_longs,
            'time': all_times,
            'day': all_days,
            'month': all_months,
            'year': all_years,
            'page': all_pages
        }

        new_log = pd.DataFrame(new_log)
        new_log.to_csv("pages/components/ips_v2.csv")
        

