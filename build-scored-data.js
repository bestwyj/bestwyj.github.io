/**
 * 诗词热度蒸馏脚本 v10
 * 使用唐诗三百首、宋词三百首 + 教科书数据
 * 确保所有教科书中的诗词都包含在 lite 数据中
 */
const fs = require('fs');

const INPUT = 'D:/bestwyj.github.io/poetry-data.json';
const OUTPUT_LITE = 'D:/bestwyj.github.io/poetry-data-lite.json';
const REF_DIR = 'D:/huajianji_temp/data';
const TEXTBOOK_DIRS = [
  'D:/textbook_ref/old.教科书',
  'D:/textbook_ref/教科书选诗',
];

const data = JSON.parse(fs.readFileSync(INPUT, 'utf8'));
const { titles, authors, couplets } = data;

// ========== 1. 加载参考数据集 ==========

function loadReference(filename) {
  try {
    const poems = JSON.parse(fs.readFileSync(REF_DIR + '/' + filename, 'utf8'));
    const map = new Map();
    for (const p of poems) {
      const author = (p.author || '').trim();
      const title = (p.title || '').trim();
      if (!author || !title) continue;
      if (!map.has(author)) map.set(author, new Set());
      map.get(author).add(title);
    }
    return map;
  } catch (e) { return new Map(); }
}

function loadTextbook(dir) {
  const poems = [];
  try {
    const files = fs.readdirSync(dir);
    for (const f of files) {
      if (!f.endsWith('.json')) continue;
      const d = JSON.parse(fs.readFileSync(dir + '/' + f, 'utf8'));
      poems.push(...d);
    }
  } catch (e) {}
  return poems;
}

const ref300Map = loadReference('唐诗三百首/0.唐诗三百首.json');
for (const [a, ts] of loadReference('宋词三百首/0.宋词三百首.json')) {
  if (ref300Map.has(a)) { for (const t of ts) ref300Map.get(a).add(t); }
  else ref300Map.set(a, new Set(ts));
}

const textbookPoems = [...loadTextbook(TEXTBOOK_DIRS[0]), ...loadTextbook(TEXTBOOK_DIRS[1])];

// Build textbook title map
const textbookMap = new Map();
for (const p of textbookPoems) {
  const a = (p.author||'').trim(), t = (p.title||'').trim();
  if (!a || !t) continue;
  if (!textbookMap.has(a)) textbookMap.set(a, new Set());
  textbookMap.get(a).add(t);
}

// Build textbook first-line lookup using the FULL first couplet (上句+下句)
// Key: author -> array of {combined8, title}
// We use upper+lower combined (去掉标点)的前8个字符
const textbookCombined = new Map();
for (const p of textbookPoems) {
  const a = (p.author||'').trim();
  if (!a || !p.paragraphs || p.paragraphs.length === 0) continue;
  // First paragraph = first couplet (上句+下句 with punctuation)
  const combined = p.paragraphs[0].replace(/[，。！？；：、\s]/g, '');
  if (combined.length < 6) continue;
  if (!textbookCombined.has(a)) textbookCombined.set(a, []);
  textbookCombined.get(a).push({ short6: combined.substring(0, 6), title: p.title });
}

console.log('Ref300:', [...ref300Map.values()].reduce((s,v) => s+v.size, 0), 'titles from', ref300Map.size, 'authors');
console.log('Textbook:', [...textbookMap.values()].reduce((s,v) => s+v.size, 0), 'titles from', textbookMap.size, 'authors');

// ========== 2. 诗人分级 ==========

const TIER_S_POETS = new Set(['李白', '杜甫', '白居易', '王维', '苏轼']);
const TIER_A_POETS = new Set([
  '孟浩然', '杜牧', '李商隐', '王昌龄', '王之涣', '柳宗元',
  '刘禹锡', '岑参', '高适', '崔颢', '张九龄', '贺知章', '王勃',
  '陈子昂', '张继', '贾岛', '李清照', '陆游', '辛弃疾', '柳永',
  '晏殊', '晏几道', '秦观', '周邦彦', '姜夔', '李煜',
  '韦应物', '韩愈', '欧阳修', '王安石', '杨万里', '范成大', '朱熹',
]);
const TIER_B_POETS = new Set([
  '李贺', '张若虚', '刘长卿', '戴叔伦', '司空曙', '许浑',
  '罗隐', '杜荀鹤', '林逋', '梅尧臣', '苏辙', '司马光',
  '邵雍', '冯延巳', '范仲淹', '黄庭坚', '文天祥', '杨炯',
  '卢照邻', '骆宾王', '张籍', '元稹', '温庭筠', '韦庄',
  '王建', '常建', '卢纶', '钱起', '李峤', '王翰',
]);
const TIER_C_POETS = new Set([
  '张祜', '崔曙', '裴迪', '权德舆', '武元衡', '李益',
  '姚合', '方干', '韩偓', '郑谷', '皮日休', '陆龟蒙',
  '贯休', '齐己', '宋祁', '张先', '晁补之', '张孝祥',
  '刘方平', '祖咏', '沈佺期', '宋之问', '韩翃', '顾况',
  '赵嘏', '马戴', '鱼玄机', '薛涛', '陈陶', '施肩吾',
  '刘昚虚', '金昌绪', '崔国辅', '綦毋潜', '丘为',
]);

// ========== 3. 标题匹配 ==========

function titlesMatch(refTitle, dbTitle) {
  if (refTitle === dbTitle) return true;
  const refBase = refTitle.split(/[·/、]/)[0].replace(/(?:三首|二首|一首|其[一二三四五六七八九十]+|·.*|第.*首)$/, '');
  const dbBase = dbTitle.replace(/\s*[一二三四五六七八九十]+$|\s*其[一二三四五六七八九十]+$|\s*[（(][一二三四五六七八九十]+[）)]$/, '');
  if (refBase && dbBase.startsWith(refBase)) return true;
  if (refBase && dbBase === refBase) return true;
  if (refBase.length >= 2 && dbBase.length >= 2) {
    if (refBase.includes(dbBase) || dbBase.includes(refBase)) return true;
  }
  return false;
}

// ========== 4. 内容匹配：检查 poem 的任一 couplet 是否匹配教科书的首句 ==========

// Group couplets by poem
const poemCoupletMap = new Map();
for (const c of couplets) {
  const key = c[2] + ':' + c[3];
  if (!poemCoupletMap.has(key)) poemCoupletMap.set(key, []);
  poemCoupletMap.get(key).push(c);
}

function poemHasTextbookMatch(key, authorName) {
  const cls = poemCoupletMap.get(key);
  if (!cls) return false;
  if (!textbookCombined.has(authorName)) return false;
  const tbEntries = textbookCombined.get(authorName);
  for (const c of cls) {
    const combined = (c[0] + c[1]).replace(/[，。！？；：、\s]/g, '');
    if (combined.length < 6) continue;
    const short6 = combined.substring(0, 6);
    for (const tb of tbEntries) {
      if (short6 === tb.short6) return true;
    }
  }
  return false;
}

// ========== 5. 评分 ==========

const poemCoupletCount = {};
for (const c of couplets) {
  const key = c[2] + ':' + c[3];
  poemCoupletCount[key] = (poemCoupletCount[key] || 0) + 1;
}

const poemHeat = new Map();
const poemMatched = new Set();

for (const c of couplets) {
  const key = c[2] + ':' + c[3];
  if (!poemHeat.has(key)) {
    const authorName = authors[c[3]];
    const titleName = titles[c[2]];
    let score = 0;

    // 信号1: 唐诗三百首/宋词三百首匹配 (+500)
    if (ref300Map.has(authorName)) {
      for (const refTitle of ref300Map.get(authorName)) {
        if (titlesMatch(refTitle, titleName)) {
          score += 500;
          poemMatched.add(key);
          break;
        }
      }
    }

    // 信号2: 教科书标题匹配 (+450)
    if (textbookMap.has(authorName)) {
      for (const refTitle of textbookMap.get(authorName)) {
        if (titlesMatch(refTitle, titleName)) {
          score += 450;
          poemMatched.add(key);
          break;
        }
      }
    }

    // 信号3: 教科书内容匹配（检查任一couplet是否匹配教科书首句）(+450)
    if (!poemMatched.has(key)) {
      if (poemHasTextbookMatch(key, authorName)) {
        score += 450;
        poemMatched.add(key);
      }
    }

    // 信号4: 额外教科书知名诗词内容匹配（标题不匹配但内容知名的）(+400)
    // 这些诗在教科书中但标题差异太大无法通过标题匹配
    if (!poemMatched.has(key)) {
      const text = c[0] + c[1];
      const knownLines = ['锄禾日当午', '谁知盘中餐', '鹅鹅鹅', '煮豆燃豆萁',
        '床前明月光', '春眠不觉晓', '白日依山尽', '红豆生南国',
        '千山鸟飞绝', '离离原上草', '远看山有色', '草长莺飞二月天',
        '牧童骑黄牛', '敕勒川阴山下', '蓬头稚子学垂纶', '好雨知时节',
        '咬定青山不放松', '浩荡离愁白日斜', '千锤万凿出深山',
        '驿外断桥边', '茅檐低小溪上', '孤村落日残霞', '明月别枝惊鹊',
        '山一程水一程', '纳兰性德', '昔我往矣杨柳依依',
      ];
      for (const line of knownLines) {
        if (text.includes(line)) {
          score += 400;
          poemMatched.add(key);
          break;
        }
      }
    }

    // 诗人分层
    if (TIER_S_POETS.has(authorName)) score += 200;
    else if (TIER_A_POETS.has(authorName)) score += 150;
    else if (TIER_B_POETS.has(authorName)) score += 100;
    else if (TIER_C_POETS.has(authorName)) score += 70;
    else if (authorName.includes('佚名') || authorName.includes('无名')) score += 0;
    else if (authorName.includes('皇帝') || authorName.includes('宗室')) score += 15;
    else if (authorName.startsWith('释')) score += 25;
    else if (authorName.startsWith('道')) score += 20;
    else score += 40;

    const coupletCount = poemCoupletCount[key] || 1;
    score += Math.min(50, Math.log2(coupletCount + 1) * 12);
    if (titleName.length <= 3) score += 15;
    else if (titleName.length <= 5) score += 10;
    else if (titleName.length <= 8) score += 5;
    if (titleName.length > 20) score -= 15;

    score = Math.min(999, Math.max(1, Math.round(score)));
    poemHeat.set(key, score);
  }
}

console.log('Scored', poemHeat.size, 'unique poems');
console.log('Total matched:', poemMatched.size);

// ========== 6. 构建 lite 数据 ==========

const scoredCouplets = couplets.map(c => {
  const key = c[2] + ':' + c[3];
  return [c[0], c[1], c[2], c[3], poemHeat.get(key)];
});

scoredCouplets.sort((a, b) => b[4] - a[4]);

const seen = new Set();
const unique = [];
const uniquePoemKeys = new Set();
for (const c of scoredCouplets) {
  const key = c[0] + '|' + c[1];
  const poemKey = c[2] + ':' + c[3];
  if (!seen.has(key)) {
    seen.add(key);
    unique.push(c);
    uniquePoemKeys.add(poemKey);
  }
}

// 确保所有匹配的教科书诗词都在
const requiredKeys = [...poemMatched].filter(k => !uniquePoemKeys.has(k));
console.log('Required poems not in top-50k:', requiredKeys.length);
for (const key of requiredKeys) {
  const [tIdx, aIdx] = key.split(':').map(Number);
  for (const c of scoredCouplets) {
    if (c[2] === tIdx && c[3] === aIdx) {
      const key2 = c[0] + '|' + c[1];
      if (!seen.has(key2)) {
        seen.add(key2);
        unique.push(c);
      }
    }
  }
}

const lite = unique.slice(0, 50000);

// Remap
const usedTitles = new Set();
const usedAuthors = new Set();
for (const c of lite) {
  usedTitles.add(c[2]);
  usedAuthors.add(c[3]);
}
const liteTitlesArr = [...usedTitles].sort((a, b) => a - b);
const liteAuthorsArr = [...usedAuthors].sort((a, b) => a - b);
const titleRemap = {};
liteTitlesArr.forEach((old, i) => titleRemap[old] = i);
const authorRemap = {};
liteAuthorsArr.forEach((old, i) => authorRemap[old] = i);

const liteData = {
  titles: liteTitlesArr.map(i => titles[i]),
  authors: liteAuthorsArr.map(i => authors[i]),
  couplets: lite.map(c => [c[0], c[1], titleRemap[c[2]], authorRemap[c[3]], c[4]])
};

fs.writeFileSync(OUTPUT_LITE, JSON.stringify(liteData), 'utf8');

console.log('\nLite:', liteData.couplets.length, 'couplets,', liteData.titles.length, 'titles,', liteData.authors.length, 'authors');
console.log('Lite size:', (fs.statSync(OUTPUT_LITE).size / 1024 / 1024).toFixed(1), 'MB');

// Verify
console.log('\nVerifying textbook poems:');
const checks = [
  ['云母屏风', '李商隐'],
  ['西塞山前', '张志和'],
  ['天街小雨', '韩愈'],
  ['更深月色', '刘方平'],
  ['谁知盘中', '李绅'],
  ['花间一壶', '李白'],
  ['春眠不觉', '孟浩然'],
];
for (const [s, a] of checks) {
  let found = false;
  for (const c of liteData.couplets) {
    if (liteData.authors[c[3]] === a && (c[0].includes(s) || c[1].includes(s))) {
      console.log('  ✓', s, a, 'heat:', c[4], ':', c[0], c[1]);
      found = true;
      break;
    }
  }
  if (!found) console.log('  ✗', s, a, 'NOT FOUND');
}
