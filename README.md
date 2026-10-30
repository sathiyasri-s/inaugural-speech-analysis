# 236 years of US inaugural addresses

A text analysis of all 60 US presidential inaugural addresses, from Washington in
1789 to 2025. Did presidents start speaking more simply? And did they start saying
"we" more?

![Words per sentence in every inaugural address, 1789 to 2025](charts/sentence_length.png)

## Findings

| Measure | 1789–1849 | 2001–2025 | Change |
|---|---|---|---|
| Words per sentence | 43 | 19 | −57% |
| "We" language per 1,000 words | 18 | 64 | more than tripled |
| Syllables per word | 1.65 | 1.53 | −7% |
| Flesch-Kincaid grade | 20.7 | 9.9 | |

1. **Sentences got much shorter.** The average fell from 43 words to 19.
2. **Sentences changed far more than words.** Syllables per word fell only 7%, so most
   of the drop in reading level comes from sentence length.
3. **"We" language more than tripled.** Most of the rise came after about 1900.
4. **The reading level has shown no clear trend since 1950.** Only 19 speeches fall in
   that period, so this is weak evidence, not proof that the decline stopped.

![Sentence length and syllables per word by era](charts/sentences_vs_words.png)

![We language per 1,000 words, 1789 to 2025](charts/we_language.png)

## What the data did not support

- **"I" was replaced by "we".** I expected this, but "I" language shows no trend since
  1900, while "we" kept rising.
- **Tone changed over time.** The link is weak and nearly zero since 1900. VADER was
  also built for modern text, so it is not reliable on 18th-century English.

## Limits

- **Punctuation:** where a sentence ends may reflect editors and transcribers,
  especially in older speeches. The main finding depends on sentence length, and
  this data cannot rule that effect out.
- **Causes:** the data shows when things changed, not why. Radio, TV and education are
  possible explanations, but none is tested here.
- **Grade levels:** a score of 20 is not a real school grade. It is best read as a
  relative measure, driven by very long sentences.
- **Sample size:** there is only one speech every four years, and 60 in total.

## How the findings were checked

`check_trends.py` tests whether each trend survives when the method changes. The full
output is in [`results/trend_checks.txt`](results/trend_checks.txt).

- Four readability formulas: Flesch-Kincaid, Gunning Fog, Coleman-Liau and Automated
  Readability
- Measures that ignore sentence endings: letters per word, syllables per word and the
  share of long words
- Removing the 4 speeches under 1,000 words
- Removing the 3 most recent speeches
- Looking only at speeches since 1900
- Permutation tests for significance, using rank correlation so outliers matter less

## Run it yourself

Requires Python 3.10 or newer.

```bash
pip install -r requirements.txt
python analyze.py
python check_trends.py
python make_charts.py
```

NLTK's data is downloaded automatically the first time `analyze.py` runs.

| File | What it does |
|---|---|
| `analyze.py` | Measures every speech and writes `results/speech_metrics.csv` |
| `check_trends.py` | Runs the checks above and writes `results/trend_checks.txt` |
| `make_charts.py` | Creates the images in `charts/` |

## Data and tools

- **Speeches:** [NLTK](https://www.nltk.org/)'s inaugural address corpus
- **Readability:** [textstat](https://github.com/textstat/textstat)
- **Sentiment:** VADER, through NLTK
- **Analysis and charts:** pandas, NumPy and Matplotlib

## License

The code is available under the [MIT License](LICENSE).
