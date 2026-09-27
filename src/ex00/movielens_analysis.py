import csv
import datetime
import re
import time
import requests
import statistics
from bs4 import BeautifulSoup
from collections import Counter, OrderedDict


def read_file(filepath):
    """Read CSV file and return list of dictionaries"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return []
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []
    return data

def extract_year_from_title(title):
    """Extract year from movie title format: Title (Year)"""
    if not title:
        return None
    match = re.search(r'\((\d{4})\)', title)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to datetime object"""
    try:
        return datetime.datetime.fromtimestamp(int(timestamp))
    except (ValueError, TypeError, OSError):
        return None

def timestamp_to_year(timestamp):
    """Convert Unix timestamp to year"""
    dt = timestamp_to_datetime(timestamp)
    return dt.year if dt else None


class Movies:
    """Analyzing data from movies.csv"""
    
    def __init__(self, filepath):
        raw_data = read_file(filepath)
        self.data = []
        self.movie_titles = {}
        
        for row in raw_data:
            movie_id = int(row['movieId'])
            title = row['title']
            genres = row['genres']
            
            movie_info = {
                'movieId': movie_id,
                'title': title,
                'genres': genres,
                'year': extract_year_from_title(title),
                'genre_list': genres.split('|') if genres != '(no genres listed)' else []
            }
            
            self.data.append(movie_info)
            self.movie_titles[movie_id] = title
    
    def dist_by_release(self):
        """Returns a dict where keys are years and values are counts."""
        years = Counter()
        for movie in self.data:
            if movie['year']:
                years[movie['year']] += 1
        return OrderedDict(years.most_common())
    
    def dist_by_genres(self):
        """Returns a dict where keys are genres and values are counts."""
        genre = Counter()
        for movie in self.data:
            all_genres = movie['genre_list']
            for genr in all_genres:
                genre[genr] += 1
        return OrderedDict(genre.most_common())
    
    def most_genres(self, n):
        """Returns top-n movies with most genres."""
        movie_genre_counts = {}
        for movie in self.data:
            title = movie["title"]
            genre_counts = len(movie['genre_list'])
            movie_genre_counts[title] = genre_counts
        
        sorted_movies = sorted(movie_genre_counts.items(), 
                             key=lambda item: item[1], 
                             reverse=True)
        return dict(sorted_movies[:n])
    
    # BONUS METHOD 1
    def movies_by_year(self, year):
        """BONUS: Returns list of movie titles for a specific year."""
        movies_in_year = []
        for movie in self.data:
            if movie['year'] == year:
                movies_in_year.append(movie['title'])
        return sorted(movies_in_year)
    
    # BONUS METHOD 2
    def year_with_most_movies(self):
        """BONUS: Returns tuple (year, count) of year with most movies released."""
        dist = self.dist_by_release()
        if not dist:
            return (None, 0)
        year, count = next(iter(dist.items()))
        return (year, count)


class Tags:
    """Analyzing data from tags.csv"""
    
    def __init__(self, filepath):
        self.data = read_file(filepath)
        self.tags = [row["tag"] for row in self.data if "tag" in row]
    
    def most_words(self, n):
        """Returns top-n tags with most words inside."""
        without_dupe = set(self.tags)
        all_tags = list(without_dupe)
        big_tags_dict = {}
        
        for tag in all_tags:
            word = tag.split()
            big_tags_dict[tag] = len(word)
        
        sorted_tag = sorted(big_tags_dict.items(), 
                           key=lambda item: item[1], 
                           reverse=True)
        return dict(sorted_tag[:n])
    
    def longest(self, n):
        """Returns top-n longest tags by character count."""
        without_dupe = set(self.tags)
        all_tags = list(without_dupe)
        length_d = {}
        
        for tag in all_tags:
            length_d[tag] = len(tag)
        
        sorted_d = sorted(length_d.items(), 
                         key=lambda item: item[1], 
                         reverse=True)
        big_tags = [tag for tag, _ in sorted_d[:n]]
        return big_tags
    
    def most_words_and_longest(self, n):
        """Returns intersection of top-n tags with most words and longest tags."""
        most_w = set(self.most_words(n).keys())
        longest = set(self.longest(n))
        return list(longest & most_w)
    
    def most_popular(self, n):
        """Returns most popular tags."""
        counter = Counter(self.tags)
        return dict(counter.most_common(n))
    
    def tags_with(self, word):
        """Returns all unique tags containing the given word."""
        unique_tags = set(self.tags)
        sep_words = []
        for tag in unique_tags:
            words = tag.lower().split()
            if word.lower() in words:
                sep_words.append(tag)
        return sorted(sep_words)
    
    # BONUS METHOD
    def _get_unique_tags(self):
        """BONUS: Returns list of unique tags."""
        return list(set(self.tags))


class Ratings:
    """Analyzing data from ratings.csv with joined movie data"""
    
    def __init__(self, path_to_the_file, movies_instance=None):
        if movies_instance is None:
            raise ValueError("Movies instance must be provided")
        
        raw_ratings = read_file(path_to_the_file)
        self.movies_obj = movies_instance
        self.joined_data = []
        self.user_ratings = {}
        self.movie_ratings = {}
        self.movie_stats = {}
        
        for row in raw_ratings:
            user_id = int(row['userId'])
            movie_id = int(row['movieId'])
            rating = float(row['rating'])
            timestamp = int(row['timestamp'])
            year = timestamp_to_year(timestamp)
            movie_title = self.movies_obj.movie_titles.get(movie_id, f"Movie {movie_id}")
            
            joined_record = {
                'userId': user_id, 'movieId': movie_id, 'movieTitle': movie_title,
                'rating': rating, 'timestamp': timestamp, 'year': year
            }
            
            self.joined_data.append(joined_record)
            
            if user_id not in self.user_ratings: self.user_ratings[user_id] = []
            self.user_ratings[user_id].append(joined_record)
            
            if movie_id not in self.movie_ratings: self.movie_ratings[movie_id] = []
            self.movie_ratings[movie_id].append(joined_record)
        
        self._compute_movie_statistics()
    
    def _compute_movie_statistics(self):
        """Pre-compute statistics for each movie"""
        for movie_id, ratings in self.movie_ratings.items():
            rating_values = [r['rating'] for r in ratings]
            self.movie_stats[movie_id] = {
                'num_ratings': len(ratings),
                'avg_rating': sum(rating_values) / len(rating_values),
                'median_rating': statistics.median(rating_values) if len(rating_values) > 1 else rating_values[0],
                'variance': statistics.variance(rating_values) if len(rating_values) > 1 else 0,
                'title': ratings[0]['movieTitle']
            }
    
    class Movies:
        """Inner class for movie-related rating analysis"""
        
        def __init__(self, ratings_instance):
            self.ratings = ratings_instance
        
        def dist_by_year(self):
            """Returns dict where keys are years and values are counts."""
            years = Counter()
            for record in self.ratings.joined_data:
                if record['year']:
                    years[record['year']] += 1
            return dict(sorted(years.items()))
        
        def dist_by_rating(self):
            """Returns dict where keys are ratings and values are counts."""
            ratings_dist = Counter()
            for record in self.ratings.joined_data:
                ratings_dist[record['rating']] += 1
            return dict(sorted(ratings_dist.items()))
        
        def top_by_num_of_ratings(self, n):
            """Returns top-n movies by number of ratings."""
            movie_counts = {}
            for movie_id, ratings in self.ratings.movie_ratings.items():
                title = ratings[0]['movieTitle']
                movie_counts[title] = len(ratings)
            sorted_movies = sorted(movie_counts.items(), key=lambda x: x[1], reverse=True)[:n]
            return dict(sorted_movies)
        
        def top_by_ratings(self, n, metric='average'):
            """Returns top-n movies by average or median rating."""
            movie_scores = {}
            for movie_id, stats in self.ratings.movie_stats.items():
                if metric == 'average': value = stats['avg_rating']
                elif metric == 'median': value = stats['median_rating']
                else: raise ValueError(f"Unknown metric: {metric}")
                
                title = stats['title']
                movie_scores[title] = round(value, 2)
            sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)[:n]
            return dict(sorted_movies)
        
        def top_controversial(self, n):
            """Returns top-n movies by variance of ratings."""
            movie_variances = {}
            for movie_id, stats in self.ratings.movie_stats.items():
                if stats['num_ratings'] < 2: continue
                title = stats['title']
                movie_variances[title] = round(stats['variance'], 2)
            sorted_movies = sorted(movie_variances.items(), key=lambda x: x[1], reverse=True)[:n]
            return dict(sorted_movies)
    
    class Users:
        """Inner class for user-related rating analysis"""
        
        def __init__(self, ratings_instance):
            self.ratings = ratings_instance
        
        def dist_by_num_of_ratings(self):
            """Returns distribution of users by number of ratings."""
            user_counts = {}
            for user_id, ratings in self.ratings.user_ratings.items():
                user_counts[user_id] = len(ratings)
            return dict(sorted(user_counts.items()))
        
        def dist_by_ratings(self, metric='average'):
            """Returns distribution of users by average/median ratings."""
            user_stats = {}
            for user_id, ratings in self.ratings.user_ratings.items():
                if len(ratings) < 1: continue
                rating_values = [r['rating'] for r in ratings]
                if metric == 'average': value = sum(rating_values) / len(rating_values)
                elif metric == 'median': value = statistics.median(rating_values)
                else: raise ValueError(f"Unknown metric: {metric}")
                user_stats[user_id] = round(value, 2)
            return dict(sorted(user_stats.items()))
        
        def top_by_variance(self, n):
            """Returns top-n users with biggest variance of ratings."""
            user_variances = {}
            for user_id, ratings in self.ratings.user_ratings.items():
                if len(ratings) < 2: continue
                rating_values = [r['rating'] for r in ratings]
                variance = statistics.variance(rating_values)
                user_variances[user_id] = round(variance, 2)
            sorted_users = sorted(user_variances.items(), key=lambda x: x[1], reverse=True)[:n]
            return dict(sorted_users)
        
        # BONUS METHOD
        def top_by_variance_of_ratings(self, n):
            """BONUS: Alias for top_by_variance."""
            return self.top_by_variance(n)


class Links:
    """
    Analyzing data from links.csv
    """
    def __init__(self, path_to_the_file):
        """
        Initialize Links class with data from links.csv
        """
        raw_data = read_file(path_to_the_file)
        
        self.links_data = {}
        self.imdb_cache = {} 
        
        for row in raw_data:
            movie_id = int(row['movieId'])
            imdb_id = row['imdbId']
            tmdb_id = row['tmdbId'] if row['tmdbId'] else None
            
            self.links_data[movie_id] = {
                'imdbId': imdb_id,
                'tmdbId': tmdb_id
            }
    
    def _get_imdb_page(self, imdb_id):
        """
        Fetch IMDB page for a given IMDB ID
        """
        if imdb_id in self.imdb_cache:
            return self.imdb_cache[imdb_id]
        
        url = f"https://www.imdb.com/title/tt{imdb_id}/"

        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        }

        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            # Silently handling 404s (Not Found) for Report
            if response.status_code == 404:
                return None

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            self.imdb_cache[imdb_id] = soup
            

            time.sleep(0.5)
            
            return soup
        except Exception as e:
            print(f"Error fetching IMDB data for {imdb_id}: {e}")
            return None
    
    def _extract_field(self, soup, field_name):
        """
        Extract specific field from IMDB soup
        """
        if not soup:
            return None
        
        try:
            if field_name.lower() == 'director':
                # Extract director
                director_section = soup.find('a', class_='ipc-metadata-list-item__list-content-item')
                if director_section:
                    return director_section.text.strip()
                
                # Alternative selector
                for section in soup.find_all('li', class_='ipc-metadata-list__item'):
                    if 'Director' in section.text:
                        director_link = section.find('a')
                        if director_link:
                            return director_link.text.strip()
                return None
            
            elif field_name == 'budget':
                section = soup.find('li', {'data-testid': 'title-boxoffice-budget'})
                if section:
                    return section.find('span', class_='ipc-metadata-list-item__list-content-item').text.strip()
                return None
            
            elif field_name.lower() == 'cumulative worldwide gross':
                # Extract gross
                gross_section = soup.find('li', {'data-testid': 'title-boxoffice-cumulativeworldwidegross'})
                if gross_section:
                    gross_text = gross_section.find('span', class_='ipc-metadata-list-item__list-content-item')
                    if gross_text:
                        return gross_text.text.strip()
                return None
            
            elif field_name.lower() == 'runtime':
                # Extract runtime
                runtime_section = soup.find('li', {'data-testid': 'title-techspec_runtime'})
                if runtime_section:
                    runtime_text = runtime_section.find('div', class_='ipc-metadata-list-item__content-container')
                    if runtime_text:
                        return runtime_text.text.strip()
                return None
            
            elif field_name.lower() == 'rating':
                # Extract rating
                rating_section = soup.find('div', {'data-testid': 'hero-rating-bar__aggregate-rating'})
                if rating_section:
                    rating_text = rating_section.find('span', class_='sc-7ab21ed2-1')
                    if rating_text:
                        return rating_text.text.strip()
                return None
            
            elif field_name.lower() == 'genres':
                # Extract genres
                genre_section = soup.find('div', {'data-testid': 'genres'})
                if genre_section:
                    genres = [a.text.strip() for a in genre_section.find_all('a')]
                    return ', '.join(genres)
                return None
            
            elif field_name.lower() == 'release date':
                # Extract release date
                date_section = soup.find('a', href=re.compile(r'releaseinfo'))
                if date_section:
                    return date_section.text.strip()
                return None
            
            else:
                # Try to find field by label
                for section in soup.find_all('li', class_='ipc-metadata-list__item'):
                    label = section.find('span', class_='ipc-metadata-list-item__label')
                    if label and field_name.lower() in label.text.lower():
                        value = section.find('div', class_='ipc-metadata-list-item__content-container')
                        if value:
                            return value.text.strip()
                return None
                
        except Exception as e:
            print(f"Error extracting field {field_name}: {e}")
            return None
    
    def _parse_currency(self, currency_str):
        if not currency_str: return 0        

        rate = 1.0
        if 'JPY' in currency_str or '¥' in currency_str: rate = 0.0065
        elif 'GBP' in currency_str or '£' in currency_str: rate = 1.27
        elif 'EUR' in currency_str or '€' in currency_str: rate = 1.09
        

        cleaned = re.sub(r'[^\d.]', '', currency_str.replace(',', ''))
        try:
            val = float(cleaned)
            return val * rate  
        except:
            return 0
    
    def _parse_runtime(self, runtime_str):
        if not runtime_str:
            return 0
        
        hours = 0
        minutes = 0
        
        hour_match = re.search(r'(\d+)\s*h', runtime_str, re.IGNORECASE)
        if hour_match:
            hours = int(hour_match.group(1))
        
        minute_match = re.search(r'(\d+)\s*m', runtime_str, re.IGNORECASE)
        if minute_match:
            minutes = int(minute_match.group(1))
        elif not hour_match:
            num_match = re.search(r'(\d+)', runtime_str)
            if num_match:
                minutes = int(num_match.group(1))
        
        return hours * 60 + minutes
    
    def get_imdb(self, list_of_movies, list_of_fields):
        results = []
        
        for movie_id in list_of_movies:
            if movie_id not in self.links_data:
                continue
            
            imdb_id = self.links_data[movie_id]['imdbId']
            soup = self._get_imdb_page(imdb_id)
            
            if not soup:
                continue
            
            row = [movie_id]
            for field in list_of_fields:
                value = self._extract_field(soup, field)
                row.append(value)
            
            results.append(row)
        
        results.sort(key=lambda x: x[0], reverse=True)
        
        return results
    
    def top_directors(self, n):
        director_counter = Counter()
        
        for movie_id, link_info in self.links_data.items():
            imdb_id = link_info['imdbId']
            soup = self._get_imdb_page(imdb_id)
            
            if not soup:
                continue
            
            director = self._extract_field(soup, 'director')
            if director:
                directors = [d.strip() for d in director.split(',')]
                for d in directors:
                    director_counter[d] += 1
        
        top_directors = OrderedDict(director_counter.most_common(n))
        return top_directors
    

    def most_expensive(self, n):
        movie_budgets = {}
        for mid, link in self.links_data.items():
            soup = self._get_imdb_page(link['imdbId'])
            if not soup: continue
            
            title = soup.find('h1').text.strip() # Will now be English
            budget_str = self._extract_field(soup, 'budget')
            
            if budget_str:
                budget_usd = self._parse_currency(budget_str)
                if budget_usd > 0:
                    movie_budgets[title] = budget_usd
                    
        return dict(sorted(movie_budgets.items(), key=lambda x: x[1], reverse=True)[:n])
    
    def most_profitable(self, n):
        movie_profits = {}
        
        for movie_id, link_info in self.links_data.items():
            imdb_id = link_info['imdbId']
            soup = self._get_imdb_page(imdb_id)
            
            if not soup:
                continue
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else f"Movie {movie_id}"
            
            budget_str = self._extract_field(soup, 'budget')
            gross_str = self._extract_field(soup, 'cumulative worldwide gross')
            
            if budget_str and gross_str:
                budget = self._parse_currency(budget_str)
                gross = self._parse_currency(gross_str)
                
                if budget > 0 and gross > 0:
                    profit = gross - budget
                    movie_profits[title] = profit
        
        sorted_profits = sorted(movie_profits.items(), key=lambda x: x[1], reverse=True)[:n]
        return dict(sorted_profits)
    
    def longest(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their runtime. If there are more than one version – choose any.
        Sort it by runtime descendingly.
        """
        movie_runtimes = {}
        
        for movie_id, link_info in self.links_data.items():
            imdb_id = link_info['imdbId']
            soup = self._get_imdb_page(imdb_id)
            
            if not soup:
                continue
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else f"Movie {movie_id}"
            
            runtime_str = self._extract_field(soup, 'runtime')
            if runtime_str:
                runtime = self._parse_runtime(runtime_str)
                if runtime > 0:
                    movie_runtimes[title] = runtime
        
        sorted_runtimes = sorted(movie_runtimes.items(), key=lambda x: x[1], reverse=True)[:n]
        return dict(sorted_runtimes)
    
    def top_cost_per_minute(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the budgets divided by their runtime. 
        The values should be rounded to 2 decimals. Sort it by the division descendingly.
        """
        movie_costs = {}
        
        for movie_id, link_info in self.links_data.items():
            imdb_id = link_info['imdbId']
            soup = self._get_imdb_page(imdb_id)
            
            if not soup:
                continue
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else f"Movie {movie_id}"
            
            budget_str = self._extract_field(soup, 'budget')
            runtime_str = self._extract_field(soup, 'runtime')
            
            if budget_str and runtime_str:
                budget = self._parse_currency(budget_str)
                runtime = self._parse_runtime(runtime_str)
                
                if budget > 0 and runtime > 0:
                    cost_per_minute = budget / runtime
                    movie_costs[title] = round(cost_per_minute, 2)
        
        sorted_costs = sorted(movie_costs.items(), key=lambda x: x[1], reverse=True)[:n]
        return dict(sorted_costs)



class Tests:
    """
    Testing class for MovieLens analysis.
    Contains methods that verify the correctness of other classes' methods.
    """

    def __init__(self, movies_path, ratings_path, tags_path, links_path):
        self.movies = Movies(movies_path)
        self.ratings = Ratings(ratings_path, self.movies)
        self.tags = Tags(tags_path)
        self.links = Links(links_path)

    def test_movies_dist_by_release(self):
        result = self.movies.dist_by_release()
        assert isinstance(result, dict)
        for year, count in result.items():
            assert isinstance(year, int)
            assert isinstance(count, int)
        counts = list(result.values())
        assert counts == sorted(counts, reverse=True)

    def test_movies_dist_by_genres(self):
        result = self.movies.dist_by_genres()
        assert isinstance(result, dict)
        for genre, count in result.items():
            assert isinstance(genre, str)
            assert isinstance(count, int)
        counts = list(result.values())
        assert counts == sorted(counts, reverse=True)

    def test_movies_most_genres(self):
        result = self.movies.most_genres(5)
        assert isinstance(result, dict)
        assert len(result) <= 5
        values = list(result.values())
        assert values == sorted(values, reverse=True)

    def test_tags_most_words(self):
        result = self.tags.most_words(10)
        assert isinstance(result, dict)
        for tag, count in result.items():
            assert isinstance(tag, str)
            assert isinstance(count, int)

    def test_tags_longest(self):
        result = self.tags.longest(5)
        assert isinstance(result, list)
        assert len(result) <= 5
        for tag in result:
            assert isinstance(tag, str)

    def test_tags_most_popular(self):
        result = self.tags.most_popular(5)
        assert isinstance(result, dict)
        values = list(result.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_movies_dist_by_year(self):
        rm = self.ratings.Movies(self.ratings)
        result = rm.dist_by_year()
        assert isinstance(result, dict)
        for year, count in result.items():
            assert isinstance(year, int)
            assert isinstance(count, int)

    def test_ratings_movies_dist_by_rating(self):
        rm = self.ratings.Movies(self.ratings)
        result = rm.dist_by_rating()
        assert isinstance(result, dict)
        for rating, count in result.items():
            assert isinstance(rating, float)
            assert isinstance(count, int)

    def test_ratings_top_by_num_of_ratings(self):
        rm = self.ratings.Movies(self.ratings)
        result = rm.top_by_num_of_ratings(5)
        assert isinstance(result, dict)
        assert len(result) <= 5

    def test_ratings_top_by_ratings(self):
        rm = self.ratings.Movies(self.ratings)
        result = rm.top_by_ratings(5)
        assert isinstance(result, dict)
        assert len(result) <= 5
        values = list(result.values())
        assert values == sorted(values, reverse=True)

    def test_ratings_top_controversial(self):
        rm = self.ratings.Movies(self.ratings)
        result = rm.top_controversial(5)
        assert isinstance(result, dict)
        assert len(result) <= 5

    def test_ratings_users_dist_by_num_of_ratings(self):
        ru = self.ratings.Users(self.ratings)
        result = ru.dist_by_num_of_ratings()
        assert isinstance(result, dict)
        for user_id, count in result.items():
            assert isinstance(user_id, int)
            assert isinstance(count, int)

    def test_links_data_loaded(self):
        assert isinstance(self.links.links_data, dict)
        assert len(self.links.links_data) > 0

if __name__ == '__main__':
    print("MovieLens Analysis Module Loaded")