
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
import requests
import pandas as pd

iou = pd.read_csv("../data/iou_zipcodes_2020.csv")
non_iou = pd.read_csv("../data/non_iou_zipcodes_2020.csv")

def get_zipcode(latitude, longitude):
    # Initialize the geocoder
    geolocator = Nominatim(user_agent="zipcode_locator")
    
    try:
        # Reverse geocoding to get the location
        location = geolocator.reverse((latitude, longitude), exactly_one=True)

        # Check if location is found and has address information
        if location and 'postcode' in location.raw['address']:
            return location.raw['address']['postcode']
        else:
            return "ZIP code not found for the given coordinates."
    
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return f"Geocoding service error: {e}"
    
# get_ei(zipcode) takes one argument, a ZIP code, and returns the corresponding EIA ID by searching in the zipcode column of the iou dataframe and returning the respective eiad, and if the ZIP is not found, search the non_iou dataframe
def get_ei(zipcode):
    int_zip = int(zipcode)
    if int_zip in iou["zip"].values:
        return iou.loc[iou["zip"] == int_zip, "eiaid"].values[0]
    elif int_zip in non_iou["zip"].values:
        return non_iou.loc[non_iou["zip"] == int_zip, "eiaid"].values[0]
    else:
        return "ZIP code not found in the dataset."

def open_api(url):
    folder = "../data/openei"
    filename = "utility_rates.csv"

    local_path = os.path.join(folder, filename)
    response = requests.get(url)

    if response.status_code == 200:
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully and saved to {local_path}")
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")

if __name__ == "__main__":
    open_api("https://api.openei.org/utility_rates?version=3&format=csv&limit=3&eia=195&api_key=GU3aRPzDoNMmTmXcaVI8lUiApKSzRfBguuhFnhOa&detail=full")
    new_df = pd.read_csv("../data/openei/utility_rates.csv")
    print(new_df.head(10))


#add a few test cases