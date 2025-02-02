import csv
import requests
import re
import sys
import time
from bs4 import BeautifulSoup
from app.login import login_and_get_cookies, create_session_with_cookies

# 🔹 Základné nastavenia
WATCHLIST_URL = "https://www.csfd.cz/soukrome/chci-videt/?filmType=0"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔹 1️⃣ Stiahni zoznam filmov z "Chci vidět"
def get_watchlist(session):
    movies = []
    page = 1
    previous_titles = []

    while True:
        url = f"{WATCHLIST_URL}&page={page}"
        response = session.get(url, headers=HEADERS)
        time.sleep(0.5)  # Prevencia proti rate-limitingu

        if response.status_code != 200:
            print("❌ Chyba pri načítaní stránky!")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        movie_rows = soup.select("h3.film-title-nooverflow a.film-title-name")

        if not movie_rows:
            break  # Ak už nie sú ďalšie filmy, ukonči
        
        current_titles = [row.text.strip() for row in movie_rows]

        # Ak sa názvy filmov na stránke nezmenili, znamená to, že sme na poslednej stránke
        if current_titles == previous_titles:
            break

        print(f"🔄 Spracovávam stránku {page}...")
        for row in movie_rows:
            title = row.text.strip()
            link = "https://www.csfd.cz" + row["href"]

            # Získať rok vzniku filmu
            year_tag = row.find_next("span", class_="film-title-info")
            year = re.search(r"\d{4}", year_tag.text).group(0) if year_tag else "N/A"

            movies.append({"title": title, "year": year, "link": link, "totalRatings": 0})

        # Uložíme názvy filmov z tejto stránky pre porovnanie na ďalšiu stránku
        previous_titles = current_titles

        page += 1  # Posun na ďalšiu stránku

    return movies

# 🔹 2️⃣ Získať počet hodnotení pre každý film
def get_ratings_count(movie_url, current_index, total_movies):
    retries = 3
    while retries > 0:
        response = requests.get(movie_url, headers=HEADERS, timeout=10)
        time.sleep(0.1)  # Prevent rate limiting

        if response.status_code != 200:
            print(f"❌ Chyba pri načítaní stránky: {movie_url}")
            retries -= 1
            time.sleep(2)
            return 0

        soup = BeautifulSoup(response.text, "html.parser")

        rating_count_tag = soup.select_one("li.tab-nav-item.ratings-btn.active span.counter")

        if rating_count_tag:
            rating_count_text = rating_count_tag.text.strip()
            rating_count = int(re.sub(r"\D", "", rating_count_text))  # Odstráni nečíselné znaky

            # Prekreslíme riadok s aktuálnym počítadlom
            sys.stdout.write(f"\rZpracováno: {current_index + 1} / {total_movies} filmů.")
            sys.stdout.flush()  # Tento príkaz zabezpečí, že sa výstup okamžite zobrazí
            return rating_count
        
        sys.stdout.write(f"\rZpracováno: {current_index + 1} / {total_movies} filmů.")
        sys.stdout.flush()  # Tento príkaz zabezpečí, že sa výstup okamžite zobrazí
        return 0 # Ak sa nepodarí nájsť údaj, vráti 0
    
    return 0  # Ak sa nepodarí nájsť údaj, vráti 0

# 🔹 3️⃣ Uloženie dát do CSV (bez filmov s 0 hodnoteniami)
def save_to_csv(movies, filename="watchlist_sorted.csv"):
    # Odstrániť filmy s 0 hodnoteniami
    filtered_movies = [movie for movie in movies if movie["totalRatings"] > 0]
    # Odstrániť "link" zo všetkých slovníkov
    for movie in movies:
        movie.pop("link", None)  # Bezpečne odstráni kľúč, ak existuje

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "year", "totalRatings"])
        writer.writeheader()
        writer.writerows(filtered_movies)

    print(f"\n✅ Dáta boli uložené do {filename} (počet filmov: {len(filtered_movies)})")

# 🔹 4️⃣ Hlavná funkcia
def main():
    cookies = login_and_get_cookies()
    if cookies:
        session = create_session_with_cookies(cookies)
        watchlist = get_watchlist(session)

        total_movies = len(watchlist)  
        # Počet filmov na spracovanie
        for index, movie in enumerate(watchlist):
            movie["totalRatings"] = get_ratings_count(movie["link"], index, total_movies)  # Získaj počet hodnotení

        # Zoradiť filmy podľa počtu hodnotení (od najviac hodnotených)
        watchlist_sorted = sorted(watchlist, key=lambda x: x["totalRatings"], reverse=True)

        save_to_csv(watchlist_sorted)

if __name__ == "__main__":
    main()
