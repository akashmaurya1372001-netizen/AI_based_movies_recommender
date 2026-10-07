
// ============================================================
// ELEMENTS
// ============================================================

const movieSearch =
    document.getElementById("movieSearch");

const recommendButton =
    document.getElementById("recommendButton");

const hero =
    document.getElementById("hero");

const heroBackground =
    document.getElementById("heroBackground");

const heroTitle =
    document.getElementById("heroTitle");

const heroMeta =
    document.getElementById("heroMeta");

const heroOverview =
    document.getElementById("heroOverview");

const recommendationsSection =
    document.getElementById(
        "recommendationsSection"
    );

const recommendationsContainer =
    document.getElementById(
        "recommendations"
    );

const loading =
    document.getElementById("loading");

const errorMessage =
    document.getElementById(
        "errorMessage"
    );

const searchMessage =
    document.getElementById(
        "searchMessage"
    );



// ============================================================
// SEARCH WITH ENTER
// ============================================================

movieSearch.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            event.preventDefault();

            getRecommendations();

        }

    }
);



// ============================================================
// GET RECOMMENDATIONS
// ============================================================

async function getRecommendations() {

    const movieName =
        movieSearch.value.trim();


    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    if (!movieName) {

        showSearchMessage(
            "Please enter a movie name."
        );

        movieSearch.focus();

        return;

    }


    // --------------------------------------------------------
    // CLEAR PREVIOUS ERROR
    // --------------------------------------------------------

    hideError();

    searchMessage.textContent = "";


    // --------------------------------------------------------
    // LOADING
    // --------------------------------------------------------

    showLoading();


    recommendButton.disabled = true;

    recommendButton.textContent =
        "Finding movies...";


    try {

        // ----------------------------------------------------
        // SEND REQUEST TO FLASK
        // ----------------------------------------------------

        const response =
            await fetch(
                "/recommend",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        movie: movieName

                    })

                }
            );


        // ----------------------------------------------------
        // READ JSON
        // ----------------------------------------------------

        const data =
            await response.json();


        // ----------------------------------------------------
        // HANDLE ERROR
        // ----------------------------------------------------

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Movie not found."
            );

        }


        // ----------------------------------------------------
        // CHECK SELECTED MOVIE
        // ----------------------------------------------------

        if (!data.selected) {

            throw new Error(
                "Selected movie information is unavailable."
            );

        }


        // ----------------------------------------------------
        // DISPLAY HERO
        // ----------------------------------------------------

        displayHero(
            data.selected
        );


        // ----------------------------------------------------
        // DISPLAY RECOMMENDATIONS
        // ----------------------------------------------------

        displayRecommendations(
            data.recommendations || []
        );


        // ----------------------------------------------------
        // SCROLL TO HERO
        // ----------------------------------------------------

        setTimeout(
            function () {

                hero.scrollIntoView({

                    behavior: "smooth",

                    block: "start"

                });

            },
            100
        );


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );


        showError(
            error.message ||
            "Something went wrong. Please try again."
        );


        hideHero();

        hideRecommendations();


    } finally {

        // ----------------------------------------------------
        // STOP LOADING
        // ----------------------------------------------------

        hideLoading();


        recommendButton.disabled =
            false;

        recommendButton.textContent =
            "🔥 Get Recommendations";

    }

}



// ============================================================
// DISPLAY HERO
// ============================================================

function displayHero(movie) {

    if (!movie) {

        return;

    }


    // --------------------------------------------------------
    // TITLE
    // --------------------------------------------------------

    heroTitle.textContent =
        movie.title ||
        "Unknown Movie";


    // --------------------------------------------------------
    // BACKGROUND
    // --------------------------------------------------------

    let imageURL = null;


    if (movie.backdrop) {

        imageURL =
            movie.backdrop;

    } else if (movie.poster) {

        imageURL =
            movie.poster;

    }


    if (imageURL) {

        heroBackground.style.backgroundImage =
            `url("${imageURL}")`;

    } else {

        heroBackground.style.backgroundImage =
            "none";

    }


    // --------------------------------------------------------
    // META
    // --------------------------------------------------------

    let metaParts = [];


    // Rating

    if (
        movie.rating !== undefined &&
        movie.rating !== null &&
        Number(movie.rating) > 0
    ) {

        metaParts.push(
            `⭐ ${Number(movie.rating).toFixed(1)}/10`
        );

    }


    // Year

    if (movie.year) {

        metaParts.push(
            `📅 ${movie.year}`
        );

    }


    // Genres

    if (
        Array.isArray(movie.genres) &&
        movie.genres.length > 0
    ) {

        metaParts.push(
            `🎭 ${movie.genres.join(", ")}`
        );

    }


    heroMeta.textContent =
        metaParts.join("  •  ");


    // --------------------------------------------------------
    // OVERVIEW
    // --------------------------------------------------------

    heroOverview.textContent =
        movie.overview ||
        "No description available.";


    // --------------------------------------------------------
    // SHOW HERO
    // --------------------------------------------------------

    hero.classList.remove(
        "hidden"
    );

}



// ============================================================
// DISPLAY RECOMMENDATIONS
// ============================================================

function displayRecommendations(
    movies
) {

    recommendationsContainer.innerHTML =
        "";


    if (
        !movies ||
        movies.length === 0
    ) {

        hideRecommendations();

        return;

    }


    movies.forEach(
        function (movie) {

            const card =
                createMovieCard(movie);

            recommendationsContainer.appendChild(
                card
            );

        }
    );


    recommendationsSection.classList.remove(
        "hidden"
    );

}



// ============================================================
// CREATE MOVIE CARD
// ============================================================

function createMovieCard(movie) {

    const card =
        document.createElement(
            "div"
        );


    card.className =
        "movie-card";


    // --------------------------------------------------------
    // POSTER
    // --------------------------------------------------------

    const posterContainer =
        document.createElement(
            "div"
        );


    posterContainer.className =
        "movie-poster";


    const img =
        document.createElement(
            "img"
        );


    img.alt =
        movie.title ||
        "Movie poster";


    img.loading =
        "lazy";


    // Use poster

    if (movie.poster) {

        img.src =
            movie.poster;

    } else {

        img.src =
            createPlaceholder(
                movie.title
            );

    }


    // --------------------------------------------------------
    // IMAGE ERROR FALLBACK
    // --------------------------------------------------------

    img.onerror =
        function () {

            this.onerror = null;

            this.src =
                createPlaceholder(
                    movie.title
                );

        };


    posterContainer.appendChild(
        img
    );


    // --------------------------------------------------------
    // RATING
    // --------------------------------------------------------

    if (
        movie.rating !== undefined &&
        movie.rating !== null &&
        Number(movie.rating) > 0
    ) {

        const rating =
            document.createElement(
                "div"
            );


        rating.className =
            "movie-rating";


        rating.textContent =
            `⭐ ${Number(movie.rating).toFixed(1)}`;


        posterContainer.appendChild(
            rating
        );

    }


    // --------------------------------------------------------
    // INFO
    // --------------------------------------------------------

    const info =
        document.createElement(
            "div"
        );


    info.className =
        "movie-info";


    // Title

    const title =
        document.createElement(
            "div"
        );


    title.className =
        "movie-title";


    title.textContent =
        movie.title ||
        "Unknown Movie";


    info.appendChild(
        title
    );


    // Details

    const details =
        document.createElement(
            "div"
        );


    details.className =
        "movie-details";


    let detailsText = [];


    if (movie.year) {

        detailsText.push(
            movie.year
        );

    }


    if (
        movie.genres &&
        movie.genres.length
    ) {

        detailsText.push(
            movie.genres
                .slice(0, 2)
                .join(", ")
        );

    }


    if (
        detailsText.length === 0
    ) {

        details.textContent =
            "Recommended for you";

    } else {

        details.textContent =
            detailsText.join(
                " • "
            );

    }


    info.appendChild(
        details
    );


    // --------------------------------------------------------
    // ADD EVERYTHING
    // --------------------------------------------------------

    card.appendChild(
        posterContainer
    );

    card.appendChild(
        info
    );


    return card;

}



// ============================================================
// PLACEHOLDER IMAGE
// ============================================================

function createPlaceholder(
    title
) {

    const safeTitle =
        encodeURIComponent(
            title ||
            "Movie"
        );


    return (
        "https://placehold.co/500x750/" +
        "17171d/ffffff" +
        "?text=" +
        safeTitle
    );

}



// ============================================================
// SHOW LOADING
// ============================================================

function showLoading() {

    loading.classList.remove(
        "hidden"
    );

}



// ============================================================
// HIDE LOADING
// ============================================================

function hideLoading() {

    loading.classList.add(
        "hidden"
    );

}



// ============================================================
// SHOW ERROR
// ============================================================

function showError(
    message
) {

    errorMessage.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );

}



// ============================================================
// HIDE ERROR
// ============================================================

function hideError() {

    errorMessage.classList.add(
        "hidden"
    );

    errorMessage.textContent =
        "";

}



// ============================================================
// SEARCH MESSAGE
// ============================================================

function showSearchMessage(
    message
) {

    searchMessage.textContent =
        message;

}



// ============================================================
// HIDE HERO
// ============================================================

function hideHero() {

    hero.classList.add(
        "hidden"
    );

}



// ============================================================
// HIDE RECOMMENDATIONS
// ============================================================

function hideRecommendations() {

    recommendationsSection.classList.add(
        "hidden"
    );

    recommendationsContainer.innerHTML =
        "";

}
