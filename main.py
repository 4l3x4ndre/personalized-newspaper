from newspaper import build
from fetch import fetch_from_source, get_best_articles
#import nltk
from utils import nlp
import time

def main():

    start_time = time.time()

    # Time to read word vectors: 10s
    file_path = 'utils/word_vectors.txt'
    word_vectors = nlp.read_word_vectors(file_path)
    print(f"Read {len(word_vectors)} word vectors, excluding TYPE 'NUM'.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"+++++++++++++++++++++++++++++++++Time taken to read word vectors: {elapsed_time:.2f} seconds+++++++++++++++++++++++++++++++++")


    # Time to compute the reference vector: 0.01s
    ref_vector = nlp.compute_text_vector(
            "intelligence cognitive computer smartphone phone mobile device technology software hardware data science code programming algorithm network internet web online digital virtual augmented reality machine learning deep neural network artificial intelligence AI",
            word_vectors
    )


    start_time = time.time()
    # Time to build sources: 120s
    paper_verge = build('https://www.theverge.com', memoize_articles=False)
    paper_nytimes = build('https://www.nytimes.com', memoize_articles=False)
    paper_nytimes_tech = build('https://www.nytimes.com/section/technology', memoize_articles=False)
    papers = [paper_verge, paper_nytimes, paper_nytimes_tech]

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"+++++++++++++++++++++++++++++++++Time taken to build the Source objects: {elapsed_time:.2f} seconds+++++++++++++++++++++++++++++++++")

    sources = ['https://www.theverge.com', 'https://www.nytimes.com', 'https://www.nytimes.com/section/technology']

    articles = []
    for source in sources:
        print(f"Fetching articles from {source}")
        articles = articles + fetch_from_source(source, limit=5)

    selected_articles = get_best_articles(articles, ref_vector, word_vectors)
    for article, similarity in selected_articles:
        print(f"Similarity with article '{article['title']}': {similarity} {article['url']}")

    return


if __name__ == "__main__":
    main()
