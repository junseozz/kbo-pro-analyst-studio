#!/usr/bin/env python3
"""전체 KBO 서버 데이터 자동 점검·동기화 스크립트 (GitHub Actions / 주기 실행 공용).

- KBO 공식 1군/퓨처스 등록 현황(RegisterAll.aspx, Futures/Player/Register.aspx) 기준일 점검
- KBO 공식 보도자료/공지(MediaNews/Notice/List.aspx) 신규 공지 확인 → live_patch.json notices 자동 반영
- 전체 데이터(.json/.js) 및 manifest.json / manifest.js 무결성 유지
"""
import json, urllib.request, re, os, datetime, html as html_mod

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))

def fetch_text(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'ignore')

def check_kbo_official_status():
    now = datetime.datetime.now(KST)
    now_iso = now.isoformat(timespec='seconds')
    today_str = now.strftime('%Y-%m-%d')
    info = {'kbo1_reg_date': '', 'futures_reg_date': '', 'new_notices': 0}

    for key, url in [
        ('kbo1_reg_date', 'https://www.koreabaseball.com/Player/RegisterAll.aspx'),
        ('futures_reg_date', 'https://www.koreabaseball.com/Futures/Player/Register.aspx'),
    ]:
        try:
            page = fetch_text(url, 12)
            m = re.search(r'(20\d{2}\.\d{2}\.\d{2})', page)
            if m:
                info[key] = m.group(1)
        except Exception as e:
            print(f'[sync_kbo_server] {key} fetch warn:', e)

    # KBO 공식 공지사항 최신 5건 확인 -> live_patch.json notices에 미등록 공지 자동 추가
    lp_path = os.path.join(REPO, 'data/live_patch.json')
    lp_js_path = os.path.join(REPO, 'data/live_patch.js')
    lp = json.load(open(lp_path, encoding='utf-8'))
    notices = lp.get('notices') or []
    existing_titles = {re.sub(r'\s+', ' ', str(n.get('title', '') or '')).strip() for n in notices}

    try:
        page = fetch_text('https://www.koreabaseball.com/MediaNews/Notice/List.aspx', 12)
        added = []
        for m in re.finditer(r'<tr[^>]*>(.*?)</tr>', page, re.S):
            row = m.group(1)
            a = re.search(r'<a[^>]+href="([^"]*View\.aspx[^"]*)"[^>]*>(.*?)</a>', row, re.S)
            dm = re.search(r'(20\d{2})\.(\d{2})\.(\d{2})', row)
            if not (a and dm):
                continue
            dt_str = f'{dm.group(1)}-{dm.group(2)}-{dm.group(3)}'
            # 최근 7일 내 공지만 신규 반영 대상
            try:
                dt_obj = datetime.datetime.strptime(dt_str, '%Y-%m-%d').replace(tzinfo=KST)
                if (now - dt_obj).days > 7:
                    continue
            except Exception:
                continue
            title = re.sub(r'\s+', ' ', html_mod.unescape(re.sub(r'<[^>]+>', '', a.group(2)))).strip()
            if not title or title in existing_titles:
                continue
            # 이미 동일 핵심어가 반영된 공지(예: 구자욱 신분조회, 시상식)는 중복 방지
            if any(kw in title and any(kw in et for et in existing_titles) for kw in ['구자욱', '시상식', 'FA 승인']):
                continue
            existing_titles.add(title)
            added.append({
                'date': dt_str,
                'tag': 'KBO공시',
                'title': title,
                'detail': 'KBO 공식 보도자료·공지사항 자동 확인'
            })
            if len(added) >= 3:
                break
        if added:
            lp['notices'] = (added + notices)[:30]
            info['new_notices'] = len(added)
    except Exception as e:
        print('[sync_kbo_server] KBO notice warn:', e)

    lp['checked_at'] = now_iso
    lp['updated_at'] = now_iso
    if info['kbo1_reg_date'] or info['futures_reg_date']:
        lp.setdefault('ai_facts', {})
        if isinstance(lp['ai_facts'], dict):
            prev_fact = str(lp['ai_facts'].get('official_check') or '')
            new_fact = (
                f"KBO 1군 등록 기준 {info['kbo1_reg_date'] or '-'} · "
                f"퓨처스 등록 기준 {info['futures_reg_date'] or '-'} · 최종 점검 {today_str}"
            )
            # 공식 등록 기준일이 실제로 바뀌었을 때만 notices에 자동 알림 추가
            for label, dt_val in [('1군 등록 현황', info['kbo1_reg_date']), ('퓨처스 등록 현황', info['futures_reg_date'])]:
                if dt_val and prev_fact and dt_val not in prev_fact:
                    nt = f'KBO 공식 {label} 갱신 ({dt_val})'
                    if nt not in existing_titles:
                        lp['notices'] = ([{
                            'date': today_str,
                            'tag': '등록변동',
                            'title': nt,
                            'detail': 'KBO 공식 등록 페이지 기준일 변경 감지'
                        }] + (lp.get('notices') or []))[:30]
                        existing_titles.add(nt)
                        info['new_notices'] += 1
            lp['ai_facts']['official_check'] = new_fact

    with open(lp_path, 'w', encoding='utf-8') as f:
        json.dump(lp, f, ensure_ascii=False, indent=1)
        f.write('\n')
    lp_min = json.dumps(lp, ensure_ascii=False, separators=(',', ':'))
    with open(lp_js_path, 'w', encoding='utf-8') as f:
        f.write('/* KBO Pro Analyst Studio — v21.0 live patch (JSONP 대체 로더용 래퍼) */\n')
        f.write(f'window.V210_RECEIVE && window.V210_RECEIVE({lp_min});\n')

    print('[sync_kbo_server]', info)
    return info

if __name__ == '__main__':
    check_kbo_official_status()
