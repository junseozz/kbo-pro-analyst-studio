# -*- coding: utf-8 -*-
"""manifest.json 무결성 검사·동기화 — 앱이 청크를 받아갈 수 있는 상태인지 확인한다.

앱(v21.1+)은 manifest 의 sha256 과 IndexedDB 저장본 sha 를 비교해 **바뀐 청크만** 받는다.
그래서 manifest 의 sha256·bytes 가 실제 파일과 다르면, 파일을 아무리 새로 올려도
앱은 "변동 없음"으로 판단해 영영 받지 않는다(2026-11-21 뉴스 미갱신 사고의 원인).

사용:
    python3 tools/verify_manifest.py            # 검사만 (불일치가 있으면 exit 1)
    python3 tools/verify_manifest.py --fix      # 실제 파일 기준으로 manifest.json·manifest.js 재작성
"""
import json, hashlib, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
KST = datetime.timezone(datetime.timedelta(hours=9))
IDS = ['core', 'extra', 'zone_pitch', 'season', 'kbo1_games', 'futures_games']


def wrap_jsonp(text):
    return 'window.V211_RECEIVE&&window.V211_RECEIVE(' + text + ');'


def main():
    fix = '--fix' in sys.argv
    mp = os.path.join(DATA, 'manifest.json')
    man = json.load(open(mp, encoding='utf-8'))
    by_id = {c.get('id'): c for c in man.get('chunks', [])}
    now_iso = datetime.datetime.now(KST).isoformat(timespec='seconds')
    bad = []
    for cid in IDS:
        jp = os.path.join(DATA, cid + '.json')
        sp = os.path.join(DATA, cid + '.js')
        if not os.path.exists(jp):
            bad.append((cid, 'json 없음'))
            continue
        body = open(jp, 'rb').read()
        sha = hashlib.sha256(body).hexdigest()
        ch = by_id.get(cid)
        if ch is None:
            bad.append((cid, 'manifest 에 없음'))
            continue
        if ch.get('sha256') != sha or int(ch.get('bytes') or 0) != len(body):
            bad.append((cid, 'sha/bytes 불일치 manifest=%s/%s real=%s/%s'
                        % (str(ch.get('sha256'))[:10], ch.get('bytes'), sha[:10], len(body))))
            if fix:
                ch['sha256'] = sha
                ch['bytes'] = len(body)
                ch['updated_at'] = now_iso
        # .js 래퍼가 같은 바이트를 감싸고 있는지
        js = open(sp, 'rb').read() if os.path.exists(sp) else b''
        if body not in js:
            bad.append((cid, '.js 래퍼 내용 불일치'))
            if fix:
                open(sp, 'wb').write((wrap_jsonp(body.decode('utf-8')) + '\n').encode('utf-8'))
    # live_patch.json / .js — 래퍼는 압축 JSON 이라 문자열 비교가 아니라 내용(파싱값)으로 본다
    lp = os.path.join(DATA, 'live_patch.json')
    if os.path.exists(lp):
        lpobj = json.load(open(lp, encoding='utf-8'))
        lpjs = os.path.join(DATA, 'live_patch.js')
        js_obj = None
        if os.path.exists(lpjs):
            js_txt = open(lpjs, encoding='utf-8').read()
            k = js_txt.rfind('V210_RECEIVE(')
            a, b = js_txt.find('(', k), js_txt.rfind(')')
            try:
                js_obj = json.loads(js_txt[a + 1:b])
            except Exception:
                js_obj = None
        if js_obj != lpobj:
            bad.append(('live_patch', '.js 래퍼 내용 불일치'))
            if fix:
                open(lpjs, 'w', encoding='utf-8').write(
                    '/* KBO Pro Analyst Studio — v21.0 live patch (JSONP 대체 로더용 래퍼) */\n'
                    + 'window.V210_RECEIVE && window.V210_RECEIVE('
                    + json.dumps(lpobj, ensure_ascii=False, separators=(',', ':')) + ');\n')
    if fix:
        man['total_bytes'] = sum(int(c.get('bytes') or 0) for c in man.get('chunks', []))
        with open(mp, 'w', encoding='utf-8') as f:
            json.dump(man, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(os.path.join(DATA, 'manifest.js'), 'w', encoding='utf-8') as f:
            f.write(wrap_jsonp(json.dumps(man, ensure_ascii=False, separators=(',', ':'))))
    for cid, why in bad:
        print('MISMATCH', cid, why)
    print('chunks checked:', len(IDS), '| problems:', len(bad), '| fixed' if fix and bad else '')
    return 0 if (not bad or fix) else 1


if __name__ == '__main__':
    sys.exit(main())
