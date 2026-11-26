import hashlib
import json
from unicodedata import normalize

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize as l2_normalize


def corpus_text(term):
    bridge = normalize("NFKC", term["bridge_words"]).casefold()
    phrase = normalize("NFKC", term["spoken_text"]).casefold()
    cue = normalize("NFKC", term["show_cue"]).casefold()
    return " | ".join([bridge, cue, phrase])


def rank_candidates(origin, targets):
    terms = [origin, *targets]
    inputs = [corpus_text(term) for term in terms]
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), sublinear_tf=True)
    matrix = vectorizer.fit_transform(inputs)
    dimensions = min(8, matrix.shape[0] - 1, matrix.shape[1] - 1)
    if dimensions < 2:
        raise ValueError("至少需要两个可表示的目标语种词条")
    reducer = TruncatedSVD(n_components=dimensions, random_state=1078, n_iter=10)
    document_vectors = l2_normalize(reducer.fit_transform(matrix))
    scores = document_vectors[1:] @ document_vectors[0]
    ranked = sorted(
        ((row["code"], round(float(np.clip(score, -1.0, 1.0)), 6))
         for row, score in zip(targets, scores, strict=True)),
        key=lambda pair: (-pair[1], pair[0]),
    )
    corpus = list(zip([term["code"] for term in terms], inputs, strict=True))
    metrics = {
        "dimensions": dimensions,
        "vocabulary_size": matrix.shape[1],
        "explained_variance": round(float(np.nan_to_num(reducer.explained_variance_ratio_).sum()), 6),
        "fingerprint": hashlib.sha256(json.dumps(corpus, ensure_ascii=False).encode()).hexdigest(),
    }
    return ranked[:5], metrics
