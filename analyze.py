"""
Measures the readability and word choice of every US presidential inaugural
address (NLTK inaugural corpus) and writes results/speech_metrics.csv.

Usage:
    python analyze.py
"""

import re
from pathlib import Path

import nltk
import pandas as pd
import textstat
import truststore

# Use the operating system's certificates, so NLTK downloads work on machines
# where antivirus software inspects SSL traffic.
truststore.inject_into_ssl()

RESULTS_FILE = Path(__file__).resolve().parent / "results" / "speech_metrics.csv"
NLTK_RESOURCES = {
    "inaugural": "corpora/inaugural",
    "punkt": "tokenizers/punkt",
    "punkt_tab": "tokenizers/punkt_tab",
    "vader_lexicon": "sentiment/vader_lexicon",
}

WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
# "I" must be a capital letter; "US" in capitals means the country, not "us"
SINGULAR = re.compile(r"\b(?:I|[Mm][Ee]|[Mm][Yy]|[Mm]ine|[Mm]yself)\b")
PLURAL = re.compile(r"\b(?:[Ww][Ee]|[Oo][Uu][Rr]|[Oo]urs|[Oo]urselves|(?!US\b)[Uu][Ss])\b")


def setup_nltk():
    """Download the NLTK data this script needs, only if it is missing."""
    for name, path in NLTK_RESOURCES.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


def per_1000(count, total):
    return 1000 * count / total if total else 0


def analyze_speech(text, sentiment):
    """Return the measures for one speech."""
    sentences = nltk.sent_tokenize(text)
    words = WORD.findall(text)
    tone = [sentiment.polarity_scores(s)["compound"] for s in sentences]
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": len(words) / len(sentences),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "gunning_fog": textstat.gunning_fog(text),
        "singular_per_1000": per_1000(len(SINGULAR.findall(text)), len(words)),
        "plural_per_1000": per_1000(len(PLURAL.findall(text)), len(words)),
        # VADER saturates on long text, so average it sentence by sentence
        "avg_sentence_tone": sum(tone) / len(tone),
    }


def main():
    setup_nltk()
    from nltk.corpus import inaugural
    from nltk.sentiment import SentimentIntensityAnalyzer

    sentiment = SentimentIntensityAnalyzer()
    rows = []
    for file_id in inaugural.fileids():
        year, president = file_id.removesuffix(".txt").split("-", 1)
        values = analyze_speech(inaugural.raw(file_id), sentiment)
        rows.append({"year": int(year), "president": president, **values})

    df = pd.DataFrame(rows).sort_values("year").round(3)
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    df.to_csv(RESULTS_FILE, index=False)
    print(f"Wrote {len(df)} speeches to {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()
