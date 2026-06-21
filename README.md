# Pet project: Movies dashboard

Live [dashboard](https://kburkin-movie-list.streamlit.app/) with table movies that I have seen and liked.  
Below the table you can find curious statistics about them.

## Motivation for this project
- I want to keep detailed log of movies I watched 
- Analyze what genres or directors I prefer
- Retrospect how my tastes change over time
- Share the movies I liked with my friends

## Data sources
- Initially, I used the movies list, that I kept over years. The last version of that list was published on [google spreadsheets](https://docs.google.com/spreadsheets/d/1zDdGrNWN3QnSgB_7Tj-hoDe1mEKkivMk/edit?usp=sharing&ouid=106349676610417203719&rtpof=true&sd=true) until I moved the logs here.
- I obtain additional movie credentials from [omdbapi.com](https://www.omdbapi.com/).

## Features

### 🎬 Movie Tracking
- Detailed log of watched movies with ratings and metadata
- Integration with OMDB and TMDB APIs for enriched movie data
- Interactive dashboard with statistics and analytics

### 🤖 AI-Powered Recommendations
- **Collaborative filtering** recommendation system
- Analyzes your last 6 months of viewing history
- Discovers similar movies from TMDB's extensive database
- Generates 5 personalized movie recommendations
- **Automatic weekly retraining** every Monday at 9:17 AM

[View Recommendation System Documentation →](docs/RECOMMENDATION_SYSTEM.md)

## Future work
- to make movies table interactive (sorting, filtering)
- add subpages with analytics
- integrate recommendations into the dashboard