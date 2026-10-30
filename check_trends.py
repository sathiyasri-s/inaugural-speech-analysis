"""
Tests whether the trends in results/speech_metrics.csv survive when the method
changes: other formulas, measures that ignore punctuation, and removing short
or transcribed speeches. Prints a report and saves it to results/trend_checks.txt.

Usage:
    python analyze.py        # first
    python check_trends.py
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import textstat
from nltk.corpus import inaugural

BASE_DIR = Path(__file__).resolve().parent
METRICS_FILE = BASE_DIR / "results" / "speech_metrics.csv"
REPORT_FILE = BASE_DIR / "results" / "trend_checks.txt"

BREAK_YEAR = 1950       # used to test whether the decline has flattened
SHORT_SPEECH = 1000     # words
PERMUTATIONS = 10000
WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")

report = []


def log(line=""):
    print(line)
    report.append(line)


def spearman(x, y):
    return np.corrcoef(pd.Series(x).rank(), pd.Series(y).rank())[0, 1]


def permutation_p(x, y, seed=0):
    """Share of random orderings with a rank correlation as strong as the real one."""
    rng = np.random.default_rng(seed)
    x_rank = pd.Series(x).rank().to_numpy()
    y_rank = pd.Series(y).rank().to_numpy()
    real = abs(np.corrcoef(x_rank, y_rank)[0, 1])
    hits = sum(abs(np.corrcoef(x_rank, rng.permutation(y_rank))[0, 1]) >= real
               for _ in range(PERMUTATIONS))
    return (hits + 1) / (PERMUTATIONS + 1)


def slope_per_century(df, column):
    return np.polyfit(df["year"], df[column], 1)[0] * 100


def word_level_measures(text):
    """Measures of word difficulty that do not depend on where sentences end."""
    words = WORD.findall(text)
    syllables = [textstat.syllable_count(w) for w in words]
    return {
        "avg_word_letters": sum(len(w) for w in words) / len(words),
        "syllables_per_word": sum(syllables) / len(words),
        "pct_3plus_syllables": 100 * sum(s >= 3 for s in syllables) / len(words),
    }


def by_word(text, pattern):
    return 1000 * len(re.findall(pattern, text)) / len(WORD.findall(text))


def main():
    df = pd.read_csv(METRICS_FILE)
    texts = {row.year: inaugural.raw(f"{row.year}-{row.president}.txt")
             for row in df.itertuples()}

    extra = pd.DataFrame([word_level_measures(texts[y]) for y in df["year"]])
    df = pd.concat([df, extra], axis=1)
    df["coleman_liau"] = [textstat.coleman_liau_index(texts[y]) for y in df["year"]]
    df["automated_readability"] = [textstat.automated_readability_index(texts[y]) for y in df["year"]]
    df["we_only"] = [by_word(texts[y], r"\b[Ww][Ee]\b") for y in df["year"]]
    df["our_only"] = [by_word(texts[y], r"\b[Oo][Uu][Rr]\b") for y in df["year"]]
    df["i_only"] = [by_word(texts[y], r"\bI\b") for y in df["year"]]

    measures = ["flesch_kincaid_grade", "gunning_fog", "coleman_liau", "automated_readability",
                "avg_sentence_length", "avg_word_letters", "syllables_per_word",
                "pct_3plus_syllables", "plural_per_1000", "we_only", "our_only",
                "singular_per_1000", "i_only", "avg_sentence_tone"]

    log("TEST 1: Trend over time (Spearman rank correlation with year)")
    log(f"{'measure':24}{'all':>7}{'p':>9}{'long only':>11}{'no 2017+':>10}{'1900+':>8}")
    long_only = df[df["word_count"] >= SHORT_SPEECH]
    no_recent = df[df["year"] < 2017]
    modern = df[df["year"] >= 1900]
    for m in measures:
        log(f"{m:24}{spearman(df['year'], df[m]):7.2f}{permutation_p(df['year'], df[m]):9.4f}"
            f"{spearman(long_only['year'], long_only[m]):11.2f}"
            f"{spearman(no_recent['year'], no_recent[m]):10.2f}"
            f"{spearman(modern['year'], modern[m]):8.2f}")
    log(f"Speeches: all {len(df)}, long only {len(long_only)}, no 2017+ {len(no_recent)}, 1900+ {len(modern)}")

    log()
    log(f"TEST 2: Has it flattened? Change per century, before and after {BREAK_YEAR}")
    before, after = df[df["year"] < BREAK_YEAR], df[df["year"] >= BREAK_YEAR]
    log(f"{'measure':24}{'before':>9}{'after':>9}{'rho after':>11}{'p after':>9}")
    for m in ["flesch_kincaid_grade", "gunning_fog", "coleman_liau", "avg_sentence_length",
              "plural_per_1000", "singular_per_1000"]:
        log(f"{m:24}{slope_per_century(before, m):9.2f}{slope_per_century(after, m):9.2f}"
            f"{spearman(after['year'], after[m]):11.2f}{permutation_p(after['year'], after[m]):9.4f}")

    log()
    log("TEST 3: Averages by era (mean / median)")
    bins = [1788, 1849, 1899, 1949, 1999, 2030]
    labels = ["1789-1849", "1853-1897", "1901-1949", "1953-1997", "2001-2025"]
    df["era"] = pd.cut(df["year"], bins, labels=labels)
    columns = ["flesch_kincaid_grade", "coleman_liau", "avg_sentence_length", "syllables_per_word",
               "plural_per_1000", "singular_per_1000"]
    era = df.groupby("era", observed=True)[columns].agg(["mean", "median"]).round(2)
    log(era.T.to_string())
    log("Speeches per era: " + df["era"].value_counts(sort=False).to_string().replace("\n", ", "))

    log()
    log("TEST 4: Lowest and highest reading grades")
    ranked = df.sort_values("flesch_kincaid_grade")[["year", "president", "flesch_kincaid_grade", "word_count"]]
    log(ranked.head(3).to_string(index=False))
    log(ranked.tail(3).to_string(index=False))

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")
    print(f"\nSaved {REPORT_FILE.name}")


if __name__ == "__main__":
    main()
