"""
PyTest tests for movielens_analysis module.
"""
import pytest
from movielens_analysis import Tests


@pytest.fixture(scope='module')
def t():
    return Tests(
        movies_path='movies.csv',
        ratings_path='ratings.csv',
        tags_path='tags.csv',
        links_path='links.csv',
    )


def test_movies_dist_by_release(t):
    t.test_movies_dist_by_release()

def test_movies_dist_by_genres(t):
    t.test_movies_dist_by_genres()

def test_movies_most_genres(t):
    t.test_movies_most_genres()

def test_tags_most_words(t):
    t.test_tags_most_words()

def test_tags_longest(t):
    t.test_tags_longest()

def test_tags_most_popular(t):
    t.test_tags_most_popular()

def test_ratings_movies_dist_by_year(t):
    t.test_ratings_movies_dist_by_year()

def test_ratings_movies_dist_by_rating(t):
    t.test_ratings_movies_dist_by_rating()

def test_ratings_top_by_num_of_ratings(t):
    t.test_ratings_top_by_num_of_ratings()

def test_ratings_top_by_ratings(t):
    t.test_ratings_top_by_ratings()

def test_ratings_top_controversial(t):
    t.test_ratings_top_controversial()

def test_ratings_users_dist_by_num_of_ratings(t):
    t.test_ratings_users_dist_by_num_of_ratings()

def test_links_data_loaded(t):
    t.test_links_data_loaded()
