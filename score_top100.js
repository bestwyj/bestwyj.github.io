const fs = require('fs');

// 读取200个常用字
const charText = fs.readFileSync('e:/CDisk/Downloads/字.txt', 'utf-8');
const commonChars = new Set(charText.split('\n').map(l => l.trim()).filter(Boolean));

console.log('常用字数量:', commonChars.size);

// 读取诗词数据
const data = JSON.parse(fs.readFileSync('D:/bestwyj.github.io/poetry-data-lite.json', 'utf-8'));
const { titles, authors, couplets } = data;

const fiveResults = [];
const sevenResults = [];

for (let i = 0; i < couplets.length; i++) {
    const c = couplets[i];
    const combined = c[0] + c[1];
    const len = combined.length;

    if (len !== 10 && len !== 14) continue;
    const isFive = len === 10;

    // 计算常用字数量作为分数
    let score = 0;
    for (const ch of combined) {
        if (commonChars.has(ch)) score++;
    }

    const entry = {
        upper: c[0],
        lower: c[1],
        title: titles[c[2]],
        author: authors[c[3]],
        heat: c[4],
        score,
        coupletIdx: i
    };

    (isFive ? fiveResults : sevenResults).push(entry);
}

// 按分数降序，分数相同按热度降序
fiveResults.sort((a, b) => b.score - a.score || b.heat - a.heat);
sevenResults.sort((a, b) => b.score - a.score || b.heat - a.heat);

const top100Five = fiveResults.slice(0, 100);
const top100Seven = sevenResults.slice(0, 100);

console.log('五言总数:', fiveResults.length, ', top100 最高分:', top100Five[0]?.score, ', 最低分:', top100Five[top100Five.length-1]?.score);
console.log('七言总数:', sevenResults.length, ', top100 最高分:', top100Seven[0]?.score, ', 最低分:', top100Seven[top100Seven.length-1]?.score);

// 保存
const output = {
    common_chars: [...commonChars].sort(),
    top100_five: top100Five,
    top100_seven: top100Seven
};

fs.writeFileSync('D:/bestwyj.github.io/top100-popular.json', JSON.stringify(output, null, 2), 'utf-8');
console.log('已保存到 top100-popular.json');
