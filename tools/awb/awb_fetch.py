"""AWB(아시아 윈터 베이스볼 리그) 공식 사이트 수집 — 서버측 스크래퍼.
공식: https://awb.cpbl.com.tw (CPBL 주관)
- 일정: POST /schedule/getgamedatas  (RequestVerificationToken 헤더 필요)
- 경기 상세/라이브: POST /box/getlive  (폼 __RequestVerificationToken + 세션 쿠키)
"""
import json, re, sys, os, time
import requests

BASE = 'https://awb.cpbl.com.tw'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36'


def session():
    s = requests.Session()
    s.headers.update({'User-Agent': UA, 'Accept-Language': 'zh-TW,zh;q=0.9'})
    return s


def get_tokens(s, path):
    r = s.get(BASE + path, timeout=30)
    r.raise_for_status()
    toks = re.findall(r"RequestVerificationToken:\s*'([^']+)'", r.text)
    form = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', r.text)
    yr = re.search(r'YearList\s*:\s*\[([^\]]*)\]', r.text)
    years = re.findall(r'"(\d{4})"', yr.group(1)) if yr else []
    return r.text, toks, (form.group(1) if form else None), years


def schedule(s):
    html, toks, form, years = get_tokens(s, '/schedule')
    year = years[0] if years else '2026'
    tok = toks[1] if len(toks) > 1 else (form or '')
    r = s.post(BASE + '/schedule/getgamedatas',
               data={'calendar': year + '/01/01', 'location': '', 'kindCode': 'P'},
               headers={'RequestVerificationToken': tok, 'X-Requested-With': 'XMLHttpRequest',
                        'Referer': BASE + '/schedule'}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not j.get('Success'):
        raise RuntimeError('schedule failed')
    return year, j['GameDatas']


def box(s, year, sno):
    html, toks, form, years = get_tokens(s, '/box?year=%s&kindCode=P&gameSno=%s' % (year, sno))
    if not form:
        raise RuntimeError('no form token for %s' % sno)
    r = s.post(BASE + '/box/getlive',
               data={'__RequestVerificationToken': form, 'GameSno': str(sno), 'KindCode': 'P',
                     'Year': str(year), 'PrevOrNext': '', 'PresentStatus': '',
                     'SelectKindCode': 'P', 'SelectYear': '', 'SelectMonth': '', 'SelectGameSno': ''},
               headers={'X-Requested-With': 'XMLHttpRequest',
                        'Referer': BASE + '/box?year=%s&kindCode=P&gameSno=%s' % (year, sno)},
               timeout=40)
    r.raise_for_status()
    return r.json()


def roster(s, team, en=False):
    path = ('/en/team?TeamNo=' if en else '/team?TeamNo=') + team
    r = s.get(BASE + path, timeout=30)
    r.raise_for_status()
    out = []
    for b in re.findall(r'<div class="item">(.*?)(?=<div class="item">|<div class="cat_title">|$)', r.text, flags=re.S):
        a = re.search(r'/team/person\?Acnt=(\d+)', b)
        n = re.search(r'<div class="name">(?:<a[^>]*>)?([^<]+)', b)
        num = re.search(r'<div class="number">([^<]*)</div>', b)
        pos = re.search(r'<div class="pos">([^<]+)</div>', b)
        img = re.search(r"url\('([^']+)'\)", b)
        if a and n:
            out.append({'acnt': a.group(1), 'name': n.group(1).strip(),
                        'no': (num.group(1).strip() if num else ''),
                        'pos': (pos.group(1).strip() if pos else ''),
                        'img': (img.group(1) if img else '')})
    return out


if __name__ == '__main__':
    os.makedirs('raw', exist_ok=True)
    s = session()
    year, games = schedule(s)
    json.dump({'year': year, 'games': games}, open('raw/schedule.json', 'w'), ensure_ascii=False)
    print('schedule', year, len(games))
    for g in games:
        sno = g['GameSno']
        p = 'raw/game_%02d.json' % sno
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        try:
            d = box(s, year, sno)
            json.dump(d, open(p, 'w'), ensure_ascii=False)
            print('game', sno, len(d.get('LiveLogJson') or ''), len(d.get('BattingJson') or ''))
        except Exception as e:
            print('game', sno, 'ERR', e)
        time.sleep(0.4)
    for t in ['ZZZ041', 'ZZZ040', 'ZZZ083', 'ZZZ389', 'ZZZ409', 'ZZZ388']:
        for en in (False, True):
            try:
                d = roster(s, t, en)
                json.dump(d, open('raw/roster_%s_%s.json' % (t, 'en' if en else 'zh'), 'w'), ensure_ascii=False)
                print('roster', t, 'en' if en else 'zh', len(d))
            except Exception as e:
                print('roster', t, en, 'ERR', e)
