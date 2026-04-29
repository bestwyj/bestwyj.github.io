import json, re, os

SONG_DIR = 'D:/bestwyj.github.io/chinese-poetry-temp/宋词'
CHAR_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

def strip_punct(s):
    return ''.join(CHAR_RE.findall(s))

def extract_couplets(paragraph_str):
    """Extract (upper, lower) couplet pairs from a paragraph string."""
    results = []
    s = paragraph_str.strip()
    for sep in ['，', ',', '；', ';']:
        if sep in s:
            parts = s.split(sep)
            upper = strip_punct(parts[0])
            lower = strip_punct(sep.join(parts[1:]))
            if upper and lower:
                results.append((upper, lower))
            break
    return results

# Collect all couplets from 宋词
all_couplets = []

for fn in sorted(os.listdir(SONG_DIR)):
    if not fn.startswith('ci.song.') or not fn.endswith('.json'):
        continue
    fp = os.path.join(SONG_DIR, fn)
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for p in data:
        author = p.get('author', '').strip()
        title = p.get('rhythmic', '').strip()
        paragraphs = p.get('paragraphs', [])
        for para in paragraphs:
            couples = extract_couplets(para)
            for upper, lower in couples:
                u_len = len(upper)
                l_len = len(lower)
                # Keep only 5 or 7 character couplets
                if u_len in (5, 7) and l_len in (5, 7) and u_len == l_len:
                    all_couplets.append({
                        'author': author,
                        'title': title,
                        'upper': upper,
                        'lower': lower,
                        'char_count': u_len
                    })

print(f'Total extracted couplets: {len(all_couplets)}')

# Show stats
from collections import Counter
author_counter = Counter(c['author'] for c in all_couplets)
print(f'Unique authors: {len(author_counter)}')
print(f'Top 20 authors:')
for author, count in author_counter.most_common(20):
    print(f'  {author}: {count}')

# Sample
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

print(f'\nSample couplets:')
for c in all_couplets[:10]:
    print(f"  {c['upper']}，{c['lower']}  ({c['author']} 《{c['title']}》)")

# Save intermediate
with open('D:/bestwyj.github.io/song_couplets.json', 'w', encoding='utf-8') as f:
    json.dump(all_couplets, f, ensure_ascii=False, indent=2)
print(f'\nSaved to song_couplets.json')
