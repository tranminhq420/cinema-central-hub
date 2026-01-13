import json
import pymysql
from datetime import datetime
from pprint import pprint
from datetime import datetime


DB_CONFIG = {
    "host": "db",
    "user": "newuser",
    "password": "123quan123",
    "database": "hanoicinema",
    "port": 3306,
    "charset": "utf8mb4",
    "use_unicode": True
}


def load_json():
    with open("cgv-movies.json", "r", encoding="utf-8") as f:
        return json.load(f)


def upsert_theater(cur, item):
    screenings = item.get("screenings", {})
    for screening in screenings:
        cinemas = screening.get("cinemas", {})
        for cinema in cinemas:
            theater_id = cinema.get("cinema_id")
            # print(theater_id)
            name = cinema.get("cinema_name")

            location = cinema.get("address")

            cur.execute(
                """
                INSERT INTO cinemas (theater_id, name, location)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE theater_id = LAST_INSERT_ID(theater_id)
                """,
                (
                    theater_id,
                    name,
                    location
                )
            )


def upsert_films(cur, item):
    movie = item.get("movie", {})

    cur.execute(
        """
        INSERT INTO films (
            cgv_id,
            title,
            age_limit,
            movie_type,
            format,
            genre,
            image_url,
            booking_url,
            created_at
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        ON DUPLICATE KEY UPDATE
            id = LAST_INSERT_ID(id),
            title = VALUES(title),
            age_limit = VALUES(age_limit),
            movie_type = VALUES(movie_type),
            format = VALUES(format),
            genre = VALUES(genre),
            image_url = VALUES(image_url),
            booking_url = VALUES(booking_url)
        """,
        (
            movie.get("id"),                       # cgv_id (slug)
            movie.get("title"),
            movie.get("rating", {}).get("code"),
            movie.get("subtitle"),
            "2D",
            ",".join(movie.get("genres", [])),
            movie.get("poster_url"),
            movie.get("booking_url"),
        )
    )

    film_id = movie.get("id")
    return film_id


def upsert_screentimes(cur, item, film_id):
    screenings = item.get("screenings", [])

    for screening in screenings:
        cinemas = screening.get("cinemas", [])

        for cinema in cinemas:
            cinema_code = cinema.get("cinema_id")

            rooms = cinema.get("rooms", [])
            for room in rooms:
                room_code = room.get("room_id")
                room_name = room.get("room_name")

                showtimes = room.get("showtimes", [])
                for show in showtimes:
                    iso_time = show.get("start_time")
                    t = datetime.fromisoformat(iso_time)
                    time = t.time().strftime("%H:%M:%S")
                    booking_url = show.get("booking_url")
                    seats = show.get("seats", [])
                    standard_price = 0
                    vip_price = 0
                    for seat in seats:
                        if seat.get("type") == "standard":
                            standard_price = seat.get("price")
                        elif seat.get("type") == "vip":
                            vip_price = seat.get("price")
                    version = show.get("version")
                    cur.execute(
                        """
                        INSERT INTO screentimes (name, format, time, date, cinema_id, film_id, created_at,standard_price,vip_price, booking_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
                        """,
                        (
                            room_name,
                            version,
                            time,
                            screening.get("date"),
                            cinema_code,
                            film_id,
                            datetime.now(),
                            standard_price,
                            vip_price,
                            booking_url
                        )
                    )


def main():
    print("START IMPORT")

    raw = load_json()

    movies = raw if isinstance(raw, list) else raw.get("data", [])
    print("Total movies:", len(movies))

    conn = pymysql.connect(
        host="db",
        user="newuser",
        password="123quan123",
        database="hanoicinema",
        port=3306,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor
    )
    cur = conn.cursor()
    for movie in movies:
        upsert_theater(cur, movie)
        film_id = upsert_films(cur, movie)
        print(film_id)
        upsert_screentimes(cur, movie, film_id)
    conn.commit()
    cur.close()
    conn.close()

    print("IMPORT DONE")


if __name__ == "__main__":
    main()
