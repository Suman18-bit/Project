from flask import Flask, render_template, request, jsonify
from model_loader import MovieRecommender
import os

app = Flask(__name__)
recommender = MovieRecommender()

@app.route('/')
def home():
    """Home page with search"""
    # Get some featured/popular movies for display
    featured = recommender.df.sample(6) if len(recommender.df) > 6 else recommender.df
    return render_template('index.html', featured=featured)

@app.route('/recommend', methods=['POST'])
def recommend():
    """Get recommendations for a movie"""
    movie_title = request.form.get('movie_title', '').strip()
    
    if not movie_title:
        return render_template('results.html', error="Please enter a movie title")
    
    recommendations = recommender.get_recommendations(movie_title)
    
    if recommendations is None:
        # Movie not found - suggest similar titles
        suggestions = recommender.search_movies(movie_title)
        return render_template('results.html', 
                             error=f"Movie '{movie_title}' not found",
                             suggestions=suggestions,
                             search_query=movie_title)
    
    return render_template('results.html', 
                         movie_title=movie_title,
                         recommendations=recommendations)

@app.route('/api/search')
def api_search():
    """AJAX endpoint for live search suggestions"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    suggestions = recommender.search_movies(query, limit=8)
    return jsonify(suggestions)

@app.route('/api/recommend/<movie_name>')
def api_recommend(movie_name):
    """API endpoint for recommendations"""
    recommendations = recommender.get_recommendations(movie_name)
    if recommendations:
        return jsonify({'success': True, 'data': recommendations})
    return jsonify({'success': False, 'error': 'Movie not found'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)