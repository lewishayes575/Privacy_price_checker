import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import csv

# File path for Windows
file_path = r"C:\device_price_checker\Privacydevicelist.csv"

# List of keywords to exclude from listings
EXCLUDE_KEYWORDS = [
    "case", "screen protector", "cover", "tempered glass", "skin", "film",
    "charger", "cable", "adapter", "box only", "empty box", "just box", "accessory", "accessories"
]

# Function to check if text contains excluded keywords
def contains_excluded_keywords(text):
    text = text.lower()
    return any(keyword in text for keyword in EXCLUDE_KEYWORDS)

# Function to get all valid eBay listings for a device
def get_ebay_listings(query):
    base_url = "https://www.ebay.co.uk"
    search_url = f"{base_url}/sch/i.html?_nkw={query.replace(' ', '+')}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    listings = []
    
    for item in soup.select('.s-item'):
        title = item.select_one('.s-item__title')
        price = item.select_one('.s-item__price')
        link_tag = item.select_one('.s-item__link')
        desc_tag = item.select_one('.s-item__subtitle')  # eBay description (if available)
        
        if title and price and link_tag:
            title_text = title.text.lower()
            description_text = desc_tag.text.lower() if desc_tag else ""
            
            if contains_excluded_keywords(title_text) or contains_excluded_keywords(description_text):
                continue
            
            price_text = price.text.replace('£', '').replace(',', '').strip()
            try:
                price_value = float(price_text.split()[0])
            except ValueError:
                continue

            listings.append({
                'Title': title.text,
                'Price (GBP)': price_value,
                'eBay Link': urljoin(base_url, link_tag['href'])
            })
    
    return listings

# Load the CSV file
df = pd.read_csv(file_path)

# Ask the user what they are searching for
print("What would you like to search by?")
print("1. OS")
print("2. Brand")
print("3. Model")
choice = input("Enter the number of your choice: ")

if choice == "1":
    os_choice = input("Enter the OS you are looking for (GrapheneOS, CalyxOS, eOS, LineageOS): ")
    filtered_df = df[df[os_choice] == 'Y']
elif choice == "2":
    brand_choice = input("Enter the brand (e.g., Google, Samsung, OnePlus): ")
    filtered_df = df[df['Make'].str.contains(brand_choice, case=False, na=False)]
elif choice == "3":
    model_choice = input("Enter the model name (e.g., Pixel 7 Pro, Galaxy S21): ")
    filtered_df = df[df['Model'].str.contains(model_choice, case=False, na=False)]
else:
    print("Invalid choice. Exiting.")
    exit()

results = []

for index, row in filtered_df.iterrows():
    device_name = f"{row['Make']} {row['Model']}"
    listings = get_ebay_listings(device_name)
    
    # Collect OS support information
    os_support = {
        'GrapheneOS': row['GrapheneOS'],
        'CalyxOS': row['CalyxOS'],
        'eOS': row['eOS'],
        'LineageOS': row['LineageOS']
    }
    
    for listing in listings:
        results.append({
            'Device': device_name,
            'Title': listing['Title'],
            'Price (GBP)': listing['Price (GBP)'],
            'eBay Link': listing['eBay Link'],
            'OS Support': os_support
        })
        
        print(f"{device_name}: £{listing['Price (GBP)']} - {listing['eBay Link']}")
        print(f"Supported OS: {os_support}\n")
    
    time.sleep(2)  # Avoid rate-limiting

# Save results to a CSV file
output_file = r"C:\device_price_checker\device_best_prices.csv"
pd.DataFrame(results).to_csv(output_file, index=False)

print(f"Results saved to {output_file}")
