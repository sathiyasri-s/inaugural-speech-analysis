"""
Creates the charts in charts/ from results/speech_metrics.csv.

Usage:
    python analyze.py        # first
    python make_charts.py
"""

import re
from pathlib import Path

import matplotlib
import pandas as pd
import textstat
from nltk.corpus import inaugural

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
METRICS_FILE = BASE_DIR / "results" / "speech_metrics.csv"
CHARTS_DIR = BASE_DIR / "charts"

# 1200 x 1350 px: fills the width of a phone screen in the LinkedIn feed
FIG_SIZE = (6, 6.75)
DPI = 200

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e6e5e0"
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"

ROLLING_WINDOW = 7      # speeches
FIRST_ERA = (1789, 1849)
LAST_ERA = (2001, 2025)
ERA_BINS = [1788, 1849, 1899, 1949, 1999, 2030]
ERA_LABELS = ["1789–\n1849", "1853–\n1897", "1901–\n1949", "1953–\n1997", "2001–\n2025"]

WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": TEXT_PRIMARY,
    "axes.labelcolor": TEXT_SECONDARY,
    "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_SECONDARY,
})


def era_mean(df, column, era):
    return df[df["year"].between(*era)][column].mean()


def new_figure(title, subtitle):
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=DPI)
    fig.subplots_adjust(left=0.09, right=0.95, top=0.76, bottom=0.17)
    fig.text(0.05, 0.955, title, fontsize=19, fontweight="bold", va="top", linespacing=1.15)
    fig.text(0.05, 0.815, subtitle, fontsize=11, color=TEXT_SECONDARY, va="top", linespacing=1.3)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, labelsize=11)
    return fig, ax


def add_footer(fig, text):
    fig.text(0.05, 0.03, text, fontsize=8.5, color=TEXT_SECONDARY, va="bottom", linespacing=1.35)


def save(fig, name):
    CHARTS_DIR.mkdir(exist_ok=True)
    fig.savefig(CHARTS_DIR / name, dpi=DPI)
    plt.close(fig)
    print(f"Saved charts/{name}")


def trend_chart(df, column, title, subtitle, unit, name, label_offsets, y_top, footer):
    """Every speech as a dot, a rolling median as a line, and the two era averages as labels."""
    fig, ax = new_figure(title, subtitle)
    trend = df[column].rolling(ROLLING_WINDOW, center=True, min_periods=4).median()

    ax.scatter(df["year"], df[column], s=30, color=SERIES_1, alpha=0.3,
               edgecolors=SURFACE, linewidths=0.6, clip_on=False, zorder=2)
    ax.plot(df["year"], trend, color=SERIES_1, linewidth=2.4,
            solid_capstyle="round", solid_joinstyle="round", zorder=3)

    for era, (x, y) in zip((FIRST_ERA, LAST_ERA), label_offsets):
        value = era_mean(df, column, era)
        ax.annotate(f"{value:.0f} {unit}", (x, y), fontsize=17, fontweight="bold",
                    ha="center", va="bottom", zorder=4)
        ax.annotate(f"average, {era[0]}–{era[1]}", (x, y), xytext=(0, -3),
                    textcoords="offset points", fontsize=10, color=TEXT_SECONDARY,
                    ha="center", va="top", zorder=4)

    ax.set_ylim(0, y_top)
    ax.set_xlim(1780, 2034)
    ax.set_xticks(range(1800, 2026, 50))
    add_footer(fig, footer)
    save(fig, name)


def syllables_per_word(year, president):
    text = inaugural.raw(f"{year}-{president}.txt")
    words = WORD.findall(text)
    return sum(textstat.syllable_count(w) for w in words) / len(words)


def sentences_vs_words_chart(df):
    """Sentence length and syllables per word by era, both indexed to the first era = 100."""
    df = df.copy()
    df["syllables_per_word"] = [syllables_per_word(r.year, r.president) for r in df.itertuples()]
    df["era"] = pd.cut(df["year"], ERA_BINS, labels=False)
    means = df.groupby("era")[["avg_sentence_length", "syllables_per_word"]].mean()
    indexed = 100 * means / means.iloc[0]

    fig, ax = new_figure("Presidents shortened\ntheir sentences far\nmore than their words",
                         "Average for each era, with 1789–1849 set to 100")
    series = [("avg_sentence_length", SERIES_1, "Words per sentence", "o"),
              ("syllables_per_word", SERIES_2, "Syllables per word", "s")]
    for column, color, label, marker in series:
        ax.plot(indexed.index, indexed[column], color=color, linewidth=2.4, marker=marker,
                markersize=7, markeredgecolor=SURFACE, markeredgewidth=1,
                solid_capstyle="round", label=label, zorder=3)
        final = indexed[column].iloc[-1]
        ax.annotate(f"{final - 100:+.0f}%".replace("-", "−"), (indexed.index[-1], final),
                    xytext=(0, 11), textcoords="offset points", fontsize=15,
                    fontweight="bold", ha="center", zorder=4)

    ax.set_ylim(0, 120)
    ax.set_yticks(range(0, 121, 20))
    ax.set_xlim(-0.3, 4.4)
    ax.set_xticks(range(5))
    ax.set_xticklabels(ERA_LABELS)
    ax.legend(loc="lower left", frameon=False, fontsize=11, labelcolor=TEXT_PRIMARY)
    add_footer(fig, "US presidential inaugural addresses, 60 speeches. Source: NLTK inaugural corpus.\n"
                    "Syllables estimated with textstat. Sentence endings may reflect editors and transcribers.")
    save(fig, "sentences_vs_words.png")


def main():
    df = pd.read_csv(METRICS_FILE)

    sentence_early = era_mean(df, "avg_sentence_length", FIRST_ERA)
    sentence_late = era_mean(df, "avg_sentence_length", LAST_ERA)
    trend_chart(
        df, "avg_sentence_length",
        f"The average presidential\nsentence went from\n{sentence_early:.0f} words to {sentence_late:.0f}",
        "Words per sentence in every US inaugural address, 1789–2025",
        "words", "sentence_length.png",
        [(1855, 57), (1990, 34)], 70,
        "Each dot is one speech. Line: rolling median of 7 speeches. Source: NLTK inaugural corpus.\n"
        "Sentence endings may reflect editors and transcribers, especially in older speeches.",
    )

    trend_chart(
        df, "plural_per_1000",
        "\"We\" language\nmore than tripled in\ninaugural addresses",
        "We, us, our, ours and ourselves per 1,000 words, 1789–2025",
        "per 1,000", "we_language.png",
        [(1825, 42), (1965, 85)], 95,
        "Each dot is one speech. Line: rolling median of 7 speeches. Source: NLTK inaugural corpus.",
    )

    sentences_vs_words_chart(df)


if __name__ == "__main__":
    main()
