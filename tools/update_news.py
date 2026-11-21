#!/usr/bin/env python3
import json, urllib.request, urllib.parse, xml.etree.ElementTree as ET, email.utils, datetime, hashlib, re, os

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

def fetch_gnews(q):
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(q) + '&hl=ko&gl=KR&ceid=KR:ko'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        xml_data = r.read()
    root = ET.fromstring(xml_data)
    out = []
    for item in root.findall('./channel/item')[:35]:
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
            'q': q
        })
    return out

new_kbo = fetch_gnews('KBO 프로야구')
new_fa = fetch_gnews('KBO FA 트레이드')
new_awb = fetch_gnews('아시아 윈터 베이스볼 KBO')

merged_gnews, seen = [], set()
for item in sorted(new_kbo + new_fa + (ns.get('gnews') or []), key=lambda x: x.get('ts', 0), reverse=True):
    t = re.sub(r'\s+', ' ', item.get('title', '')).strip()
    if not t or t in seen:
        continue
    seen.add(t)
    merged_gnews.append(item)
ns['gnews'] = merged_gnews[:60]

merged_intl, seen_i = [], set()
for item in sorted(new_awb + (ns.get('intl') or []), key=lambda x: x.get('ts', 0), reverse=True):
    t = re.sub(r'\s+', ' ', item.get('title', '')).strip()
    if not t or t in seen_i:
        continue
    seen_i.add(t)
    merged_intl.append(item)
ns['intl'] = merged_intl[:60]

ns['built'] = now.strftime('%Y-%m-%d %H:%M:%S')
ex['V164_NEWS_SNAPSHOT'] = ns

ex_bytes = json.dumps(ex, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
with open(ex_path, 'wb') as f:
    f.write(ex_bytes)

ex_js_bytes = b'window.V211_RECEIVE&&window.V211_RECEIVE(' + ex_bytes + b');\n'
with open(ex_js_path, 'wb') as f:
    f.write(ex_js_bytes)

sha = hashlib.sha256(ex_bytes).hexdigest()
mf = json.load(open(mf_path, encoding='utf-8'))
mf['updated_at'] = now_iso
mf['checked_at'] = now_iso
for ch in mf.get('chunks', []):
    if ch.get('name') == 'extra':
        ch['bytes'] = len(ex_bytes)
        ch['sha256'] = sha
        ch['js_bytes'] = len(ex_js_bytes)
with open(mf_path, 'w', encoding='utf-8') as f:
    json.dump(mf, f, ensure_ascii=False, indent=1)
    f.write('\n')

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

print('Updated V164_NEWS_SNAPSHOT.built:', ns['built'])
print('gnews top 3:', [(x['date'], x['time'], x['title'][:35]) for x in ns['gnews'][:3]])
print('extra sha256:', sha, 'bytes:', len(ex_bytes))
