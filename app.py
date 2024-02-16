from flask import Flask, request, render_template, redirect, url_for
import csv
from fetch import get_ref_vector, build_sources, fetch_from_built_paper, get_best_articles, get_word_vectors


# Constants
MAIN_ARTICLES_FILE = 'articles.csv'
CACHED_ARTICLES_FILE = 'articles_cached.csv'
MAIN_SOURCES_FILE = 'sources.csv'
REF_DOC_FILE = 'utils/ref_document.txt'


app = Flask(__name__)
sources = []
articles = []
built_papers = []
built_sources = []
ref_vector = []
word_vectors = []

def read_sources():
    global sources
    sources = []
    with open(MAIN_SOURCES_FILE, 'r', newline='\n') as csvfile:
        reader = csv.reader(csvfile)
        sources = [row[0] for row in reader]
    return sources


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


@app.route('/')
def index():
    return render_template("base.html", sources=[])


@app.route('/submit', methods=['POST'])
def submit():
    source_url = request.form['source_url']
    with open(MAIN_SOURCES_FILE, 'a', newline='\n') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([source_url])
    
    return render_template("base.html", sources=sources)


@app.route('/load', methods=['GET'])
def load():
    global sources
    sources = read_sources()
    return render_template("base.html", sources=sources)


@app.route('/fetch', methods=['GET'])
def fetch():
    global articles, built_papers, built_sources, ref_vector, word_vectors
    articles = []
    
    papers = build_sources(sources=read_sources(), built_sources=built_sources, built_papers=built_papers)
    built_papers = papers
    built_sources = sources

    if len(word_vectors) == 0: word_vectors = get_word_vectors()
    if len(ref_vector) == 0: ref_vector = get_ref_vector(word_vectors)


    for paper in papers:
        print(f"Fetching articles from {paper.url}")
        articles = articles + fetch_from_built_paper(paper, limit=5)

    selected_articles = get_best_articles(articles, ref_vector, word_vectors)

    articles = selected_articles
    save_articles_to_csv(CACHED_ARTICLES_FILE, articles, 'w')

    return render_template("articles.html", articles=articles)


@app.route('/load_articles', methods=['GET'])
def load_articles():
    global articles
    articles = read_articles(MAIN_ARTICLES_FILE)
    
    return render_template("articles.html", articles=articles)


@app.route('/load_cached_articles', methods=['GET'])
def load_cached_articles():
    _articles = read_articles(CACHED_ARTICLES_FILE)
    return render_template("articles.html", articles=_articles)



@app.route('/build_sources', methods=['GET'])
def page_build_sources():
    global built_papers, built_sources
    built_papers = build_sources(read_sources(), [], [])
    built_sources = sources
    return render_template("base.html", sources=sources)


@app.route('/save_articles', methods=['GET'])
def save_articles():
    save_articles_to_csv("articles.csv", articles)
    return render_template("base.html", articles=articles)


@app.route('/article/<int:article_id>')
def article(article_id):
    global articles
    print(f"There are {len(articles)} articles in cache.")
    save_articles_to_csv(CACHED_ARTICLES_FILE, articles, 'w')
    if 0 < article_id <= len(articles):
        return render_template('text_article.html', article=articles[article_id-1][0])
    else:
        return "Article not found", 404

@app.route('/save_article/<int:article_id>')
def save_article(article_id):
    global articles
    if len(articles) > 0:
        save_articles_to_csv(MAIN_ARTICLES_FILE, [articles[article_id-1]])
        return render_template("articles.html", articles=articles)
    else:
        return "No article in cache", 404
 

@app.route('/unsave_article/<int:article_id>')
def unsave_article(article_id):
    global articles
    if 0 < article_id <= len(articles):
        remove_article_by_title(MAIN_ARTICLES_FILE, articles[article_id-1][0]['title'])
        articles = read_articles(MAIN_ARTICLES_FILE)
        return render_template("articles.html", articles=articles)
    else:
        return "Article not found", 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
