import time
import json
import os
import pandas as pd
import tkinter as tk
from tkinter import simpledialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from googlesearch import search  # Google search for product links

# Set up Selenium WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Create a dialog box for user input
root = tk.Tk()
root.withdraw()  # Hide main window

product_name = simpledialog.askstring("Input", "Enter the product name:").strip()
website = simpledialog.askstring("Input", "Enter website (Amazon/Flipkart):").strip().lower()

# Function to find product URL from Google search
def get_product_url(product_name, website):
    query = f"{product_name} site:{website}.com"
    try:
        for result in search(query, num_results=5):  # Fixed function
            if website in result:
                return result
    except Exception as e:
        print(f"❌ Google Search Error: {e}")
    return None

# Get product URL automatically
product_url = get_product_url(product_name, website)
if not product_url:
    print(f"❌ No product found on {website}. Try another product name.")
    driver.quit()
    exit()

print(f"✅ Found product URL: {product_url}")

# Scraping functions
def scrape_amazon(url):
    driver.get(url)
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "productTitle")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title = soup.find("span", id="productTitle").text.strip()
        price_element = soup.find("span", class_="a-price-whole")
        price = price_element.text.strip().replace(",", "") if price_element else "Price Not Found"

        reviews = scrape_amazon_reviews(url)

        return {"Website": "Amazon", "Title": title, "Price": price, "Reviews": reviews}

    except Exception as e:
        print("❌ Amazon Scraping Error:", e)
        return {"Website": "Amazon", "Title": "N/A", "Price": "N/A", "Reviews": {"Best Reviews": [], "Worst Reviews": []}}

def scrape_amazon_reviews(url):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    review_elements = soup.find_all("span", {"data-hook": "review-body"})
    rating_elements = soup.find_all("i", {"data-hook": "review-star-rating"})

    reviews = []
    for review, rating in zip(review_elements, rating_elements):
        text = review.text.strip()
        star_rating = float(rating.text.strip().split(" ")[0])  # Extract numeric rating
        reviews.append({"Rating": star_rating, "Review": text})

    best_reviews = sorted(reviews, key=lambda x: x["Rating"], reverse=True)[:5]
    worst_reviews = sorted(reviews, key=lambda x: x["Rating"])[:5]

    return {"Best Reviews": best_reviews, "Worst Reviews": worst_reviews}

def scrape_flipkart(url):
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "B_NuCI")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title = soup.find("span", class_="B_NuCI").text.strip()
        price_element = soup.find("div", class_="_30jeq3 _16Jk6d")
        price = price_element.text.strip().replace("₹", "").replace(",", "") if price_element else "Price Not Found"

        reviews = scrape_flipkart_reviews(url)

        return {"Website": "Flipkart", "Title": title, "Price": price, "Reviews": reviews}

    except Exception as e:
        print("❌ Flipkart Scraping Error:", e)
        return {"Website": "Flipkart", "Title": "N/A", "Price": "N/A", "Reviews": {"Best Reviews": [], "Worst Reviews": []}}

def scrape_flipkart_reviews(url):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    review_elements = soup.find_all("div", class_="t-ZTKy")
    rating_elements = soup.find_all("div", class_="_3LWZlK")

    reviews = []
    for review, rating in zip(review_elements, rating_elements):
        text = review.text.strip()
        try:
            star_rating = float(rating.text.strip())  # Convert to numeric
        except:
            star_rating = 0.0  # Handle missing ratings
        reviews.append({"Rating": star_rating, "Review": text})

    best_reviews = sorted(reviews, key=lambda x: x["Rating"], reverse=True)[:5]
    worst_reviews = sorted(reviews, key=lambda x: x["Rating"])[:5]

    return {"Best Reviews": best_reviews, "Worst Reviews": worst_reviews}

# Choose scraper based on user input
if "amazon" in website:
    product_data = scrape_amazon(product_url)
elif "flipkart" in website:
    product_data = scrape_flipkart(product_url)
else:
    print("❌ Invalid website. Please enter 'Amazon' or 'Flipkart'.")
    driver.quit()
    exit()

# Ensure JSON file saves next to the script
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script location
output_file = os.path.join(script_dir, "scraped_product_data.json")  # Save near script

# Save data in JSON format
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(product_data, json_file, indent=4, ensure_ascii=False)

print(f"✅ Data saved to {output_file}")

# Close the browser
driver.quit()
