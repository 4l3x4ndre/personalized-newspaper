# Personalized newspaper

Fetch article from a list of newspaper and retrieve relevent article based on a reference keywords file. The reference keywords file is updated with keywords of saved articles. 

Articles are fetched using the python library `newspaper3k`.

Word vectors are coming from http://vectors.nlpl.eu/repository with the ID 188.

Relevence is calculated by a cosine similarity between the reference-keywords mean vector representation and the article's keywords mean vector representation.

# Installation

Use `install_app.sh` to install requirements and launch server on localhost port 5000.

```
chmod +x ./install_app.sh
./install_app.sh
```

---
[favicon](https://www.flaticon.com/free-icons/paper)
