import pandas as pd

def calculate_recommendations(user_input, num_recommendations=3):
    tags_df = pd.read_csv('movielens-data/tags.csv')

    user_input = list(map(int, user_input))

    # Get common tags for the input movieIds
    common_tags = tags_df[tags_df['movieId'].isin(user_input)]['tag'].tolist()

    # Extract movie IDs from tags that have common tags
    movie_ids_to_show = tags_df[
        (tags_df['tag'].isin(common_tags)) &
        (~tags_df['movieId'].isin(user_input))
    ]['movieId'].unique().tolist()

    # Weighted tag matching
    tag_weights = {tag: common_tags.count(tag) for tag in common_tags}
    total_weight = sum(tag_weights.values())

    # Calculate weights for each movie based on common tags
    movie_weights = {}
    for movie_id in movie_ids_to_show:
        movie_tags = tags_df[tags_df['movieId'] == movie_id]['tag'].tolist()
        weight = sum(tag_weights.get(tag, 0) for tag in movie_tags)
        movie_weights[movie_id] = weight / total_weight

    # Sort movies by weights
    sorted_movies = sorted(movie_weights.items(), key=lambda x: x[1], reverse=True)

    # Get the top num_recommendations movies
    top_movies = sorted_movies[:num_recommendations]

    # Query the database to find movies with similar tags and order by the score column
    query = f"""
        SELECT movieId, title, year, score
        FROM movies
        WHERE movieId IN ({', '.join(map(str, [movie[0] for movie in top_movies]))})
    """

    return query