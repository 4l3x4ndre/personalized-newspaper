import numpy as np
from nltk.tokenize import word_tokenize
import nltk

def read_word_vectors(file_path):
    """
    Reads a file containing word vectors. Each line in the file is expected
    to have the format "word_TYPE" followed by 300 float values representing
    the word vector. Only adds the vector to the dictionary if the TYPE is not "NUM".

    Parameters:
    - file_path: Path to the file containing the word vectors.

    Returns:
    A dictionary where keys are "word_TYPE" strings and values are lists of
    floats representing the word vectors, excluding those with TYPE "NUM".
    """
    word_vectors = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 301:
                print(f"Skipping line due to unexpected length: {line}")
                continue
            word_type, vector = parts[0], parts[1:]
            if not word_type.endswith("_NUM"):  # Check if TYPE is not "NUM"
                try:
                    word_vectors[word_type.split("_")[0]] = [float(num) for num in vector]
                except ValueError as e:
                    print(f"Error converting vector to floats for word {word_type}: {e}")
                    continue  # Skip this line but continue processing the rest of the file

    return word_vectors


def compute_text_vector(text, word_vectors):
    """
    Computes the average word vector for a given text.
    
    Parameters:
    - text (str): The input text.
    - word_vectors (KeyedVectors): Pre-trained word vectors.
    
    Returns:
    - np.array: The average word vector for the text.
    """
    # Tokenize the text
    words = word_tokenize(text.lower())
    
    # Retrieve word vectors for each word in the text, if available
    vectors = [word_vectors[word] for word in words if word in word_vectors]
    
    # Check if we have at least one vector
    if vectors:
        # Compute the average vector
        text_vector = np.mean(vectors, axis=0)
    else:
        # If no words in the text have vectors, return a zero vector
        #text_vector = np.zeros(word_vectors.vector_size)
        text_vector = np.zeros(len(next(iter(word_vectors.values()))))  # Assuming all vectors have the same size
        
    return text_vector

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


