import csv
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from app.login import login_and_get_cookies
from app.login import create_session_with_cookies


# 🔹 Načítanie .env súboru
load_dotenv()

# 🔑 Použitie premenných z .env
USER_ID = os.getenv("CSFD_USER_ID")


# URL adresy
BASE_URL = f"https://www.csfd.cz/uzivatel/{USER_ID}/hodnoceni/?type=0&sort=rating" # type=0 - filmy, 

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 🔹 1️⃣Použitie cookies v Requests.Session()


# 🔹 2️⃣ Funkcia na sťahovanie filmov zo stránky hodnotení
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

# 🔹 3️⃣ Stiahnutie všetkých hodnotení
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

# 🔹 4️⃣ Uloženie dát do CSV
def save_to_csv(movies, filename="movies_ratings.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["title", "year", "rating"])
        writer.writeheader()
        writer.writerows(movies)

    print(f"✅ Dáta boli uložené do súboru {filename}")

# ✅ Spustenie procesu
def main():
    cookies = login_and_get_cookies()
    if cookies:
        session = create_session_with_cookies(cookies)
        ratings = get_all_ratings(session)
        save_to_csv(ratings)

if __name__ == "__main__":
    main()