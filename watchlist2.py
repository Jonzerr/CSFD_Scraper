import csv
import requests
import re
import sys
import time
from bs4 import BeautifulSoup
from app.login import login_and_get_cookies, create_session_with_cookies

# 🔹 Základné nastavenia
WATCHLIST_URL = "https://www.csfd.cz/soukrome/chci-videt/?filmType=1"  #?filmType=0
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔹 1️⃣ Stiahni zoznam filmov z "Chci vidět"
def get_watchlist(session):
    movies = []
    page = 1
    previous_titles = []

    while True:
        url = f"{WATCHLIST_URL}&page={page}"
        print(url)
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

            movies.append({
                "title": title, 
                "englishTitle": "",
                "year": year, 
                "link": link, 
                "totalRatings": 0,
                "genres": "",
                "plot": ""
            })

        # Uložíme názvy filmov z tejto stránky pre porovnanie na ďalšiu stránku
        previous_titles = current_titles

        page += 1  # Posun na ďalšiu stránku

    return movies

# 🔹 2️⃣ Získať detailné informácie o filme (hodnotenia, žánre, anglický názov, obsah)
def get_movie_details(movie_url, current_index, total_movies):
    retries = 3
    while retries > 0:
        response = requests.get(movie_url, headers=HEADERS, timeout=10)
        time.sleep(0.1)  # Prevent rate limiting

        if response.status_code != 200:
            print(f"❌ Chyba pri načítaní stránky: {movie_url}")
            retries -= 1
            time.sleep(2)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Získať počet hodnotení
        rating_count = 0
        rating_count_tag = soup.select_one("li.tab-nav-item.ratings-btn.active span.counter")
        if rating_count_tag:
            rating_count_text = rating_count_tag.text.strip()
            rating_count = int(re.sub(r"\D", "", rating_count_text))

        # Získať anglický názov
        english_title = ""
        english_title_tag = soup.select_one("ul.names li[title]")
        if english_title_tag:
            english_title = english_title_tag.text.strip()
        
        # Získať žánre
        genres = []
        genres_div = soup.select_one("div.genres")
        if genres_div:
            genre_links = genres_div.select("a")
            genres = [genre.text.strip() for genre in genre_links]
        genres_str = " / ".join(genres) if genres else ""
        
        # Získať obsah/popis
        plot = ""
        plot_div = soup.select_one("div.plot-full")
        if plot_div:
            # Získať text a odstrániť nadbytočné medzery
            plot_text = plot_div.get_text(separator=" ", strip=True)
            # Vyčistiť text od viacerých medzier
            plot = re.sub(r'\s+', ' ', plot_text).strip()

        # Prekreslíme riadok s aktuálnym počítadlom
        sys.stdout.write(f"\rZpracováno: {current_index + 1} / {total_movies} filmů.")
        sys.stdout.flush()
        
        return {
            "totalRatings": rating_count,
            "englishTitle": english_title,
            "genres": genres_str,
            "plot": plot
        }
    
    return {
        "totalRatings": 0,
        "englishTitle": "",
        "genres": "",
        "plot": ""
    }

# 🔹 3️⃣ Uloženie dát do CSV (bez filmov s 0 hodnoteniami)
def save_to_csv(movies, filename="watchlist_sorted.csv"):
    # Odstrániť filmy s 0 hodnoteniami
    filtered_movies = [movie for movie in movies if movie["totalRatings"] > 0]
    # Odstrániť "link" zo všetkých slovníkov
    for movie in filtered_movies:
        movie.pop("link", None)  # Bezpečne odstráni kľúč, ak existuje

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "englishTitle", "year", "totalRatings", "genres", "plot"])
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
            details = get_movie_details(movie["link"], index, total_movies)
            movie["totalRatings"] = details["totalRatings"]
            movie["englishTitle"] = details["englishTitle"]
            movie["genres"] = details["genres"]
            movie["plot"] = details["plot"]

        # Zoradiť filmy podľa počtu hodnotení (od najviac hodnotených)
        watchlist_sorted = sorted(watchlist, key=lambda x: x["totalRatings"], reverse=True)

        save_to_csv(watchlist_sorted)

if __name__ == "__main__":
    main()