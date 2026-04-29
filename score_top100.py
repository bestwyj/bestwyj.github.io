import json

# 读取200个常用字
with open('e:/CDisk/Downloads/字.txt', 'r', encoding='utf-8') as f:
    common_chars = set(line.strip() for line in f if line.strip())

print(f'常用字数量: {len(common_chars)}')

# 读取诗词数据
with open('D:/bestwyj.github.io/poetry-data-lite.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

titles = data['titles']
authors = data['authors']
couplets = data['couplets']

five_results = []
seven_results = []

for i, c in enumerate(couplets):
    combined = c[0] + c[1]
    # 判断五言还是七言
    if len(combined) == 10:
        char_type = 'five'
    elif len(combined) == 14:
        char_type = 'seven'
    else:
        continue

    # 计算常用字数量作为分数
    score = sum(1 for ch in combined if ch in common_chars)

    entry = {
        'upper': c[0],
        'lower': c[1],
        'title': titles[c[2]],
        'author': authors[c[3]],
        'heat': c[4],
        'score': score,
        'couplet_idx': i
    }

    if char_type == 'five':
        five_results.append(entry)
    else:
        seven_results.append(entry)

# 按分数降序，分数相同按热度降序
five_results.sort(key=lambda x: (-x['score'], -x['heat']))
seven_results.sort(key=lambda x: (-x['score'], -x['heat']))

top100_five = five_results[:100]
top100_seven = seven_results[:100]

print(f'五言总数: {len(five_results)}, top100 最高分: {top100_five[0]["score"] if top100_five else 0}')
print(f'七言总数: {len(seven_results)}, top100 最高分: {top100_seven[0]["score"] if top100_seven else 0}')
print(f'五言 top100 最低分: {top100_five[-1]["score"] if top100_five else 0}')
print(f'七言 top100 最低分: {top100_seven[-1]["score"] if top100_seven else 0}')

# 保存
output = {
    'common_chars': sorted(list(common_chars)),
    'top100_five': top100_five,
    'top100_seven': top100_seven
}

with open('D:/bestwyj.github.io/top100-popular.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print('已保存到 top100-popular.json')
