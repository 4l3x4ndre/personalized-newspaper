from flask import Flask, request, render_template, redirect, url_for
import csv
from fetch import get_ref_vector, build_sources, fetch_from_built_paper, get_best_articles, get_word_vectors
import os # load api keys
import requests # request weeather

# Job: 
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

# Constants
MAIN_ARTICLES_FILE = 'articles.csv'
CACHED_ARTICLES_FILE = 'articles_cached.csv'
MAIN_SOURCES_FILE = 'sources.csv'
MAIN_FORBIDDEN_SOURCES_FILE = 'forbidden_sources.csv'
REF_DOC_FILE = 'utils/ref_document.txt'
OPEN_WEATHER_APIKEY = os.getenv('newworld_post_python')


app = Flask(__name__)
sources = []
forbidden_sources = []
articles = []
built_papers = []
built_sources = []
ref_vector = []
word_vectors = []
weather_data = []

def read_sources():
    global sources
    sources = []
    with open(MAIN_SOURCES_FILE, 'r', newline='\n') as csvfile:
        reader = csv.reader(csvfile)
        sources = [row[0] for row in reader]
    return sources

def read_forbidden_sources():
    global forbidden_sources
    forbidden_sources = []
    with open(MAIN_FORBIDDEN_SOURCES_FILE, 'r', newline='\n') as csvfile:
        reader = csv.reader(csvfile)
        forbidden_sources = [row[0] for row in reader]
    return forbidden_sources


def save_articles_to_csv(filename, _articles, mode='a'):
    old_articles = []
    if mode == 'a':
        with open(filename, 'r', newline='\n') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) > 0:
                    old_articles.append(row[0])
       
        if len(old_articles) == 0: mode='w'
    caching = filename == CACHED_ARTICLES_FILE
    print(f"Caching: {caching}")

    keywords = ""
    with open(filename, mode, newline='\n') as csvfile:
        writer = csv.writer(csvfile)
        for article, similarity in _articles:
            if not article['title'] in old_articles:
                writer.writerow([article['title'], article['url'], article['text'], article['keywords'], article['source'], similarity])
                if not caching: 
                    print(f"Saving kw of {article['title']} :\n  {article['keywords']}")
                    keywords += " ".join(article['keywords'])

    if not caching:
        keywords += " "
        with open(REF_DOC_FILE, 'a') as file:
            file.write(keywords)


def read_articles(filename):
    global articles
    articles = []
    with open(filename, 'r', newline='\n') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            if len(row) >0:
                articles.append(({'title': row[0], 'url': row[1], 'text':row[2], 'keywords': row[3], 'source':row[4]}, row[-1]))
    return articles


def remove_article_by_title(filename, article_title):
    """
    Remove an article from a CSV file based on its title.
    
    Parameters:
    - filename: Path to the CSV file.
    - article_title: The title of the article to remove.
    """
    rows = []
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Collect rows that don't match the article title
        rows = [row for row in reader if row[0] != article_title]
    
    # Write the filtered rows back to the file
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def get_weather(city="Paris"):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPEN_WEATHER_APIKEY}&units=metric' 
    print(url)
    response = requests.get(url)

    global weather_data
    
    if response.status_code == 200:
        data = response.json()
        weather_data = {
            'description': data['weather'][0]['description'].capitalize(),
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'city':city
        }
        return weather_data
    else:
        return None


# ---------------------- Job ------------------------
# Job to run the `fetch` function every day at 7am
def fetch_articles_job():
    """
    Job to run the `fetch` function every day at 7am
    """
    global built_papers, built_sources, forbidden_sources, articles, ref_vector, word_vectors

    # 1. Rebuild sources objects
    built_papers = build_sources(read_sources(), [], [])
    built_sources = sources
    forbidden_sources = read_forbidden_sources()

    # 2. Fetch their article
    articles = []
    
    if len(word_vectors) == 0: word_vectors = get_word_vectors()
    if len(ref_vector) == 0: ref_vector = get_ref_vector(word_vectors)


    for paper in built_papers:
        print(f"Fetching articles from {paper.url}")
        articles = articles + fetch_from_built_paper(paper, forbidden_sources=forbidden_sources, limit=10)

    selected_articles = get_best_articles(articles, ref_vector, word_vectors)
    articles = selected_articles
    save_articles_to_csv(CACHED_ARTICLES_FILE, articles, 'w')

    print("Articles fetched successfully at 7am.")
    #return render_template("base.html", articles=articles, sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


# Initialize APScheduler
scheduler = BackgroundScheduler()

# Schedule the fetch_articles_job to run every day at 7am
scheduler.add_job(fetch_articles_job, 'cron', hour=7, minute=0, timezone='Europe/Vienna')
scheduler.start()

# Shut down the scheduler when exiting the app
@app.before_request
def initialize_scheduler():
    if not scheduler.running:
        scheduler.start()

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    scheduler.shutdown()



# ----------------------------- WEB ROUTING -----------------------------

@app.route('/')
def index():
    global sources, forbidden_sources
    sources = read_sources()
    forbidden_sources = read_forbidden_sources()

    weather_data = get_weather("Paris")

    return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/submit', methods=['POST'])
def submit():
    source_url = request.form['source_url']
    with open(MAIN_SOURCES_FILE, 'a', newline='\n') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([source_url])

    global sources, forbidden_sources
    sources = read_sources()
    return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)

@app.route('/submit_forbidden', methods=['POST'])
def submit_forbidden():
    forbidden = request.form['forbidden_source_url']
    with open(MAIN_FORBIDDEN_SOURCES_FILE, 'a', newline='\n') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([forbidden])

    global forbidden_sources
    forbidden_sources = read_forbidden_sources()
    return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/load', methods=['GET'])
def load():
    global sources, forbidden_sources
    sources = read_sources()
    forbidden_sources = read_forbidden_sources()
    return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/fetch', methods=['GET'])
def fetch():
    fetch_articles_job()
    return "Articles fetched manually!", 200



    # 1. Rebuild sources objects
    global built_papers, built_sources
    built_papers = build_sources(read_sources(), [], [])
    built_sources = sources

    # 2. Fetch their article
    global articles, ref_vector, word_vectors
    articles = []
    
    papers = build_sources(sources=read_sources(), built_sources=built_sources, built_papers=built_papers)
    built_papers = papers
    built_sources = sources

    if len(word_vectors) == 0: word_vectors = get_word_vectors()
    if len(ref_vector) == 0: ref_vector = get_ref_vector(word_vectors)


    for paper in papers:
        print(f"Fetching articles from {paper.url}")
        articles = articles + fetch_from_built_paper(paper, forbidden_sources=forbidden_sources, limit=10)

    selected_articles = get_best_articles(articles, ref_vector, word_vectors)

    articles = selected_articles
    save_articles_to_csv(CACHED_ARTICLES_FILE, articles, 'w')

    return render_template("base.html", articles=articles, sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/load_articles', methods=['GET'])
def load_articles():
    global articles
    articles = read_articles(MAIN_ARTICLES_FILE)
    
    return render_template("base.html", articles=articles, sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/load_cached_articles', methods=['GET'])
def load_cached_articles():
    _articles = read_articles(CACHED_ARTICLES_FILE)
    weather_data = get_weather("Paris")
    return render_template("base.html", articles=articles, sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)



@app.route('/build_sources', methods=['GET'])
def page_build_sources():
    global built_papers, built_sources
    built_papers = build_sources(read_sources(), [], [])
    built_sources = sources
    return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/save_articles', methods=['GET'])
def save_articles():
    save_articles_to_csv("articles.csv", articles)
    return render_template("base.html", articles=articles, sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)


@app.route('/article/<int:article_id>')
def article(article_id):
    global articles
    print(f"There are {len(articles)} articles in cache.")
    save_articles_to_csv(CACHED_ARTICLES_FILE, articles, 'w')
    if 0 < article_id <= len(articles):
        return render_template('text_article.html', article=articles[article_id-1][0], weather=weather_data)
    else:
        return "Article not found", 404

@app.route('/save_article/<int:article_id>')
def save_article(article_id):
    global articles
    if len(articles) > 0:
        save_articles_to_csv(MAIN_ARTICLES_FILE, [articles[article_id-1]])
        return render_template("base.html", articles=articles, sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)
    else:
        return "No article in cache", 404
 

@app.route('/unsave_article/<int:article_id>')
def unsave_article(article_id):
    global articles
    if 0 < article_id <= len(articles):
        remove_article_by_title(MAIN_ARTICLES_FILE, articles[article_id-1][0]['title'])
        articles = read_articles(MAIN_ARTICLES_FILE)
        return render_template("articles.html", articles=articles, weather=weather_data)
    else:
        return "Article not found", 404

@app.route('/remove_source/<int:source_id>')
def remove_source(source_id):
    global sources
    if 0 < source_id <= len(sources):
        source = sources[source_id-1]
        with open(MAIN_SOURCES_FILE, 'w', newline='\n') as csvfile:
            writer = csv.writer(csvfile)
            for source_url in sources:
                if source_url != source:
                    writer.writerow([source_url])
        sources = read_sources()
        return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)
    else:
        return "Source not found", 404

@app.route('/remove_forbidden_source/<int:source_id>')
def remove_forbidden_source(source_id):
    # rewrite
    global forbidden_sources
    if 0 < source_id <= len(forbidden_sources):
        source = forbidden_sources[source_id-1]
        with open(MAIN_FORBIDDEN_SOURCES_FILE, 'w', newline='\n') as csvfile:
            writer = csv.writer(csvfile)
            for source_url in forbidden_sources:
                if source_url != source:
                    writer.writerow([source_url])
        forbidden_sources = read_forbidden_sources()
        return render_template("base.html", sources=sources, forbidden_sources=forbidden_sources, weather=weather_data)
    else:
        return "Source not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
