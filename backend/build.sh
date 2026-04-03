#!/bin/bash
set -e
pip install -r requirements.txt
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L3-v2')"