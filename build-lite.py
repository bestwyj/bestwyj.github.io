"""
诗词热度蒸馏脚本 Python版
基于 build-scored-data.js 的逻辑，但限制 lite 数据不超过 1W 条
"""
import json, sys, codecs, os

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

INPUT = 'D:/bestwyj.github.io/poetry-data.json'
OUTPUT_LITE = 'D:/bestwyj.github.io/poetry-data-lite.json'
REF_DIR = 'D:/huajianji_temp/data'
TEXTBOOK_DIRS = ['D:/textbook_ref/old.教科书', 'D:/textbook_ref/教科书选诗']

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)
titles = data['titles']
authors = data['authors']
couplets = data['couplets']

# ========== 1. Load reference datasets ==========

def load_reference(filename):
    try:
        fp = os.path.join(REF_DIR, filename)
        with open(fp, 'r', encoding='utf-8') as f:
            poems = json.load(f)
        result = {}
        for p in poems:
            author = (p.get('author') or '').strip()
            title = (p.get('title') or '').strip()
            if not author or not title:
                continue
            if author not in result:
                result[author] = set()
            result[author].add(title)
        return result
    except Exception as e:
        print(f'  Skip {filename}: {e}')
        return {}

def load_textbook(directory):
    poems = []
    if not os.path.isdir(directory):
        return poems
    for fn in os.listdir(directory):
        if not fn.endswith('.json'):
            continue
        try:
            with open(os.path.join(directory, fn), 'r', encoding='utf-8') as f:
                poems.extend(json.load(f))
        except:
            pass
    return poems

ref300 = load_reference('唐诗三百首/0.唐诗三百首.json')
ci300 = load_reference('宋词三百首/0.宋词三百首.json')
for a, ts in ci300.items():
    if a in ref300:
        ref300[a].update(ts)
    else:
        ref300[a] = ts

textbook_poems = []
for d in TEXTBOOK_DIRS:
    textbook_poems.extend(load_textbook(d))

# Textbook title map
textbook_titles = {}
for p in textbook_poems:
    a = (p.get('author') or '').strip()
    t = (p.get('title') or '').strip()
    if not a or not t:
        continue
    if a not in textbook_titles:
        textbook_titles[a] = set()
    textbook_titles[a].add(t)

# Textbook first-line lookup
textbook_first = {}
for p in textbook_poems:
    a = (p.get('author') or '').strip()
    paras = p.get('paragraphs') or p.get('paragraphs') or []
    if not a or not paras:
        continue
    first_para = paras[0]
    # Remove punctuation
    combined = ''.join(c for c in first_para if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')
    if len(combined) < 6:
        continue
    short6 = combined[:6]
    if a not in textbook_first:
        textbook_first[a] = []
    textbook_first[a].append({'short6': short6, 'title': t})

print(f'Ref300: {sum(len(v) for v in ref300.values())} titles from {len(ref300)} authors')
print(f'Textbook: {sum(len(v) for v in textbook_titles.values())} titles from {len(textbook_titles)} authors')

# ========== 2. Poet tiers ==========

TIER_S = {'李白', '杜甫', '白居易', '王维', '苏轼'}
TIER_A = {
    '孟浩然', '杜牧', '李商隐', '王昌龄', '王之涣', '柳宗元',
    '刘禹锡', '岑参', '高适', '崔颢', '张九龄', '贺知章', '王勃',
    '陈子昂', '张继', '贾岛', '李清照', '陆游', '辛弃疾', '柳永',
    '晏殊', '晏几道', '秦观', '周邦彦', '姜夔', '李煜',
    '韦应物', '韩愈', '欧阳修', '王安石', '杨万里', '范成大', '朱熹',
    # 魏晋诗人
    '陶潜', '曹植',
}
TIER_B = {
    '李贺', '张若虚', '刘长卿', '戴叔伦', '司空曙', '许浑',
    '罗隐', '杜荀鹤', '林逋', '梅尧臣', '苏辙', '司马光',
    '邵雍', '冯延巳', '范仲淹', '黄庭坚', '文天祥', '杨炯',
    '卢照邻', '骆宾王', '张籍', '元稹', '温庭筠', '韦庄',
    '王建', '常建', '卢纶', '钱起', '李峤', '王翰',
    # 魏晋诗人
    '阮籍', '陆机', '张华', '傅玄', '嵇康', '王粲', '潘岳', '郭璞', '左思',
    '曹丕', '刘桢', '谢灵运', '鲍照', '谢朓', '陶渊明',
}
TIER_C = {
    '张祜', '崔曙', '裴迪', '权德舆', '武元衡', '李益',
    '姚合', '方干', '韩偓', '郑谷', '皮日休', '陆龟蒙',
    '贯休', '齐己', '宋祁', '张先', '晁补之', '张孝祥',
    '刘方平', '祖咏', '沈佺期', '宋之问', '韩翃', '顾况',
    '赵嘏', '马戴', '鱼玄机', '薛涛', '陈陶', '施肩吾',
    '刘昚虚', '金昌绪', '崔国辅', '綦毋潜', '丘为',
    # 魏晋诗人
    '张协', '应璩', '应玚', '蔡琰', '诸葛亮', '曹操',
}

# ========== 3. Title matching ==========

def titles_match(ref_title, db_title):
    if ref_title == db_title:
        return True
    ref_base = ref_title.split('·')[0].split('/')[0].split('、')[0]
    ref_base = ref_base.replace('三首','').replace('二首','').replace('一首','')
    import re
    ref_base = re.sub(r'其[一二三四五六七八九十]+$', '', ref_base)
    ref_base = re.sub(r'·.*$', '', ref_base)
    ref_base = re.sub(r'第.*首$', '', ref_base)
    db_base = re.sub(r'\s*[一二三四五六七八九十]+$', '', db_title)
    db_base = re.sub(r'\s*其[一二三四五六七八九十]+$', '', db_base)
    db_base = re.sub(r'\s*[（(][一二三四五六七八九十]+[）)]$', '', db_base)
    if ref_base and db_base.startswith(ref_base):
        return True
    if ref_base and db_base == ref_base:
        return True
    if len(ref_base) >= 2 and len(db_base) >= 2:
        if ref_base in db_base or db_base in ref_base:
            return True
    return False

# ========== 4. Group couplets by poem ==========

poem_couplets = {}
for i, c in enumerate(couplets):
    key = f'{c[2]}:{c[3]}'
    if key not in poem_couplets:
        poem_couplets[key] = []
    poem_couplets[key].append((i, c))

def poem_has_textbook_match(key, author_name):
    cls = poem_couplets.get(key)
    if not cls:
        return False
    tb_list = textbook_first.get(author_name)
    if not tb_list:
        return False
    for idx, c in cls:
        combined = ''.join(ch for ch in (c[0]+c[1]) if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf')
        if len(combined) < 6:
            continue
        short6 = combined[:6]
        for tb in tb_list:
            if short6 == tb['short6']:
                return True
    return False

# ========== 5. Score poems ==========

poem_cpl_count = {}
for c in couplets:
    key = f'{c[2]}:{c[3]}'
    poem_cpl_count[key] = poem_cpl_count.get(key, 0) + 1

KNOWN_LINES = [
    '锄禾日当午', '谁知盘中餐', '鹅鹅鹅', '煮豆燃豆萁',
    '床前明月光', '春眠不觉晓', '白日依山尽', '红豆生南国',
    '千山鸟飞绝', '离离原上草', '远看山有色', '草长莺飞二月天',
    '牧童骑黄牛', '敕勒川阴山下', '蓬头稚子学垂纶', '好雨知时节',
    '咬定青山不放松', '浩荡离愁白日斜', '千锤万凿出深山',
    '驿外断桥边', '茅檐低小溪上', '孤村落日残霞', '明月别枝惊鹊',
    '山一程水一程', '昔我往矣杨柳依依',
    # Add 宋词 famous lines
    '了却君王天下事', '大江东去浪淘尽', '寻寻觅觅冷冷清清',
    '十年生死两茫茫', '明月几时有', '但愿人长久',
    '莫等闲白了少年头', '三十功名尘与土', '怒发冲冠凭栏处',
    '问君能有几多愁', '恰似一江春水向东流',
    '两情若是久长时', '又岂在朝朝暮暮', '此情无计可消除',
    '才下眉头却上心头', '花自飘零水自流', '一种相思两处闲愁',
    '衣带渐宽终不悔', '为伊消得人憔悴', '众里寻他千百度',
    '蓦然回首那人却在', '杨柳岸晓风残月', '今宵酒醒何处',
    '无可奈何花落去', '似曾相识燕归来', '人生自是有情痴',
    '此恨不关风与月', '落花人独立微雨', '微雨燕双飞',
    # Add 魏晋 famous lines
    '采菊东篱下', '悠然见南山', '羁鸟恋旧林', '池鱼思故渊',
    '刑天舞干戚', '猛志固常在', '种豆南山下', '草盛豆苗稀',
    '晨兴理荒秽', '带月荷锄归', '少无适俗韵', '性本爱丘山',
    '本自同根生', '相煎何太急', '捐躯赴国难', '视死忽如归',
    '明月照高楼', '流光正徘徊', '豆在釜中泣',
    '结庐在人境', '而无车马喧', '问君何能尔', '心远地自偏',
    '山气日夕嘉', '飞鸟相与还', '此中有真意', '欲辩已忘言',
    '户庭无尘杂', '虚室有余闲', '久在樊笼里', '复得返自然',
    '榆柳荫后檐', '桃李罗堂前', '暧暧远人村', '依依墟里烟',
    '狗吠深巷中', '鸡鸣桑树颠', '芳草鲜美落英', '初极狭才通人',
]

poem_heat = {}
poem_matched = set()

for i, c in enumerate(couplets):
    key = f'{c[2]}:{c[3]}'
    if key in poem_heat:
        continue

    author_name = authors[c[3]]
    title_name = titles[c[2]]
    score = 0

    # Signal 1: 三百首 match (+500)
    if author_name in ref300:
        for ref_title in ref300[author_name]:
            if titles_match(ref_title, title_name):
                score += 500
                poem_matched.add(key)
                break

    # Signal 2: Textbook title match (+450)
    if author_name in textbook_titles:
        for ref_title in textbook_titles[author_name]:
            if titles_match(ref_title, title_name):
                score += 450
                poem_matched.add(key)
                break

    # Signal 3: Textbook content match (+450)
    if key not in poem_matched:
        if poem_has_textbook_match(key, author_name):
            score += 450
            poem_matched.add(key)

    # Signal 4: Famous lines content match (+400)
    if key not in poem_matched:
        text = c[0] + c[1]
        for line in KNOWN_LINES:
            if line in text:
                score += 400
                poem_matched.add(key)
                break

    # Poet tier
    if author_name in TIER_S:
        score += 200
    elif author_name in TIER_A:
        score += 150
    elif author_name in TIER_B:
        score += 100
    elif author_name in TIER_C:
        score += 70
    elif '佚名' in author_name or '无名' in author_name:
        score += 0
    elif '皇帝' in author_name or '宗室' in author_name:
        score += 15
    elif author_name.startswith('释'):
        score += 25
    elif author_name.startswith('道'):
        score += 20
    else:
        score += 40

    # Couplet count bonus
    cpl_count = poem_cpl_count.get(key, 1)
    import math
    score += min(50, math.log2(cpl_count + 1) * 12)

    # Title length bonus
    if len(title_name) <= 3:
        score += 15
    elif len(title_name) <= 5:
        score += 10
    elif len(title_name) <= 8:
        score += 5
    if len(title_name) > 20:
        score -= 15

    score = min(999, max(1, round(score)))
    poem_heat[key] = score

print(f'Scored {len(poem_heat)} unique poems')
print(f'Total matched: {len(poem_matched)}')

# ========== 6. Build lite data ==========

# Score each couplet
scored = []
for i, c in enumerate(couplets):
    key = f'{c[2]}:{c[3]}'
    scored.append((c[0], c[1], c[2], c[3], poem_heat.get(key, 0), i))

# Sort by score descending
scored.sort(key=lambda x: x[4], reverse=True)

# Deduplicate and collect unique couplets
seen = set()
unique = []
unique_poem_keys = set()

for upper, lower, t_idx, a_idx, score, orig_idx in scored:
    key = upper + '|' + lower
    poem_key = f'{t_idx}:{a_idx}'
    if key not in seen:
        seen.add(key)
        unique.append([upper, lower, t_idx, a_idx, score])
        unique_poem_keys.add(poem_key)

# Ensure matched textbook poems are included
required = [k for k in poem_matched if k not in unique_poem_keys]
print(f'Required textbook poems not in top: {len(required)}')

required_set = set(required)
for upper, lower, t_idx, a_idx, score, orig_idx in scored:
    poem_key = f'{t_idx}:{a_idx}'
    if poem_key in required_set:
        key2 = upper + '|' + lower
        if key2 not in seen:
            seen.add(key2)
            unique.append([upper, lower, t_idx, a_idx, score])

# Limit to 50K
lite_limit = 50000
lite = unique[:lite_limit]

# Remap
used_titles = set()
used_authors = set()
for c in lite:
    used_titles.add(c[2])
    used_authors.add(c[3])

lite_titles_arr = sorted(used_titles)
lite_authors_arr = sorted(used_authors)
title_remap = {old: i for i, old in enumerate(lite_titles_arr)}
author_remap = {old: i for i, old in enumerate(lite_authors_arr)}

lite_data = {
    'titles': [titles[i] for i in lite_titles_arr],
    'authors': [authors[i] for i in lite_authors_arr],
    'couplets': [[c[0], c[1], title_remap[c[2]], author_remap[c[3]], c[4]] for c in lite]
}

with open(OUTPUT_LITE, 'w', encoding='utf-8') as f:
    json.dump(lite_data, f, ensure_ascii=False)

print(f'\nLite: {len(lite_data["couplets"])} couplets, {len(lite_data["titles"])} titles, {len(lite_data["authors"])} authors')
size_mb = os.path.getsize(OUTPUT_LITE) / 1024 / 1024
print(f'Lite size: {size_mb:.1f} MB')

# Verify
print('\nVerifying key poems:')
checks = [
    ('云母屏风', '李商隐'),
    ('春眠不觉', '孟浩然'),
    ('了却', '辛弃疾'),
    ('大江东去', '苏轼'),
    ('寻寻觅觅', '李清照'),
    ('明月几时', '苏轼'),
    ('衣带渐宽', '柳永'),
    ('莫等闲白', '岳飞'),
]
for s, a in checks:
    found = False
    for c in lite_data['couplets']:
        if lite_data['authors'][c[3]] == a and (s in c[0] or s in c[1]):
            print(f'  ✓ {s} {a} heat: {c[4]} : {c[0]}，{c[1]}')
            found = True
            break
    if not found:
        print(f'  ✗ {s} {a} NOT FOUND')
