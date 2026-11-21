# -*- coding: utf-8 -*-
"""AWB 공식 데이터 → 앱용 intl_live.json (한국어 100%)."""
import json, os, re, sys, datetime, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from awb_tr import subs as tr_subs, CJK

KST = datetime.timezone(datetime.timedelta(hours=9))
TEAMS = {
    'ZZZ041': {'ko': 'KBO 연합팀', 'short': 'KBO 연합', 'flag': '🇰🇷', 'kbo': True},
    'ZZZ040': {'ko': '일본 프로야구 연합팀', 'short': '일본 프로', 'flag': '🇯🇵', 'kbo': False},
    'ZZZ083': {'ko': '일본 사회인 연합팀', 'short': '일본 사회인', 'flag': '🇯🇵', 'kbo': False},
    'ZZZ389': {'ko': '대만 해양팀', 'short': '대만 해양', 'flag': '🇹🇼', 'kbo': False},
    'ZZZ379': {'ko': '대만 산림팀', 'short': '대만 산림', 'flag': '🇹🇼', 'kbo': False},
    'ZZZ409': {'ko': '대만 대학 올스타', 'short': '대학 올스타', 'flag': '🇹🇼', 'kbo': False},
}
PARKS = {'嘉義市': '자이시 야구장', '亞太主': '타이난 아시아태평양 야구장', '亞太': '타이난 아시아태평양 야구장'}
POS = {'P': '투수', 'C': '포수', '1B': '1루수', '2B': '2루수', '3B': '3루수', 'SS': '유격수',
       'LF': '좌익수', 'CF': '중견수', 'RF': '우익수', 'DH': '지명타자', '': '-'}
ACT = {
    '三振': '삼진', '飛球接殺': '플라이 아웃', '四壞球': '볼넷', '一壘安打': '1루타',
    '刺殺': '땅볼 아웃', '二壘安打': '2루타', '趁傳': '틈타 진루', '界外飛球接殺': '파울 플라이 아웃',
    '雙殺打 刺殺': '병살타', '觸身死球': '몸에 맞는 공', '犧牲飛球': '희생플라이',
    '一壘安打 內野安打': '내야 안타', '野手接球自踩壘包 一壘': '베이스 밟아 아웃',
    '三壘安打': '3루타', '接球失誤': '포구 실책', '全壘打': '홈런', '傳球失誤': '송구 실책',
    '野手接球觸殺': '태그 아웃', '內野高飛球': '내야 플라이 아웃', '一壘安打 場地安打': '그라운드 안타',
    '犧牲短打 傳球': '희생번트', '三振/遭捕手傳一壘刺殺': '삼진 후 포수 1루 송구 아웃',
    '不死三振 暴投': '삼진 후 폭투 출루', '犧牲界外飛球': '희생 파울 플라이',
    '犧牲短打上壘-失誤': '희생번트 출루(실책)', '': '',
}
DIR = {'右外野': '우익수', '中外野': '중견수', '左外野': '좌익수', '內野': '내야'}
STATUS = {1: ('pre', '경기 전'), 2: ('live', '경기 중'), 3: ('final', '경기 종료'),
          4: ('final', '경기 종료'), 5: ('stop', '경기 중단'), 6: ('cancel', '취소'),
          7: ('final', '경기 종료'), 8: ('final', '경기 종료')}


def kst(s):
    if not s:
        return ''
    return s  # 사이트 시각은 현지(대만, UTC+8) → KST +1h


def tw_to_kst(s):
    """'2026-11-21T18:05:00' 대만 현지 → KST '19:05'"""
    if not s:
        return ''
    try:
        dt = datetime.datetime.fromisoformat(s[:19])
    except Exception:
        return ''
    return (dt + datetime.timedelta(hours=1)).strftime('%H:%M')


def load_names(path='names.json'):
    n = json.load(open(path, encoding='utf-8'))
    by_acnt = n
    by_zh = {v['zh']: v['ko'] for v in n.values()}
    return by_acnt, by_zh


def name_of(acnt, zh, names):
    v = names.get(str(acnt))
    if v:
        return v['ko']
    return ''


def parse_lineups(first, names):
    """FirstSnoJson → 팀별 타순·수비 위치·교체 이력"""
    out = {}
    for p in first or []:
        t = p['TeamNo']
        out.setdefault(t, [])
        out[t].append(p)
    res = {}
    for t, rows in out.items():
        order = {}
        for r in rows:
            ln = int(r['Lineup'])
            if ln == 0:
                continue
            slot = order.setdefault(ln, [])
            slot.append(r)
        lineup = []
        for ln in sorted(order):
            rows2 = order[ln]
            rows2.sort(key=lambda r: str(r.get('MainEventNoS') or ''))
            first_row = rows2[0]
            subs_list = []
            seen_sub = set()
            for r in rows2[1:]:
                nm2 = name_of(r['Acnt'], r['CHName'], names)
                ps2 = POS.get(r['DefendStationCode'], r['DefendStationCode'])
                key2 = (nm2, ps2)
                if key2 in seen_sub:
                    continue
                seen_sub.add(key2)
                subs_list.append({'name': nm2, 'pos': ps2,
                                  'at': str(r.get('MainEventNoS') or '')})
            lineup.append({
                'order': ln,
                'name': name_of(first_row['Acnt'], first_row['CHName'], names),
                'no': first_row.get('UniformNo', ''),
                'pos': POS.get(first_row['DefendStationCode'], first_row['DefendStationCode']),
                'now': POS.get(rows2[-1]['DefendStationCode'], rows2[-1]['DefendStationCode']),
                'now_name': name_of(rows2[-1]['Acnt'], rows2[-1]['CHName'], names),
                'subs': subs_list,
            })
        # 현재 수비 라인업 (MainEventNoE 가 빈 줄 = 현재)
        cur = []
        seen_pos = set()
        for r in sorted(rows, key=lambda r: -int(r.get('Seq') or 1)):
            if r.get('MainEventNoE'):
                continue
            pos = POS.get(r['DefendStationCode'], r['DefendStationCode'])
            if pos in seen_pos or pos == '-':
                continue
            seen_pos.add(pos)
            cur.append({'pos': pos, 'name': name_of(r['Acnt'], r['CHName'], names), 'no': r.get('UniformNo', '')})
        res[t] = {'batting': lineup, 'defense': cur}
    return res


def parse_scoreboard(sb, codes):
    """ScoreboardJson → 팀별 이닝 배열 + R/H/E"""
    res = {}
    for r in sb or []:
        t = r['TeamNo']
        d = res.setdefault(t, {'inn': [], 'r': 0, 'h': 0, 'e': 0})
        d['inn'].append(int(r['ScoreCnt'] or 0))
        d['r'] += int(r['ScoreCnt'] or 0)
        d['h'] += int(r['HittingCnt'] or 0)
        d['e'] += int(r['ErrorCnt'] or 0)
    return res


def parse_plays(live, names):
    """LiveLogJson → 완결된 타석만 뽑아 한국어 플레이 목록"""
    plays = []
    last_state = None
    for i, x in enumerate(live or []):
        c = x.get('Content') or ''
        act = (x.get('ActionName') or '').strip()
        finished = any(k in c for k in ('出局', '安打', '上壘', '全壘打', '犧牲', '比賽結束'))
        if not finished:
            last_state = x
            continue
        d = ''
        m = re.search(r'擊出(右外野|中外野|左外野|內野)', c)
        if m:
            d = DIR[m.group(1)]
        ko = ACT.get(act)
        if ko is None:
            ko = ACT.get(act.strip())
        if ko is None:
            ko = ''
        plays.append({
            'inn': int(x.get('InningSeq') or 0),
            'half': '초' if str(x.get('VisitingHomeType')) == '1' else '말',
            'batter': name_of(x.get('HitterAcnt'), x.get('HitterName'), names),
            'pitcher': name_of(x.get('PitcherAcnt'), x.get('PitcherName'), names),
            'dir': d, 'act': ko,
            'o': int(x.get('OutCnt') or 0),
            'va': int(x.get('VisitingScore') or 0), 'ho': int(x.get('HomeScore') or 0),
            'scored': str(x.get('IsScoreCnt')) == '1',
            'b1': bool(x.get('FirstBase')), 'b2': bool(x.get('SecondBase')), 'b3': bool(x.get('ThirdBase')),
        })
        last_state = x
    return plays, last_state


def parse_subs(live, names):
    out = []
    for x in live or []:
        if '更換' in (x.get('Content') or ''):
            for s in tr_subs(x['Content'], names):
                if s not in out:
                    out.append(s)
    return out


# ---------- 승률(자체 산식) ----------
def rates(games_bat):
    PA = H = B2 = B3 = HR = BB = HBP = SO = 0
    for b in games_bat:
        for p in b:
            PA += int(p.get('PlateAppearances') or 0)
            H += int(p.get('HittingCnt') or 0)
            B2 += int(p.get('TwoBaseHitCnt') or 0)
            B3 += int(p.get('ThreeBaseHitCnt') or 0)
            HR += int(p.get('HomeRunCnt') or 0)
            BB += int(p.get('BasesONBallsCnt') or 0)
            HBP += int(p.get('HitBYPitchCnt') or 0)
            SO += int(p.get('StrikeOutCnt') or 0)
    PA = max(PA, 1)
    p1 = max(H - B2 - B3 - HR, 0) / PA
    p2 = B2 / PA
    p3 = B3 / PA
    phr = HR / PA
    pbb = (BB + HBP) / PA
    pso = SO / PA
    pout = max(1 - (p1 + p2 + p3 + phr + pbb + pso), 0.05)
    return np.array([pout, pso, pbb, p1, p2, p3, phr])


def wp_sim(rate, inning, half, outs, bases, diff, n=6000, seed=7):
    """visiting(=away) 승리 확률. bases: 비트0=1루,1=2루,2=3루"""
    rng = np.random.default_rng(seed)
    d = np.full(n, diff, dtype=np.int16)      # home - away
    inn = np.full(n, inning, dtype=np.int16)
    hf = np.full(n, half, dtype=np.int8)      # 0 top(away 공격), 1 bottom
    ob = np.full(n, outs, dtype=np.int8)
    b1 = np.full(n, bool(bases & 1)); b2 = np.full(n, bool(bases & 2)); b3 = np.full(n, bool(bases & 4))
    alive = np.ones(n, dtype=bool)
    p = rate / rate.sum()
    while alive.any():
        idx = np.where(alive)[0]
        # 종료 조건
        done = ((inn[idx] >= 9) & (hf[idx] == 1) & (d[idx] > 0)) | \
               ((inn[idx] >= 9) & (hf[idx] == 0) & (d[idx] == 0) & (ob[idx] >= 3))
        alive[idx[done]] = False
        idx = np.where(alive)[0]
        if idx.size == 0:
            break
        # 한 타석
        res = rng.choice(7, size=idx.size, p=p)
        for k, ii in enumerate(idx):
            rr = res[k]
            if rr == 0 or rr == 1:      # 아웃
                ob[ii] += 1
                if ob[ii] >= 3:
                    ob[ii] = 0; b1[ii] = b2[ii] = b3[ii] = False
                    if hf[ii] == 0:
                        hf[ii] = 1
                    else:
                        hf[ii] = 0; inn[ii] += 1
                    if inn[ii] > 15:
                        alive[ii] = False
                continue
            runs = 0
            if rr == 2:                 # 볼넷
                if b1[ii] and b2[ii] and b3[ii]:
                    runs += 1
                nb3 = b3[ii] or (b2[ii] and b1[ii])
                nb2 = b2[ii] or b1[ii]
                b3[ii] = nb3; b2[ii] = nb2; b1[ii] = True
            elif rr == 3:               # 1루타
                runs += 1 if b3[ii] else 0
                nb3 = b2[ii]
                nb2 = b1[ii]
                b3[ii] = nb3; b2[ii] = nb2; b1[ii] = True
            elif rr == 4:               # 2루타
                runs += (1 if b3[ii] else 0) + (1 if b2[ii] else 0)
                b3[ii] = b1[ii]; b2[ii] = True; b1[ii] = False
            elif rr == 5:               # 3루타
                runs += (1 if b3[ii] else 0) + (1 if b2[ii] else 0) + (1 if b1[ii] else 0)
                b3[ii] = True; b2[ii] = b1[ii] = False
            else:                       # 홈런
                runs += 1 + (1 if b3[ii] else 0) + (1 if b2[ii] else 0) + (1 if b1[ii] else 0)
                b3[ii] = b2[ii] = b1[ii] = False
            if hf[ii] == 0:
                d[ii] -= runs           # away 득점
            else:
                d[ii] += runs
        # 9회말 종료 처리
        idx2 = np.where(alive & (inn >= 9) & (hf == 1) & (ob >= 3))[0]
        alive[idx2] = False
        idx3 = np.where(alive & (inn >= 9) & (hf == 1) & (d != 0))[0]
        alive[idx3] = False
    return float(np.mean(d < 0))


def wp_series(rate, plays, kbo_code, away_code):
    """각 플레이 직후 KBO 팀 승리 확률(%)"""
    pts = []
    last = None
    for p in plays:
        # 상태 재구성은 플레이 필드의 아웃/점수만 사용(주자 상태는 생략 → 표준 근사)
        base = (1 if p.get('b1') else 0) | (2 if p.get('b2') else 0) | (4 if p.get('b3') else 0)
        key = (p['inn'], 0 if p['half'] == '초' else 1, min(p['o'], 2), base, p['ho'] - p['va'])
        if key == last:
            continue
        last = key
        pw = wp_sim(rate, key[0], key[1], key[2], key[3], key[4], n=4000, seed=11)
        if kbo_code != away_code:
            pw = 1 - pw
        pts.append({'inn': p['inn'], 'half': p['half'], 'p': round(pw * 100, 1)})
    return pts


def build(schedule_path='raw/schedule.json', raw_dir='raw', names_path='names.json', now=None, include_final=False):
    now = now or datetime.datetime.now(KST)
    names, zh_pairs = load_names(names_path)
    pairs = sorted(zh_pairs.items(), key=lambda x: -len(x[0]))
    sch = json.load(open(schedule_path, encoding='utf-8'))
    games = sch['games']
    bat_all = []
    for g in games:
        p = os.path.join(raw_dir, 'game_%02d.json' % g['GameSno'])
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            if d.get('BattingJson'):
                try:
                    bat_all.append(json.loads(d['BattingJson']))
                except Exception:
                    pass
    rate = rates(bat_all)
    today = now.strftime('%Y-%m-%d')
    out_games = []
    upcoming = []
    for g in games:
        code_v, code_h = g['VisitingTeamCode'], g['HomeTeamCode']
        if 'ZZZ041' not in (code_v, code_h):
            continue
        gd = g['GameDate'][:10]
        if gd < today:
            continue
        p = os.path.join(raw_dir, 'game_%02d.json' % g['GameSno'])
        d = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        cur = {}
        try:
            cur = json.loads(d.get('CurtGameDetailJson') or '{}')
        except Exception:
            cur = {}
        st = int(cur.get('GameStatus') or 1)
        status, status_ko = STATUS.get(st, ('pre', '경기 전'))
        def zk(x):
            return zh_pairs.get(str(x or '').strip(), str(x or ''))
        item = {
            'no': g['GameSno'], 'date': gd, 'time_kst': tw_to_kst(cur.get('PreExeDate') or g['GameDateTimeS']),
            'park': PARKS.get(cur.get('FieldAbbe') or g['FieldAbbe'], cur.get('FieldAbbe') or g['FieldAbbe']),
            'status': status, 'status_ko': status_ko,
            'away': {'code': code_v, 'name': TEAMS.get(code_v, {}).get('ko', g['VisitingTeamName']),
                     'flag': TEAMS.get(code_v, {}).get('flag', '')},
            'home': {'code': code_h, 'name': TEAMS.get(code_h, {}).get('ko', g['HomeTeamName']),
                     'flag': TEAMS.get(code_h, {}).get('flag', '')},
        }
        if status == 'final':
            # 끝난 경기는 종료 20분 안에만 남긴다(그 뒤에는 국제대회 화면에서 사라진다)
            end = (cur.get('GameDateTimeE') or '')[:19]
            try:
                dt = datetime.datetime.fromisoformat(end) + datetime.timedelta(hours=1)
                dt = dt.replace(tzinfo=KST)
                item['recent'] = (now - dt).total_seconds() < 20 * 60
            except Exception:
                item['recent'] = False
        if status in ('live', 'final'):
            sb = parse_scoreboard(json.loads(d.get('ScoreboardJson') or '[]'), (code_v, code_h))
            item['score'] = {
                'away': sb.get(code_v, {}).get('r', 0), 'home': sb.get(code_h, {}).get('r', 0),
                'away_h': sb.get(code_v, {}).get('h', 0), 'home_h': sb.get(code_h, {}).get('h', 0),
                'away_e': sb.get(code_v, {}).get('e', 0), 'home_e': sb.get(code_h, {}).get('e', 0),
                'inn_away': sb.get(code_v, {}).get('inn', []), 'inn_home': sb.get(code_h, {}).get('inn', []),
            }
            try:
                live = json.loads(d.get('LiveLogJson') or '[]')
            except Exception:
                live = []
            plays, last = parse_plays(live, names)
            item['plays'] = plays[-40:]
            item['subs'] = parse_subs(live, pairs)
            if last:
                item['state'] = {
                    'inn': int(last.get('InningSeq') or 0),
                    'half': '초' if str(last.get('VisitingHomeType')) == '1' else '말',
                    'outs': int(last.get('OutCnt') or 0),
                    'b': int(last.get('BallCnt') or 0), 's': int(last.get('StrikeCnt') or 0),
                    'bases': [bool(last.get('FirstBase')), bool(last.get('SecondBase')), bool(last.get('ThirdBase'))],
                    'runner1': name_of('', last.get('FirstBase'), names) if False else '',
                    'batter': name_of(last.get('HitterAcnt'), last.get('HitterName'), names),
                    'pitcher': name_of(last.get('PitcherAcnt'), last.get('PitcherName'), names),
                }
            try:
                first = json.loads(d.get('FirstSnoJson') or '[]')
            except Exception:
                first = []
            lu = parse_lineups(first, names)
            item['lineup'] = {'away': lu.get(code_v, {}), 'home': lu.get(code_h, {})}
            try:
                bat = json.loads(d.get('BattingJson') or '[]')
            except Exception:
                bat = []
            box = {}
            for side, code in (('away', code_v), ('home', code_h)):
                rows = [b for b in bat if str(b.get('VisitingHomeType')) == ('1' if side == 'away' else '2')]
                box[side] = [{'name': name_of(b.get('HitterAcnt'), b.get('HitterName'), names),
                              'pa': int(b.get('PlateAppearances') or 0),
                              'h': int(b.get('HitCnt') or 0), 'hr': int(b.get('HomeRunCnt') or 0),
                              'rbi': int(b.get('RunBattedINCnt') or 0), 'r': int(b.get('ScoreCnt') or 0),
                              'bb': int(b.get('BasesONBallsCnt') or 0), 'so': int(b.get('StrikeOutCnt') or 0)}
                             for b in rows]
            item['box'] = box
            item['wp'] = wp_series(rate, plays, 'ZZZ041', code_v)
        else:
            item['starters'] = {'away': zk(cur.get('VisitingFirstMover', '')), 'home': zk(cur.get('HomeFirstMover', ''))}
        out_games.append(item)
    live_g = [g for g in out_games if g['status'] == 'live']
    pre_g = [g for g in out_games if g['status'] == 'pre']
    fin_g = [g for g in out_games if g['status'] == 'final']
    games_sel = (live_g + (fin_g if include_final else []) + pre_g)[:6]
    data = {
        'schema': 1,
        'competition': {
            'id': 'awb2026', 'name': '2026 아시아 윈터 베이스볼 리그',
            'period': '2026-11-14 ~ 2026-12-06', 'host': '대만 프로야구 주관',
            'note': 'KBO 연합팀은 14경기(정규 50경기 중) 출전 · 플레이오프 미참가',
        },
        'meta': {
            'checked_at': now.strftime('%Y-%m-%dT%H:%M:%S+09:00'),
            'source': 'https://awb.cpbl.com.tw',
            'state': 'live' if live_g else ('pre' if pre_g else 'none'),
            'games': len(games_sel),
        },
        'teams': {k: {'ko': v['ko'], 'flag': v['flag'], 'kbo': v['kbo']} for k, v in TEAMS.items()},
        'games': games_sel,
    }
    return data


if __name__ == '__main__':
    d = build()
    s = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    print('bytes', len(s.encode()), 'games', len(d['games']), 'state', d['meta']['state'])
    print(CJK.findall(s)[:20])
    json.dump(d, open('intl_live.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    g = d['games'][0]
    print(json.dumps({k: v for k, v in g.items() if k not in ('plays', 'box', 'wp', 'lineup')}, ensure_ascii=False)[:800])
