import requests
from bs4 import BeautifulSoup
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from webdriver_manager.chrome import ChromeDriverManager
import tempfile

# --- Configuration ---
SSSB_URL = "https://minasidor.sssb.se/en/available-apartments?oboTyper=BOASR&hyraMax=6000"
CHECK_INTERVAL = 3600  # Check every hour
STATE_FILE = "seen_apartments.txt"



# Email setup
EMAIL_FROM =  os.environ["GMAIL_USER"]
EMAIL_TO =  os.environ["RECEIVING_USER"]
EMAIL_SUBJECT = "New SSSB Apartment Available"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER =  os.environ["GMAIL_USER"]
SMTP_PASS = os.environ["GMAIL_PASSWORD"]

# Set up Selenium WebDriver
user_data_dir = tempfile.mkdtemp(prefix="chrome_user_data_")
chromeOptions = Options()
chromeOptions.add_argument(f"user-data-dir={user_data_dir}")

# chromeOptions.add_argument("--headless")  # Run in headless mode
driver =  webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)

def get_apartments():
    apartments = []
    driver.get(SSSB_URL)
    time.sleep(5)  # Wait for the page to load
    page_idx = 1
    while True:
        # Locate the apartment listings
        apt_divs = driver.find_elements(By.CSS_SELECTOR, "div.appartment.row")
        
        if not apt_divs:  # Break if no apartments are found
            break

        for apt_div in apt_divs:
            title_element = apt_div.find_element(By.CSS_SELECTOR, "h2.apt-title a")
            address_element = apt_div.find_element(By.CSS_SELECTOR, "p.apt-address")
            details_elements = apt_div.find_elements(By.CSS_SELECTOR, "ul.apt-details-data li")

            if not title_element or not address_element or len(details_elements) < 4:
                continue

            apt = {
                "title": title_element.text.strip(),
                "url": title_element.get_attribute("href"),
                "address": address_element.text.strip(),
                "area": details_elements[0].text.strip(),
                "size": details_elements[1].text.strip(),
                "rent": details_elements[2].text.strip(),
                "move_in": details_elements[3].text.strip(),
            }

            apartments.append(apt)
        print(f"Page {page_idx} scraped.")
        
        # Check for the next page link
        try:
            # Find the next pagination link
            # <a href="http://minasidor.sssb.se/en/available-apartments/?pagination=2&amp;paginationantal=10">3</a
            next_page_link = driver.find_element(By.XPATH, f"//a[contains(@href, 'pagination={page_idx}')]")
            next_page_url = next_page_link.get_attribute("href")
            driver.get(next_page_url)
            time.sleep(5)  # Wait for the next page to load
            page_idx += 1
        except Exception as e:
            print("No more pages or error")
            break

    return apartments


def get_apartment_hash(apt):
    string = f"{apt['title']}-{apt['address']}-{apt['move_in']}"
    return hashlib.sha256(string.encode()).hexdigest()

def load_seen_apartments():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_seen_apartment(apt_hashes):
    with open(STATE_FILE, "a") as f:
        for h in apt_hashes:
            f.write(h + "\n")

def send_email(new_apartments):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    body = "New apartments have been listed:\n\n"
    for apt in new_apartments:
        body += f"{apt['title']} at {apt['address']}\nRent: {apt['rent']}\nMove-in: {apt['move_in']}\nLink: {apt['url']}\n\n"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("Email sent.")

def main():
    while True:
        try:
            seen = load_seen_apartments()
            apartments = get_apartments()

            new_apt_hashes = []
            new_apt_data = []

            for apt in apartments:
                apt_hash = get_apartment_hash(apt)
                if apt_hash not in seen:
                    new_apt_hashes.append(apt_hash)
                    new_apt_data.append(apt)

            if new_apt_data:
                send_email(new_apt_data)
                save_seen_apartment(new_apt_hashes)
            else:
                print("No new apartments.")

            # Wait for 1 minute before checking again
            time.sleep(600)
        except Exception as e:
            print(e)
            time.sleep(10)
            

if __name__ == "__main__":
    main()
