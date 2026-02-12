import pickle
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class MovieRecommender:
    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.df = None
        self.indices = None
        self.load_models()
    
    def load_models(self):
        """Load all pickle files"""
        with open('data/BOW.pkl', 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        with open('data/BOW_metrix.pkl', 'rb') as f:
            self.matrix = pickle.load(f)
        
        with open('data/df.pkl', 'rb') as f:
            self.df = pickle.load(f)
        
        with open('data/Indices.pkl', 'rb') as f:
            self.indices = pickle.load(f)
    
    def get_recommendations(self, title, top_n=10):
        """Get movie recommendations based on title"""
        try:
            # Find the index of the movie
            idx = self.indices[title]
            
            # Calculate similarity scores
            sim_scores = cosine_similarity(
                self.matrix[idx], 
                self.matrix
            ).flatten()
            
            # Get top similar movies (excluding the input movie)
            similar_indices = sim_scores.argsort()[::-1][1:top_n+1]
            
            # Return movie details
            recommendations = []
            for i in similar_indices:
                movie_data = self.df.iloc[i]
                recommendations.append({
                    'title': movie_data.get('title', 'Unknown'),
                    'similarity': round(sim_scores[i] * 100, 2),
                    'year': movie_data.get('year', 'N/A'),
                    'genre': movie_data.get('genre', 'N/A'),
                    'rating': movie_data.get('rating', 'N/A')
                })
            
            return recommendations
            
        except KeyError:
            return None
        except Exception as e:
            return str(e)
    
    def search_movies(self, query, limit=5):
        """Search for movies by partial title match"""
        matches = self.df[self.df['title'].str.contains(query, case=False, na=False)]
        return matches['title'].head(limit).tolist()