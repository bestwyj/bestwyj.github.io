"""Extract 五言/七言片句 from 魏晋.csv and merge into poetry-data.json"""
import csv, json, sys, codecs, re

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

CHAR_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

def strip_punct(s):
    return ''.join(CHAR_RE.findall(s))

# ========== Step 1: Extract couplets from 魏晋.csv ==========

all_couplets = []

with open('魏晋.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 4:
            continue
        title = row[0].strip()
        author = row[2].strip()
        content = row[3].strip()
        if not author or not content:
            continue

        # Split by sentence terminator (。！？)
        sentences = re.split(r'[。！？]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # Split by comma-like separator
            for sep in ['，', ',', '；', ';']:
                if sep in sentence:
                    parts = sentence.split(sep)
                    upper = strip_punct(parts[0])
                    lower = strip_punct(sep.join(parts[1:]))
                    if upper and lower:
                        u_len = len(upper)
                        l_len = len(lower)
                        if u_len in (5, 7) and l_len in (5, 7) and u_len == l_len:
                            all_couplets.append({
                                'title': title,
                                'author': author,
                                'upper': upper,
                                'lower': lower,
                                'char_count': u_len
                            })
                    break

print(f'Total extracted couplets: {len(all_couplets)}')

# Stats
from collections import Counter
author_counter = Counter(c['author'] for c in all_couplets)
print(f'Unique authors: {len(author_counter)}')
for author, count in author_counter.most_common(20):
    print(f'  {author}: {count}')

# Save intermediate
with open('魏晋片句.json', 'w', encoding='utf-8') as f:
    json.dump(all_couplets, f, ensure_ascii=False, indent=2)
print('Saved 魏晋片句.json')

# ========== Step 2: Merge into poetry-data.json ==========

with open('poetry-data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

titles = data['titles']
authors = data['authors']
couplets = data['couplets']

print(f'\nBefore: {len(titles)} titles, {len(authors)} authors, {len(couplets)} couplets')

title_to_idx = {t: i for i, t in enumerate(titles)}
author_to_idx = {a: i for i, a in enumerate(authors)}

existing = set()
for c in couplets:
    existing.add(c[0] + '|' + c[1] + '|' + titles[c[2]] + '|' + authors[c[3]])

new_count = 0
dup_count = 0

for c in all_couplets:
    title = c['title']
    author = c['author']
    upper = c['upper']
    lower = c['lower']

    key = upper + '|' + lower + '|' + title + '|' + author
    if key in existing:
        dup_count += 1
        continue

    if title not in title_to_idx:
        title_to_idx[title] = len(titles)
        titles.append(title)
    if author not in author_to_idx:
        author_to_idx[author] = len(authors)
        authors.append(author)

    couplets.append([upper, lower, title_to_idx[title], author_to_idx[author]])
    existing.add(key)
    new_count += 1

print(f'New couplets added: {new_count}')
print(f'Duplicates skipped: {dup_count}')
print(f'After: {len(titles)} titles, {len(authors)} authors, {len(couplets)} couplets')

data['titles'] = titles
data['authors'] = authors
data['couplets'] = couplets

with open('poetry-data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print('Saved poetry-data.json')
