import re, shutil, io, os, sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
s = open(P, encoding='utf-8').read()
orig = s

CARD = re.compile(r'<div class="qcard.*?(?=<div class="qcard |<h3|<h2 class="anchor"|</section>)', re.S)

def scan(s):
    out = []
    for m in CARD.finditer(s):
        c = m.group(0)
        qid = re.search(r'id="(q\d+)"', c)
        label = re.search(r'data-label="([^"]+)"', c)
        if '<div class="ver zh">' not in c:
            continue
        head = c.split('<div class="ver ')[0]
        zhseg = c.split('<div class="ver zh">')[1].split('<details')[0]
        if '<pre' in head:
            continue
        if '<pre' in zhseg:
            out.append((m.start(), m.end(), qid.group(1) if qid else '?',
                        label.group(1) if label else '?', head, zhseg))
    return out

targets = scan(s)
print('英文视图缺代码的题卡：', len(targets))
for t in targets:
    print('  ', t[2], t[3])

if '--apply' not in sys.argv:
    print('\n[dry-run] 未写入。加 --apply 执行。')
    raise SystemExit(0)

# 备份
bak = P + '.bak-fixctx-' + __import__('time').strftime('%Y%m%d-%H%M%S')
shutil.copyfile(P, bak)
print('备份 ->', bak)

# 从后往前改，避免偏移
for start, end, qid, label, head, zhseg in reversed(targets):
    card = s[start:end]
    pres = re.findall(r'<pre>.*?</pre>', zhseg, re.S)
    if not pres:
        continue
    # 1) 从 zh 区移除 pre
    new_zh = zhseg
    for p in pres:
        new_zh = new_zh.replace(p, '', 1)
    new_zh = re.sub(r'\s+</p>', '</p>', new_zh)
    new_card = card.replace(zhseg, new_zh, 1)
    # 2) 插到 qbody 之后（语言无关区）
    idx = new_card.rindex('<div class="qbody">') + len('<div class="qbody">')
    insert = '\n    ' + '\n    '.join(pres)
    new_card = new_card[:idx] + insert + new_card[idx:]
    s = s[:start] + new_card + s[end:]

open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('写入完成，剩余问题卡：', len(scan(s)))
