import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

# Načítanie .env premenných
load_dotenv()

USERNAME = os.getenv("CSFD_USERNAME")
PASSWORD = os.getenv("CSFD_PASSWORD")
LOGIN_URL = "https://www.csfd.cz/prihlaseni/"

def login_and_get_cookies():
    """Prihlási sa na ČSFD a vráti cookies na ďalšie použitie."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Skryje prehliadač
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(LOGIN_URL)
        time.sleep(2)

        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        time.sleep(2)  # Počkáme na načítanie stránky

        if "Odhlásit" in driver.page_source:
            print("✅ Prihlásenie úspešné!")
        else:
            print("❌ Prihlásenie zlyhalo!")
            return None

        cookies = driver.get_cookies()  # Uloží cookies
        return cookies

    finally:
        driver.quit()

def create_session_with_cookies(cookies):
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])
    return session