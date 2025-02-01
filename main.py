from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import requests
from bs4 import BeautifulSoup
import csv
import os
from dotenv import load_dotenv

# 🔹 Načítanie .env súboru
load_dotenv()

# 🔑 Použitie premenných z .env
USERNAME = os.getenv("CSFD_USERNAME")
PASSWORD = os.getenv("CSFD_PASSWORD")
USER_ID = os.getenv("CSFD_USER_ID")


# URL adresy
LOGIN_URL = "https://www.csfd.cz/prihlaseni/"
BASE_URL = f"https://www.csfd.cz/uzivatel/{USER_ID}/hodnoceni/?type=0"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 🔹 1️⃣ Prihlásenie cez Selenium a získanie cookies
def login_and_get_cookies():
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Skryje prehliadač
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(LOGIN_URL)
    time.sleep(2)

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

    time.sleep(2)  # Počkáme, kým sa načíta stránka

    if "Odhlásit" in driver.page_source:
        print("✅ Prihlásenie úspešné!")
    else:
        print("❌ Prihlásenie zlyhalo!")
        driver.quit()
        return None

    cookies = driver.get_cookies()  # Získame cookies
    driver.quit()
    return cookies

# 🔹 2️⃣ Použitie cookies v Requests.Session()
def create_session_with_cookies(cookies):
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])
    return session

# 🔹 3️⃣ Funkcia na sťahovanie filmov zo stránky hodnotení
def get_ratings(session, page=1):
    url = f"{BASE_URL}&page={page}"
    response = session.get(url, headers=HEADERS)

    if response.status_code != 200:
        print("Chyba pri sťahovaní stránky")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    movies = []

    for row in soup.find_all("tr"):
        title_tag = row.select_one(".film-title-name")
        year_tag = row.select_one(".film-title-info .info")
        rating_tag = row.select_one(".stars")

        if title_tag and rating_tag:
            title = title_tag.text.strip()  # Originálny názov filmu
            year = year_tag.text.split('(')[-1].split(')')[0] if year_tag else "Neznámy rok"
            rating_value = rating_tag.get("class", [])[-1].replace("stars-", "") if rating_tag else "0"
            rating = f"{rating_value}/5"

            movies.append({
                "title": title,
                "year": year,
                "rating": rating
            })

    return movies

# 🔹 4️⃣ Stiahnutie všetkých hodnotení
def get_all_ratings(session):
    all_ratings = []
    page = 1

    while True:
        print(f"🔄 Spracovávam stránku {page}...")
        ratings = get_ratings(session, page)

        if not ratings:
            break  # Ak stránka neobsahuje žiadne filmy, končíme
        
        all_ratings.extend(ratings)
        page += 1

    return all_ratings

# 🔹 5️⃣ Uloženie dát do CSV
def save_to_csv(movies, filename="movies_ratings.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["title", "year", "rating"])
        writer.writeheader()
        writer.writerows(movies)

    print(f"✅ Dáta boli uložené do súboru {filename}")

# ✅ Spustenie procesu
cookies = login_and_get_cookies()
if cookies:
    session = create_session_with_cookies(cookies)
    ratings = get_all_ratings(session)
    save_to_csv(ratings)