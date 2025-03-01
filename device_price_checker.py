import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import subprocess
from tabulate import tabulate

# Function to install missing packages
def install_missing_packages():
    required_packages = ['requests', 'pandas', 'beautifulsoup4', 'tabulate']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing package: {package}")
            subprocess.run(['pip', 'install', package])

# Install dependencies if missing
install_missing_packages()

# File path for Windows
github_directory = os.getcwd()
file_path = os.path.join(github_directory, "Privacydevicelist.csv")

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

# Ensure CSV file exists
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found. Make sure you've cloned the repository correctly.")
    exit()

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
    
    time.sleep(2)  # Avoid rate-limiting

# Display results neatly in the terminal
if results:
    headers = ["Device", "Title", "Price (GBP)", "eBay Link", "OS Support"]
    table_data = [[r['Device'], r['Title'], r['Price (GBP)'], r['eBay Link'], r['OS Support']] for r in results]
    print("\nResults:\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
else:
    print("No results found.")

# Save results to a CSV file
output_file = os.path.join(github_directory, "device_best_prices.csv")
pd.DataFrame(results).to_csv(output_file, index=False)

print(f"\nResults saved to {output_file}")
