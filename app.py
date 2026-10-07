
from flask import Flask, render_template, request, jsonify
import pandas as pd
import pickle
import requests
import os
from functools import lru_cache
import os
import requests

MOVIES_URL = os.environ["MOVIES_URL"]
SIMILARITY_URL = os.environ["SIMILARITY_URL"]


def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

        print(f"{filename} downloaded.")


download_file(MOVIES_URL, "movies.pkl")
download_file(SIMILARITY_URL, "similarity.pkl")
# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)


# ============================================================
# LOAD ML MODEL
# ============================================================

try:
    with open("movies.pkl", "rb") as file:
        movies = pickle.load(file)

    with open("similarity.pkl", "rb") as file:
        similarity = pickle.load(file)

except FileNotFoundError:
    raise FileNotFoundError(
        "movies.pkl and similarity.pkl must be in the same "
        "folder as app.py"
    )


# Make sure movies is a DataFrame
if not isinstance(movies, pd.DataFrame):
    movies = pd.DataFrame(movies)


# ============================================================
# VALIDATE DATASET
# ============================================================

required_columns = ["title", "movie_id"]

for column in required_columns:

    if column not in movies.columns:

        raise ValueError(
            f"movies.pkl does not contain '{column}' column."
        )


# ============================================================
# TMDB CONFIGURATION
# ============================================================

TMDB_TOKEN = os.environ.get("TMDB_API_KEY", "").strip()

TMDB_API = "https://api.themoviedb.org/3"

TMDB_IMAGE = "https://image.tmdb.org/t/p"


TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json"
}


# ============================================================
# GET TMDB MOVIE DETAILS
# ============================================================

@lru_cache(maxsize=1000)
def get_movie_details(movie_id):

    if not TMDB_TOKEN:

        print("WARNING: TMDB_API_KEY is not configured.")

        return None

    try:

        response = requests.get(

            f"{TMDB_API}/movie/{int(movie_id)}",

            headers=TMDB_HEADERS,

            params={
                "language": "en-US"
            },

            timeout=10
        )

        print(
            f"TMDB request: {movie_id} "
            f"-> {response.status_code}"
        )

        if response.status_code == 200:

            return response.json()

        else:

            print(
                "TMDB Error:",
                response.text[:300]
            )

    except requests.RequestException as error:

        print(
            "TMDB connection error:",
            error
        )

    return None


# ============================================================
# GET POSTER
# ============================================================

@lru_cache(maxsize=1000)
def get_poster(movie_id, title):

    details = get_movie_details(movie_id)

    # --------------------------------------------------------
    # TMDB POSTER
    # --------------------------------------------------------

    if details:

        poster_path = details.get("poster_path")

        if poster_path:

            return (
                f"{TMDB_IMAGE}/w500"
                f"{poster_path}"
            )

    # --------------------------------------------------------
    # IMDb FALLBACK
    # --------------------------------------------------------

    try:

        query = str(title).strip().replace(" ", "_")

        url = (
            "https://v3.sg.media-imdb.com/"
            f"suggestion/x/{query}.json"
        )

        response = requests.get(

            url,

            headers={
                "User-Agent": "Mozilla/5.0"
            },

            timeout=5
        )

        if response.status_code == 200:

            data = response.json()

            results = data.get("d", [])

            # Try to find a movie matching the title
            for movie in results:

                movie_title = str(
                    movie.get("l", "")
                ).strip().lower()

                if (
                    movie_title
                    == str(title).strip().lower()
                ):

                    image = movie.get("i")

                    if image:

                        image_url = image.get(
                            "imageUrl"
                        )

                        if image_url:

                            return image_url

            # General fallback
            for movie in results:

                image = movie.get("i")

                if image:

                    image_url = image.get(
                        "imageUrl"
                    )

                    if image_url:

                        return image_url

    except requests.RequestException as error:

        print(
            "IMDb image error:",
            error
        )

    return None


# ============================================================
# GET BACKDROP
# ============================================================

@lru_cache(maxsize=1000)
def get_backdrop(movie_id, title=""):

    details = get_movie_details(movie_id)

    # --------------------------------------------------------
    # TMDB BACKDROP
    # --------------------------------------------------------

    if details:

        backdrop_path = details.get(
            "backdrop_path"
        )

        if backdrop_path:

            return (
                f"{TMDB_IMAGE}/original"
                f"{backdrop_path}"
            )

        # ----------------------------------------------------
        # If backdrop is unavailable, use poster as fallback
        # ----------------------------------------------------

        poster_path = details.get(
            "poster_path"
        )

        if poster_path:

            return (
                f"{TMDB_IMAGE}/original"
                f"{poster_path}"
            )

    # --------------------------------------------------------
    # IMDb IMAGE FALLBACK
    # --------------------------------------------------------

    poster = get_poster(
        movie_id,
        title
    )

    return poster


# ============================================================
# MOVIE INFORMATION
# ============================================================

def format_movie(movie):

    movie_id = int(movie["movie_id"])

    title = str(movie["title"])

    details = get_movie_details(movie_id)

    # --------------------------------------------------------
    # DEFAULT DATA
    # --------------------------------------------------------

    result = {

        "title": title,

        "movie_id": movie_id,

        "poster": get_poster(
            movie_id,
            title
        ),

        "backdrop": get_backdrop(
            movie_id,
            title
        ),

        "rating": 0,

        "year": "",

        "genres": [],

        "overview": (
            "Movie information unavailable."
        )
    }

    # --------------------------------------------------------
    # TMDB DATA
    # --------------------------------------------------------

    if details:

        # Rating
        rating = details.get(
            "vote_average"
        )

        if rating is not None:

            result["rating"] = round(
                float(rating),
                1
            )

        # Release year
        release_date = details.get(
            "release_date",
            ""
        )

        if release_date:

            result["year"] = release_date[:4]

        # Genres
        result["genres"] = [

            genre.get("name")

            for genre in details.get(
                "genres",
                []
            )

            if genre.get("name")
        ][:3]

        # Overview
        overview = details.get(
            "overview"
        )

        if overview:

            result["overview"] = overview

    return result


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

def recommend(
    movie_title,
    number_of_movies=10
):

    titles = movies["title"].astype(str)

    # Exact case-insensitive match
    matches = titles[
        titles.str.strip().str.lower()
        == movie_title.strip().lower()
    ]

    if len(matches) == 0:

        return []

    index = matches.index[0]

    distances = similarity[index]

    movie_list = sorted(

        enumerate(distances),

        reverse=True,

        key=lambda x: x[1]
    )

    recommendations = []

    for movie_index, score in movie_list[1:]:

        if len(recommendations) >= number_of_movies:

            break

        movie = movies.iloc[movie_index]

        recommendations.append({

            "title": str(
                movie["title"]
            ),

            "movie_id": int(
                movie["movie_id"]
            ),

            "score": float(score)

        })

    return recommendations


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    movie_titles = (

        movies["title"]

        .astype(str)

        .drop_duplicates()

        .sort_values()

        .tolist()
    )

    return render_template(

        "index.html",

        movie_titles=movie_titles
    )


# ============================================================
# RECOMMENDATION API
# ============================================================

@app.route(
    "/recommend",
    methods=["POST"]
)
def recommendation_api():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "error":
                "No data received."

            }), 400

        movie_title = data.get(
            "movie",
            ""
        ).strip()

        if not movie_title:

            return jsonify({

                "error":
                "Movie title is required."

            }), 400

        # ----------------------------------------------------
        # RECOMMENDATIONS
        # ----------------------------------------------------

        recommendations = recommend(
            movie_title,
            10
        )

        if not recommendations:

            return jsonify({

                "error":
                f"Movie '{movie_title}' not found."

            }), 404

        # ----------------------------------------------------
        # SELECTED MOVIE
        # ----------------------------------------------------

        selected_rows = movies[

            movies["title"]

            .astype(str)

            .str.strip()

            .str.lower()

            == movie_title.lower()

        ]

        selected_movie = None

        if len(selected_rows) > 0:

            selected_movie = format_movie(

                selected_rows.iloc[0]

            )

        # ----------------------------------------------------
        # RECOMMENDED MOVIES
        # ----------------------------------------------------

        result = []

        for movie in recommendations:

            result.append(

                format_movie(movie)

            )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "selected": selected_movie,

            "recommendations": result

        })

    except Exception as error:

        print(
            "Recommendation error:",
            error
        )

        return jsonify({

            "error":
            "Internal server error."

        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )





# if __name__ == "__main__":
#     print("\n========== ML MODEL TEST ==========")

#     test_movie = "Avatar"   # CHANGE THIS to a movie in your dataset

#     results = recommend(test_movie, 10)

#     print(f"\nInput movie: {test_movie}")
#     print("Recommendations from similarity.pkl:")

#     for i, movie in enumerate(results, 1):
#         print(
#             f"{i}. {movie['title']} "
#             f"(similarity={movie['score']:.4f})"
#         )

#     print("===================================\n")

#     app.run(
#         debug=True,
#         host="127.0.0.1",
#         port=5000
#     )
