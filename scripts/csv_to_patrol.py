#!/usr/bin/env python3
# jonghap_new.csv -> patrol_data.js (열 위치/기간 라벨에 강건)
import json, sys, glob, os, datetime
def find_csv():
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]): return sys.argv[1]
    c = glob.glob('/sessions/*/mnt/**/jonghap_new.csv', recursive=True)
    c.sort(key=lambda p: (0 if 'EHS' in p else 1, p))
    return c[0] if c else None
CSV = find_csv()
if not CSV: sys.exit('jonghap_new.csv 를 찾지 못했습니다')
OUT = sys.argv[2] if len(sys.argv) > 2 else 'patrol_data.js'
rows = []
with open(CSV, encoding='utf-8-sig') as f:
    for line in f: rows.append(line.rstrip('\r\n').split(','))
# 헤더행과 '구분' 열 위치(gc) 자동 탐지
hr = -1; gc = 0
for i, r in enumerate(rows):
    for c in range(len(r)-2):
        if r[c].strip() == '구분' and r[c+2].strip() == '점검구분':
            hr = i; gc = c; break
    if hr >= 0: break
if hr < 1: sys.exit('CSV 헤더(구분/점검구분)를 찾지 못했습니다')
catcol = gc + 2
per, sub = rows[hr-1], rows[hr]
# 표시할 기간(있는 것만 채택) — 신/구 라벨 모두 허용
want = ['2026년 누적','7월 누적','6월 누적','5월 누적','1분기','2분기','3분기','4분기']
pcol = {}
for c in range(len(sub)):
    if sub[c].strip() == '발굴':
        lab = per[c].strip() if c < len(per) else ''
        if lab in want and lab not in pcol: pcol[lab] = (c, c+1)
def catOf(s):
    s = s.strip()
    if s in ('총계','소계'): return '계'
    if s.startswith('01'): return '일반'
    if s.startswith('02'): return '위험성평가'
    if s.startswith('03'): return '테마별순회점검'
    if s.startswith('04'): return '정기순회점검'
    return None
def toNum(v):
    v = ''.join(ch for ch in v if ch.isdigit() or ch == '-')
    return None if v in ('','-') else int(v)
facs = ['CTR Mobility','10-울산','30-서산','40-대구']
d = {}; cur = None
for i in range(hr+1, len(rows)):
    r = rows[i]
    if len(r) > gc and r[gc].strip() == 'END': break
    fa = r[gc].strip() if len(r) > gc else ''
    fb = r[gc+1].strip() if len(r) > gc+1 else ''
    if fa in facs: cur = fa
    elif fb in facs: cur = fb
    if not cur: continue
    cat = catOf(r[catcol]) if len(r) > catcol else None
    if not cat: continue
    d.setdefault(cur, {})
    for p,(fc,dc) in pcol.items():
        f  = toNum(r[fc]) if fc < len(r) else None
        dn = toNum(r[dc]) if dc < len(r) else None
        if f is None and dn is None: continue
        d[cur].setdefault(p, {})
        d[cur][p][cat] = [f or 0, dn or 0]
for fac in list(d.keys()):
    for p in list(d[fac].keys()):
        t = d[fac][p].get('계')
        if not t or (t[0] == 0 and t[1] == 0): del d[fac][p]
# 채택된 기간 순서(want 순서 유지, 실제 데이터 있는 것만)
order = [p for p in want if any(p in d[f] for f in d)]
kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
obj = {"stamp": kst.strftime('%Y-%m-%d') + ' 기준', "periods": order, "d": d}
open(OUT, 'w', encoding='utf-8').write('window.PATROL_DATA = ' + json.dumps(obj, ensure_ascii=False, separators=(',',':')) + ';')
print('OK gc=%d catcol=%d periods=%s' % (gc, catcol, order))
print('CTR Mobility:', d.get('CTR Mobility'))
