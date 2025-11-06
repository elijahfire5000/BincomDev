import re
from collections import Counter
import random
from typing import List, Tuple
from urllib.request import localhost

import psycopg2  # NEW: PostgreSQL support

HTML_FILE = "python_class_question.html"

# -------- parsing & normalization --------
def load_html(path: str = HTML_FILE) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()

def extract_color_rows(html: str) -> List[str]:
    return re.findall(r'<tr>\s*<td>\s*[^<]+</td>\s*<td>\s*([^<]+)</td>\s*</tr>', html, flags=re.IGNORECASE)

def normalize_color(name: str) -> str:
    s = name.strip().upper()
    corrections = {
        "BLEW": "BLUE",
        "BLUW": "BLUE",
        "BLU": "BLUE",
    }
    return corrections.get(s, s)

def flatten_colors(rows: List[str]) -> List[str]:
    flat = []
    for line in rows:
        parts = [p.strip() for p in re.split(r',\s*', line) if p.strip()]
        flat.extend(normalize_color(p) for p in parts)
    return flat

# -------- statistics helpers --------
def mode_colors(freq: Counter) -> Tuple[List[str], int]:
    if not freq:
        return [], 0
    maxf = max(freq.values())
    return [c for c,f in freq.items() if f == maxf], maxf

def mean_color(freq: Counter) -> Tuple[float, List[str]]:
    if not freq:
        return 0.0, []
    values = list(freq.values())
    meanv = sum(values) / len(values)
    min_diff = None
    closest = []
    for c, f in freq.items():
        diff = abs(f - meanv)
        if (min_diff is None) or (diff < min_diff):
            min_diff = diff
            closest = [c]
        elif diff == min_diff:
            closest.append(c)
    return meanv, closest

def median_color(freq: Counter) -> List[str]:
    if not freq:
        return []
    items = sorted(freq.items(), key=lambda kv: kv[1])
    n = len(items)
    if n % 2 == 1:
        return [items[n//2][0]]
    else:
        return [items[n//2 - 1][0], items[n//2][0]]

def variance_of_frequencies(freq: Counter) -> float:
    if not freq:
        return 0.0
    vals = list(freq.values())
    meanv = sum(vals) / len(vals)
    return sum((x - meanv)**2 for x in vals) / len(vals)

# -------- PostgreSQL save function --------
def save_to_postgres(freq: Counter, dbname="colors_db", user="postgres", password="postgres", host="localhost", port="5432"):
    """
    Saves color frequencies to a PostgreSQL database.
    Table: color_frequencies(color TEXT PRIMARY KEY, frequency INT)
    """
    try:
        conn = psycopg2.connect(
            dbname=dbname, user="postgres", password="", host="localhost", port="5432"
        )
        cur = conn.cursor()
        # Create table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS color_frequencies (
                color TEXT PRIMARY KEY,
                frequency INT
            )
        """)
        # Insert or update frequencies
        for color, count in freq.items():
            cur.execute("""
                INSERT INTO color_frequencies (color, frequency)
                VALUES (%s, %s)
                ON CONFLICT (color) DO UPDATE
                SET frequency = EXCLUDED.frequency
            """, (color, count))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Colors successfully saved to PostgreSQL table 'color_frequencies'.")
    except Exception as e:
        print("Error saving to PostgreSQL:", e)

# -------- other tasks --------
def recursive_search(lst: List[int], target: int, index: int = 0) -> int:
    if index >= len(lst):
        return -1
    if lst[index] == target:
        return index
    return recursive_search(lst, target, index+1)

def random_binary_to_decimal(n_digits: int = 4) -> Tuple[str,int]:
    bits = [str(random.choice([0,1])) for _ in range(n_digits)]
    bstr = ''.join(bits)
    return bstr, int(bstr, 2)

def sum_first_n_fibonacci(n: int = 50) -> int:
    a, b = 0, 1
    total = 0
    for _ in range(n):
        total += a
        a, b = b, a + b
    return total

# -------- runner --------
def main():
    html = load_html()
    rows = extract_color_rows(html)
    if not rows:
        print("ERROR: Could not parse color rows from HTML. Make sure python_class_question.html is in the same folder.")
        return

    flat = flatten_colors(rows)
    freq = Counter(flat)
    total = sum(freq.values())

    meanv, mean_colors = mean_color(freq)
    modes, mode_freq = mode_colors(freq)
    medians = median_color(freq)
    var_freq = variance_of_frequencies(freq)
    red_count = freq.get("RED", 0)
    prob_red = red_count / total if total > 0 else 0.0

    print("\n==== RESULTS (per question) ====\n")

    print("Question 1) Mean color:")
    print(f"  - Mean frequency: {meanv:.3f}")
    print(f"  - Closest color(s): {', '.join(mean_colors)}\n")

    print("Question 2) Mode color:")
    print(f"  - {', '.join(modes)} ({mode_freq} times)\n")

    print("Question 3) Median color:")
    print(f"  - {', '.join(medians)}\n")

    print("Question 4) Variance:")
    print(f"  - {var_freq:.4f}\n")

    print("Question 5) Probability RED:")
    print(f"  - RED count: {red_count}/{total}")
    print(f"  - Probability: {prob_red:.4f}\n")

    print("Question 6) Save to PostgreSQL database")
    save_to_postgres(freq)  # NEW call
    print()

    print("Question 7) Recursive search:")
    demo_list = [3,5,7,9,11,13]
    demo_target = 9
    idx_found = recursive_search(demo_list, demo_target)
    print(f"  - Found {demo_target} at index {idx_found}\n")

    print("Question 8) Random binary to decimal:")
    bstr, dec = random_binary_to_decimal(4)
    print(f"  - {bstr} -> {dec}\n")

    print("Question 9) Sum of first 50 Fibonacci numbers:")
    fib_sum = sum_first_n_fibonacci(50)
    print(f"  - Sum: {fib_sum}\n")

    print("==== END ====\n")

if __name__ == "__main__":
    main()
