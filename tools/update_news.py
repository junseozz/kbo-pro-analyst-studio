#!/usr/bin/env python3
import json, urllib.request, urllib.parse, xml.etree.ElementTree as ET, email.utils, datetime, hashlib, re, os, html as html_mod

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ex_path = os.path.join(repo, 'data/extra.json')
ex_js_path = os.path.join(repo, 'data/extra.js')
mf_path = os.path.join(repo, 'data/manifest.json')
lp_path = os.path.join(repo, 'data/live_patch.json')
lp_js_path = os.path.join(repo, 'data/live_patch.js')

ex = json.load(open(ex_path, encoding='utf-8'))
ns = ex['V164_NEWS_SNAPSHOT']

kst = datetime.timezone(datetime.timedelta(hours=9))
now = datetime.datetime.now(kst)
now_iso = now.isoformat(timespec='seconds')

def merge_items(new_list, old_list, limit=60):
    merged, seen = [], set()
    for item in sorted((new_list or []) + (old_list or []), key=lambda x: x.get('ts', 0), reverse=True):
        t = re.sub(r'\s+', ' ', item.get('title', '')).strip()
        if not t or t in seen:
            continue
        seen.add(t)
        merged.append(item)
    return merged[:limit]

def fetch_gnews(q):
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(q) + '&hl=ko&gl=KR&ceid=KR:ko'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        xml_data = r.read()
    root = ET.fromstring(xml_data)
    out = []
    for item in root.findall('./channel/item')[:40]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        src_el = item.find('source')
        src = (src_el.text or '').strip() if src_el is not None and src_el.text else ''
        if not src and ' - ' in title:
            parts = title.rsplit(' - ', 1)
            title, src = parts[0].strip(), parts[1].strip()
        elif src and title.endswith(' - ' + src):
            title = title[:-len(' - ' + src)].strip()
        try:
            dt = email.utils.parsedate_to_datetime(pub).astimezone(kst)
        except Exception:
            continue
        if (now - dt).days > 7:
            continue
        out.append({
            'title': title,
            'link': link,
            'route': 'gnews',
            'src': src or '구글뉴스',
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H:%M'),
            'ts': int(dt.strftime('%Y%m%d%H%M')),
            'summary': '',
            'q': q.replace(' when:1d', '')
        })
    return out

def fetch_yna():
    url = 'https://www.yna.co.kr/rss/sports.xml'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        xml_data = r.read()
    root = ET.fromstring(xml_data)
    kw = ('야구', 'KBO', '프로야구', '두산', 'LG', '삼성', 'KIA', 'SSG', '한화', '롯데', 'NC', 'KT', '키움', '상무', '퓨처스', '윈터리그', '메이저리그', 'MLB', '포스팅', '골든글러브', 'FA ')
    exclude_kw = ('축구', 'FIFA', 'K리그', '농구', 'KBL', '배구', 'V리그', '골프', 'LPGA', 'KPGA', '테니스', '바둑')
    out = []
    for item in root.findall('./channel/item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        desc = (item.findtext('description') or '').strip()
        text = title + ' ' + desc
        if any(ek in text for ek in exclude_kw):
            continue
        if not (any(k in text for k in kw) or re.search(r'(?<![A-Z])FA(?![A-Z])', text)):
            continue
        try:
            dt = email.utils.parsedate_to_datetime(pub).astimezone(kst)
        except Exception:
            continue
        if (now - dt).days > 14:
            continue
        out.append({
            'title': title,
            'link': link,
            'route': 'yna',
            'src': '연합뉴스',
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H:%M'),
            'ts': int(dt.strftime('%Y%m%d%H%M')),
            'summary': ''
        })
    return out

def fetch_kbo():
    url = 'https://www.koreabaseball.com/MediaNews/Notice/List.aspx'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        page = r.read().decode('utf-8', 'ignore')
    out = []
    for m in re.finditer(r'<tr[^>]*>(.*?)</tr>', page, re.S):
        row = m.group(1)
        a = re.search(r'<a[^>]+href="([^"]*View\.aspx[^"]*)"[^>]*>(.*?)</a>', row, re.S)
        dm = re.search(r'(20\d{2})\.(\d{2})\.(\d{2})', row)
        if not (a and dm):
            continue
        href = html_mod.unescape(a.group(1)).strip()
        if href.startswith('/'):
            href = 'https://www.koreabaseball.com' + href
        title = re.sub(r'\s+', ' ', html_mod.unescape(re.sub(r'<[^>]+>', '', a.group(2)))).strip()
        if not title:
            continue
        dt_str = f'{dm.group(1)}-{dm.group(2)}-{dm.group(3)}'
        out.append({
            'title': title,
            'link': href,
            'route': 'kbo',
            'src': 'KBO 보도자료',
            'date': dt_str,
            'time': '',
            'ts': int(f'{dm.group(1)}{dm.group(2)}{dm.group(3)}0000'),
            'summary': ''
        })
    return out

def fetch_naver():
    out, seen_href = [], set()
    for q in ['KBO 프로야구', '프로야구 FA 외국인']:
        url = 'https://m.search.naver.com/search.naver?where=m_news&query=' + urllib.parse.quote(q) + '&sort=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36'})
        with urllib.request.urlopen(req, timeout=15) as r:
            page = r.read().decode('utf-8', 'ignore')
        for m in re.finditer(r'<a[^>]+href="(https?://m\.sports\.naver\.com/kbaseball/article/[^"]+)"[^>]*>(.*?)</a>', page, re.S):
            href = html_mod.unescape(m.group(1)).split('?')[0]
            if href in seen_href:
                continue
            title = re.sub(r'\s+', ' ', html_mod.unescape(re.sub(r'<[^>]+>', '', m.group(2)))).strip()
            if len(title) < 10 or '네이버뉴스' in title:
                continue
            seen_href.add(href)
            ctx = re.sub(r'<[^>]+>', ' ', page[max(0, m.start() - 600):min(len(page), m.start() + 300)])
            dt = now
            tm = re.search(r'(\d+)\s*분\s*전', ctx)
            th = re.search(r'(\d+)\s*시간\s*전', ctx)
            td = re.search(r'(20\d{2})\.(\d{2})\.(\d{2})\.', ctx)
            if tm:
                dt = now - datetime.timedelta(minutes=int(tm.group(1)))
            elif th:
                dt = now - datetime.timedelta(hours=int(th.group(1)))
            elif td:
                dt = datetime.datetime(int(td.group(1)), int(td.group(2)), int(td.group(3)), 9, 0, tzinfo=kst)
            out.append({
                'title': title,
                'link': href,
                'route': 'naver',
                'src': '네이버 스포츠',
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M'),
                'ts': int(dt.strftime('%Y%m%d%H%M')),
                'summary': ''
            })
    return out

new_kbo_gnews, new_awb, new_yna, new_kbo_off, new_naver = [], [], [], [], []
try:
    new_kbo_gnews = fetch_gnews('KBO when:1d') + fetch_gnews('프로야구 when:1d') + fetch_gnews('KBO FA 트레이드 when:1d')
except Exception as e:
    print('gnews err:', e)
try:
    new_awb = fetch_gnews('아시아 윈터 베이스볼 when:1d') + fetch_gnews('KBO 연합팀 when:1d')
except Exception as e:
    print('intl err:', e)
try:
    new_yna = fetch_yna()
except Exception as e:
    print('yna err:', e)
try:
    new_kbo_off = fetch_kbo()
except Exception as e:
    print('kbo err:', e)
try:
    new_naver = fetch_naver()
except Exception as e:
    print('naver err:', e)

ns['gnews'] = merge_items(new_kbo_gnews, ns.get('gnews'), 60)
ns['intl'] = merge_items(new_awb, ns.get('intl'), 60)
ns['yna'] = merge_items(new_yna, ns.get('yna'), 40)
ns['kbo'] = merge_items(new_kbo_off, ns.get('kbo'), 40)
ns['naver'] = merge_items(new_naver, ns.get('naver'), 60)

ns['built'] = now.strftime('%Y-%m-%d %H:%M:%S')
ex['V164_NEWS_SNAPSHOT'] = ns

ex_bytes = json.dumps(ex, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
with open(ex_path, 'wb') as f:
    f.write(ex_bytes)

ex_js_bytes = b'window.V211_RECEIVE&&window.V211_RECEIVE(' + ex_bytes + b');\n'
with open(ex_js_path, 'wb') as f:
    f.write(ex_js_bytes)

news_obj = {
    'built': ns['built'],
    'yna': ns.get('yna') or [],
    'naver': ns.get('naver') or [],
    'kbo': ns.get('kbo') or [],
    'gnews': ns.get('gnews') or [],
    'intl': ns.get('intl') or [],
}
news_bytes = json.dumps(news_obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
with open(os.path.join(repo, 'data/news.json'), 'wb') as f:
    f.write(news_bytes)
with open(os.path.join(repo, 'data/news.js'), 'wb') as f:
    f.write(b'/* KBO Pro Analyst Studio - news snapshot (v22.0) */\n')
    f.write(b'window.V220_NEWS&&window.V220_NEWS(' + news_bytes + b');\n')

sha = hashlib.sha256(ex_bytes).hexdigest()
mf = json.load(open(mf_path, encoding='utf-8'))
mf['updated_at'] = now_iso
mf['checked_at'] = now_iso
for ch in mf.get('chunks', []):
    if ch.get('id') == 'extra' or ch.get('name') == 'extra':
        ch['bytes'] = len(ex_bytes)
        ch['sha256'] = sha
        ch['updated_at'] = now_iso
        ch['js_bytes'] = len(ex_js_bytes)
mf['total_bytes'] = sum(int(c.get('bytes') or 0) for c in mf.get('chunks', []))
with open(mf_path, 'w', encoding='utf-8') as f:
    json.dump(mf, f, ensure_ascii=False, indent=1)
    f.write('\n')
with open(os.path.join(repo, 'data/manifest.js'), 'w', encoding='utf-8') as f:
    f.write('window.V211_RECEIVE&&window.V211_RECEIVE('
            + json.dumps(mf, ensure_ascii=False, separators=(',', ':')) + ');')

lp = json.load(open(lp_path, encoding='utf-8'))
lp['checked_at'] = now_iso
lp['updated_at'] = now_iso
with open(lp_path, 'w', encoding='utf-8') as f:
    json.dump(lp, f, ensure_ascii=False, indent=1)
    f.write('\n')
lp_min = json.dumps(lp, ensure_ascii=False, separators=(',', ':'))
with open(lp_js_path, 'w', encoding='utf-8') as f:
    f.write('/* KBO Pro Analyst Studio — v21.0 live patch (JSONP 대체 로더용 래퍼) */\n')
    f.write(f'window.V210_RECEIVE && window.V210_RECEIVE({lp_min});\n')

try:
    import sync_kbo_server
    sync_kbo_server.check_kbo_official_status()
except Exception as e:
    print('sync_kbo_server warn:', e)

print('Updated V164_NEWS_SNAPSHOT.built:', ns['built'])
print('counts:', {k: len(ns.get(k) or []) for k in ['yna', 'naver', 'kbo', 'gnews', 'intl']})
print('yna top2:', [(x['date'], x['time'], x['title'][:30]) for x in ns['yna'][:2]])
print('naver top2:', [(x['date'], x['time'], x['title'][:30]) for x in ns['naver'][:2]])
print('kbo top2:', [(x['date'], x['title'][:30]) for x in ns['kbo'][:2]])
print('gnews top2:', [(x['date'], x['time'], x['title'][:30]) for x in ns['gnews'][:2]])
print('news.json bytes:', len(news_bytes))
print('extra sha256:', sha, 'bytes:', len(ex_bytes))
