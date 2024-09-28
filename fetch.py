from newspaper import Article, Config, build, news_pool
from utils import nlp
import sys

def fetch_article(url):
    """
    Fetches an article by URL and extracts information.

    Parameters:
    - url: URL of the news article to fetch.

    Returns:
    A dictionary containing the title, authors, publish date, and text of the article.
    """

    print(f"   Fetching article: {url}")

    # Configure newspaper to not download images
    config = Config()
    config.fetch_images = False

    # Download and parse the article
    article = Article(url, config=config)
    article.download()
    article.parse()
    article.nlp()


    return {
        'title': article.title,
        'authors': article.authors,
        'publish_date': article.publish_date,
        'text': article.text,
        'keywords': article.keywords,
        'url': article.url,
        'source': article.url[:article.url.find('.com')+4]
    }


def fetch_from_list_of_sources(source_papers, limit=5):
    """
    Fetches articles from a list of news sources.

    Parameters:
    - source_papers: List of built papers of the news sources to fetch articles from.
    - limit: Maximum number of articles to fetch per source.

    Returns:
    A list of dictionaries, each containing information about an article.
    """
    print("Building pool...", end="")

    news_pool.set(source_papers, threads_per_source=6)
    news_pool.join()

    print("done. Fetching articles...")

    articles = []
    titles = []
    counter = 0

    for source in papers:
        for article in source.articles:
            if counter >= 10:
                break
            try:
                article_data = fetch_article(article.url)
                if not article_data['title'] in titles:
                    articles.append(article_data)
                    titles.append(article_data['title'])
                    counter += 1
            except Exception as e:
                print(f"Error fetching article: {e}")

    return articles


def fetch_from_source(source_url, limit=5):
    """
    Fetches articles from a news source.

    Parameters:
    - source_url: URL of the news source to fetch articles from.
    - limit: Maximum number of articles to fetch.

    Returns:
    A list of dictionaries, each containing information about an article.
    """
    # Build the Source object
    news_source = build(source_url, memoize_articles=False)

    articles = []
    titles = []
    counter = 0
    for article in news_source.articles:
        if counter >= limit:
            break
        try:
            article_data = fetch_article(article.url)
            if not article_data['title'] in titles:
                titles.append(article_data['title'])
                articles.append(article_data)
                counter += 1
        except Exception as e:
            print(f"Failed to fetch article: {e}")
    return articles


def fetch_from_built_paper(paper, forbidden_sources, limit=5):
    articles = []
    titles = []
    counter = 0
    for article in paper.articles:
        if counter >= limit:
            break
        try:
            if not any(article.url.startswith(s) for s in forbidden_sources):
                article_data = fetch_article(article.url)
                if not article_data['title'] in titles:
                    titles.append(article_data['title'])
                    articles.append(article_data)
                    counter += 1
                else:
                    print(f"    --- Article already in list")

            else:
                print(f"    --- Article from forbidden source: {article.url}")
        except Exception as e:
            print(f"Failed to fetch article: {e}")
    return articles


def dot_product(vec_a, vec_b):
    """Compute the dot product of two vectors."""
    return sum(a * b for a, b in zip(vec_a, vec_b))

def magnitude(vec):
    """Compute the magnitude (Euclidean norm) of a vector."""
    return sum(x**2 for x in vec) ** 0.5

def compute_cosine_similarity(vec_a, vec_b):
    """Compute the cosine similarity between two vectors."""
    dot_prod = dot_product(vec_a, vec_b)
    mag_a = magnitude(vec_a)
    mag_b = magnitude(vec_b)
    
    # To prevent division by zero, check if magnitudes are non-zero
    if mag_a == 0 or mag_b == 0:
        return 0  # Returns 0 if either vector has magnitude 0
    else:
        return dot_prod / (mag_a * mag_b)


def get_best_articles(articles, ref_vector, word_vectors):
    selected_articles = []
    for article in articles:
        text_vector = nlp.compute_text_vector(
            article['text'], 
            word_vectors
        )
        keyword_vector = nlp.compute_text_vector(
            " ".join(article['keywords']), 
            word_vectors
        )
        #similarity = nlp.compute_cosine_similarity(ref_vector, text_vector)
        similarity_kw = nlp.compute_cosine_similarity(ref_vector, keyword_vector)
        #print(f"   Similarity with article '{article['title']}': {similarity:.2f} (text) {similarity_kw:.2f} (keywords)")
        selected_articles.append((article, round(similarity_kw, 2)))
    selected_articles.sort(key=lambda x: x[1], reverse=True)
    return selected_articles

def get_ref_vector(word_vectors):
    file = "utils/ref_document.txt"
    ref_content = ""
    with open(file, 'r') as f:
        ref_content = f.read()
    ref_vector = nlp.compute_text_vector(ref_content, word_vectors)
    return ref_vector


def get_word_vectors():
    file_path = 'utils/word_vectors'
    word_vectors = {}
    for i in range(1,5):
        word_vectors = word_vectors | nlp.read_word_vectors(file_path + str(i) + '.txt')
    return word_vectors

def build_sources(sources, built_sources, built_papers):
    papers = []
    index = 0
    for source in sources:
        if source not in built_sources:
            built_sources.append(source)
            print(f"Building source '{source}...'", end="")
            paper = build(source, memoize_articles=False)
            papers.append(paper)
            print("done")
        else:
            print(f"Source '{source}' already built")
            papers.append(built_papers[index])
        index += 1    
    return papers





def main_fetch(built_papers):
    #papers = [build(source, memoize_articles=False) for source in sources]
    word_vectors = get_word_vectors()
    ref_vector = get_ref_vector(word_vectors)

    articles = []
    for source in sources:
        print(f"Fetching {source}", file=sys.stderr)
        articles = articles + fetch_from_source(source, limit=5)

    selected_articles = get_best_articles(articles, ref_vector, word_vectors)
    return selected_articles

