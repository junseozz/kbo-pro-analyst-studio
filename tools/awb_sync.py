# -*- coding: utf-8 -*-
"""AWB(아시아 윈터 베이스볼 리그) 실시간 동기화 — GitHub Actions 에서 실행.

· 공식 사이트(awb.cpbl.com.tw)는 브라우저에서 CORS 로 직접 호출할 수 없다
  (POST + RequestVerificationToken + 세션 쿠키 필요, 응답에 Access-Control-Allow-Origin 없음).
  그래서 서버(이 워크플로)가 대신 받아 data/intl_live.json 으로 올리고,
  앱은 그 JSON 을 20초 간격으로 읽는다.
· 경기 중에는 25초 간격으로 다시 받아 값이 바뀌면 즉시 커밋한다.
"""
import json, os, sys, time, subprocess, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
AWB = os.path.join(HERE, 'awb')
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, AWB)
sys.path.insert(0, HERE)

import awb_fetch
import awb_build
import awb_build_names

KST = datetime.timezone(datetime.timedelta(hours=9))
DATA = os.path.join(ROOT, 'data')
RAW = os.path.join(HERE, 'raw')


def git(*args):
    return subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)


def write_atomic(path, text):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


def one_pass(sess, year, games, names_path):
    kbo = [g for g in games if 'ZZZ041' in (g['VisitingTeamCode'], g['HomeTeamCode'])]
    today = datetime.datetime.now(KST).strftime('%Y-%m-%d')
    want = [g for g in kbo if g['GameDate'][:10] >= today][:8]
    for g in want:
        p = os.path.join(RAW, 'game_%02d.json' % g['GameSno'])
        try:
            d = awb_fetch.box(sess, year, g['GameSno'])
            json.dump(d, open(p, 'w'), ensure_ascii=False)
        except Exception as e:
            print('box fail', g['GameSno'], e)
    return awb_build.build(schedule_path=os.path.join(RAW, 'schedule.json'),
                           raw_dir=RAW, names_path=names_path)


def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    loop = int(os.environ.get('AWB_LOOP_SEC', '0'))
    names_path = os.path.join(AWB, 'names.json')
    sess = awb_fetch.session()

    # 명단 사전은 하루 1회만 새로 만든다
    need_names = True
    if os.path.exists(names_path):
        age = time.time() - os.path.getmtime(names_path)
        need_names = age > 86400
    if need_names:
        for t in awb_build_names.TEAMS:
            for en in (False, True):
                d = awb_fetch.roster(sess, t, en)
                json.dump(d, open(os.path.join(RAW, 'roster_%s_%s.json' % (t, 'en' if en else 'zh')), 'w'), ensure_ascii=False)
        nm = awb_build_names.build(RAW)
        write_atomic(names_path, json.dumps(nm, ensure_ascii=False, indent=0))

    year, games = awb_fetch.schedule(sess)
    json.dump({'year': year, 'games': games}, open(os.path.join(RAW, 'schedule.json'), 'w'), ensure_ascii=False)

    last_commit = 0
    last_body = ''
    t0 = time.time()
    while True:
        data = one_pass(sess, year, games, names_path)
        body = json.dumps({k: v for k, v in data.items() if k != 'meta'}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        txt = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        js = 'window.V212_RECEIVE&&window.V212_RECEIVE(' + txt + ');'
        write_atomic(os.path.join(DATA, 'intl_live.json'), txt)
        write_atomic(os.path.join(DATA, 'intl_live.js'), js)
        # manifest 의 checked_at(서버 정기점검 시각) 갱신
        mp = os.path.join(DATA, 'manifest.json')
        man = json.load(open(mp, encoding='utf-8'))
        man['checked_at'] = data['meta']['checked_at']
        man['intl_live'] = {'bytes': len(txt.encode()), 'sha256': hashlib.sha256(txt.encode()).hexdigest(),
                            'checked_at': data['meta']['checked_at'], 'state': data['meta']['state']}
        write_atomic(mp, json.dumps(man, ensure_ascii=False, indent=1) + '\n')
        write_atomic(os.path.join(DATA, 'manifest.js'),
                     'window.V211_RECEIVE&&window.V211_RECEIVE(' + json.dumps(man, ensure_ascii=False, separators=(',', ':')) + ');')

        changed = body != last_body
        now = time.time()
        if changed or now - last_commit > 120:
            git('add', 'data/intl_live.json', 'data/intl_live.js', 'data/manifest.json', 'data/manifest.js')
            r = git('commit', '-m', 'AWB live %s' % data['meta']['checked_at'])
            if r.returncode == 0:
                for _ in range(3):
                    p = git('push', 'origin', 'HEAD:main')
                    if p.returncode == 0:
                        break
                    time.sleep(3)
                last_commit = now
                last_body = body
        if loop <= 0 or now - t0 > loop:
            break
        time.sleep(25)


if __name__ == '__main__':
    main()
