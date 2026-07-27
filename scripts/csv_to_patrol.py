#!/usr/bin/env python3
# jonghap_new.csv -> patrol_data.js
# 기간: 연 누적 + [월 누적 드롭다운] + 월별(당월) 버튼. 열 위치 자동 탐지.
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
hr = -1; gc = 0
for i, r in enumerate(rows):
    for c in range(len(r)-2):
        if r[c].strip() == '구분' and r[c+2].strip() == '점검구분':
            hr = i; gc = c; break
    if hr >= 0: break
if hr < 1: sys.exit('CSV 헤더(구분/점검구분)를 찾지 못했습니다')
catcol = gc + 2
per, sub = rows[hr-1], rows[hr]
fugul = [(c, per[c].strip() if c < len(per) else '') for c in range(len(sub)) if sub[c].strip() == '발굴']
# 숫자 연속 런(1,2,3,...) 추출
runs = []; i = 0
while i < len(fugul):
    if fugul[i][1] == '1':
        exp = 1; run = []; j = i
        while j < len(fugul) and fugul[j][1] == str(exp):
            run.append(fugul[j]); exp += 1; j += 1
        runs.append(run); i = j
    else:
        i += 1
monthly_runs = [r for r in runs if len(r) >= 8]   # 12개월 런 (당월, 누적)
pcol = {}; ann = None; month_labels = []; cum_labels = []
for c, lab in fugul:
    if lab.endswith('년 누적'): ann = lab; pcol[lab] = (c, c+1); break
if len(monthly_runs) >= 1:  # 당월
    for k, (c, lab) in enumerate(monthly_runs[0]):
        L = str(k+1) + '월'; pcol[L] = (c, c+1); month_labels.append(L)
if len(monthly_runs) >= 2:  # 누적
    for k, (c, lab) in enumerate(monthly_runs[1]):
        L = str(k+1) + '월 누적'; pcol[L] = (c, c+1); cum_labels.append(L)
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
# 당월 계=0 제거
for fac in list(d.keys()):
    for L in month_labels:
        t = d[fac].get(L, {}).get('계')
        if not t or (t[0] == 0 and t[1] == 0): d[fac].pop(L, None)
# 마지막 활동 월
def midx(L): return int(L.replace('월 누적','').replace('월',''))
active = [midx(L) for L in month_labels if any(L in d[f] for f in d)]
lastM = max(active) if active else 0
# 월 누적: 마지막 활동 월까지만 유지, 그 이후 제거
keep_cum = []
for L in cum_labels:
    if midx(L) <= lastM: keep_cum.append(L)
    else:
        for fac in d: d[fac].pop(L, None)
# 순서 정리
months_order = [L for L in month_labels if any(L in d[f] for f in d)]
periods = ([ann] if ann else []) + months_order      # 버튼(연 누적 + 당월)
cumPeriods = keep_cum                                  # 드롭다운(월 누적)
kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
obj = {"stamp": kst.strftime('%Y-%m-%d') + ' 기준', "periods": periods, "cumPeriods": cumPeriods, "d": d}
open(OUT, 'w', encoding='utf-8').write('window.PATROL_DATA = ' + json.dumps(obj, ensure_ascii=False, separators=(',',':')) + ';')
print('버튼:', periods)
print('드롭다운:', cumPeriods)
print('CTR 당월 계:', {p:d['CTR Mobility'][p]['계'] for p in months_order})
print('CTR 누적 계:', {p:d['CTR Mobility'][p]['계'] for p in cumPeriods})
