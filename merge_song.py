"""Merge 宋词 couplets into poetry-data.json"""
import json, sys, codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

# Load existing data
with open('D:/bestwyj.github.io/poetry-data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

titles = data['titles']
authors = data['authors']
couplets = data['couplets']

print(f'Before: {len(titles)} titles, {len(authors)} authors, {len(couplets)} couplets')

# Load song couplets
with open('D:/bestwyj.github.io/song_couplets.json', 'r', encoding='utf-8') as f:
    song_data = json.load(f)

# Build index maps
title_to_idx = {}
for i, t in enumerate(titles):
    title_to_idx[t] = i

author_to_idx = {}
for i, a in enumerate(authors):
    author_to_idx[a] = i

# Deduplicate existing couplets (as set of strings for fast lookup)
existing = set()
for c in couplets:
    existing.add(c[0] + '|' + c[1] + '|' + titles[c[2]] + '|' + authors[c[3]])

new_count = 0
dup_count = 0

for c in song_data:
    title = c['title']
    author = c['author']
    upper = c['upper']
    lower = c['lower']

    key = upper + '|' + lower + '|' + title + '|' + author

    if key in existing:
        dup_count += 1
        continue

    # Add title if new
    if title not in title_to_idx:
        title_to_idx[title] = len(titles)
        titles.append(title)

    # Add author if new
    if author not in author_to_idx:
        author_to_idx[author] = len(authors)
        authors.append(author)

    couplets.append([upper, lower, title_to_idx[title], author_to_idx[author]])
    existing.add(key)
    new_count += 1

print(f'New couplets added: {new_count}')
print(f'Duplicates skipped: {dup_count}')
print(f'After: {len(titles)} titles, {len(authors)} authors, {len(couplets)} couplets')

# Save
data['titles'] = titles
data['authors'] = authors
data['couplets'] = couplets

with open('D:/bestwyj.github.io/poetry-data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print('Saved poetry-data.json')
