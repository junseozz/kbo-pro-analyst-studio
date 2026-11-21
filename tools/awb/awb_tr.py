# -*- coding: utf-8 -*-
"""AWB 중국어 중계 문장 → 한국어 (공식 중계 문장 패턴 구조 해석)."""
import re

TEAM_KO = {
    '韓職聯隊': 'KBO 연합팀', '日職聯隊': '일본 프로야구 연합팀', '日本社會人': '일본 사회인 연합팀',
    '台灣海洋': '대만 해양팀', '台灣山林': '대만 산림팀', '大學明星': '대만 대학 올스타',
    '韓國職棒': 'KBO 연합팀',
}
POS_KO = {
    '右外野手': '우익수', '中外野手': '중견수', '左外野手': '좌익수', '游擊手': '유격수',
    '一壘手': '1루수', '二壘手': '2루수', '三壘手': '3루수', '捕手': '포수', '投手': '투수',
    '指定打擊': '지명타자',
}
CJK = re.compile(r'[\u4e00-\u9fff]')


def _pos(s):
    for k, v in POS_KO.items():
        s = s.replace(k, v)
    return s


def _seg(seg, names):
    s = seg.strip()
    if not s:
        return ''
    for zh, ko in names:
        s = s.replace(zh, ko)
    for zh, ko in TEAM_KO.items():
        s = s.replace(zh, ko)
    s = _pos(s)
    # 투구·기본
    simple = {
        '壞球': '볼', '好球沒揮棒': '스트라이크', '揮棒落空': '헛스윙',
        '擊出界外球': '파울', '界外球(觸擊)': '파울(번트)', '擦棒被捕球': '파울팁',
        '教練暫停': '감독 타임', '比賽結束': '경기 종료', '投手牽制一壘跑者': '투수 1루 견제',
        '四壞球上壘': '볼넷 출루', '觸身死球上壘': '몸에 맞는 공 출루', '故意四壞球上壘': '고의사구 출루',
        '趁傳上壘': '틈타 출루',
    }
    if s in simple:
        return simple[s]
    # 타구
    head = ''
    m = re.match(r'^擊出球\(觸擊\)', s)
    if m:
        head = '번트 타구'
        s = s[m.end():].lstrip('，, ')
    else:
        m = re.match(r'^擊出(內野|右外野|中外野|左外野)?(高飛|平飛|滾)球', s)
        if m:
            d = m.group(1)
            dk = {'內野': '내야', '右外野': '우익수', '中外野': '중견수', '左外野': '좌익수'}.get(d, '')
            tk = {'高飛': '플라이', '平飛': '라인드라이브', '滾': '땅볼'}[m.group(2)]
            head = (dk + ' ' + tk).strip()
            s = s[m.end():].lstrip('，, ')
    body = s
    # 결과 구문 정리
    body = body.replace('打者出局-犧牲飛球出局', '희생플라이 아웃')
    body = body.replace('打者出局-犧牲界外飛球出局', '희생 파울 플라이 아웃')
    body = body.replace('打者-犧牲短打', '희생번트')
    body = body.replace('打者出局-雙殺打', '병살타')
    body = body.replace('打者出局-三振出局', '삼진 아웃')
    body = body.replace('打者-界外飛球接殺出局', '파울 플라이 아웃')
    body = body.replace('打者-內野高飛球出局', '내야 플라이 아웃')
    body = body.replace('打者-飛球接殺出局', '플라이 아웃')
    body = body.replace('打者-', '')  # 수비수 표기는 방향으로 이미 드러난다
    body = re.sub(r'(\S+?) 飛球接殺出局', '플라이 아웃', body)
    body = re.sub(r'(\S+?) 自踩壘包出局', r'\1 베이스 직접 밟아 아웃', body)
    body = re.sub(r'(\S+?) 接球失誤上一壘', '실책 출루', body)
    body = re.sub(r'(\S+?)(?:ベース)?失誤回本壘得分', '실책으로 홈인', body)
    # 송구 아웃: '三壘手 송구 二壘手封殺出局' / '游擊手 傳一壘手刺殺出局'
    def relay(m):
        a, b = m.group(1), m.group(2)
        kind = '포스 아웃' if '封殺' in m.group(0) else ('병살' if '雙殺' in m.group(0) else '송구 아웃')
        return '%s → %s %s' % (a, b, kind)
    body = re.sub(r'(\S+?)の? 송구 (\S+?)(?:封殺出局|刺殺出局)', relay, body)
    body = body.replace('傳', '→').replace(' 송구 ', ' → ')
    body = re.sub(r'(\S+?) → (\S+?)(封殺出局|刺殺出局)', relay, body)
    body = body.replace('封殺出局', '포스 아웃').replace('刺殺出局', '송구 아웃')
    body = body.replace('雙殺打', '병살타')
    body = body.replace('三振出局', '삼진 아웃')
    body = body.replace('犧牲飛球出局', '희생플라이 아웃')
    body = body.replace('野手接球自踩壘包', '야수가 베이스 직접 밟아')
    body = body.replace('野手接球觸殺', '태그 아웃')
    body = body.replace('接殺出局', '플라이 아웃')
    body = re.sub(r'(\d)分打點', r'\1타점', body)
    body = re.sub(r'(\d)人出局', r'\1사', body)
    body = re.sub(r'(\d)壘殘壘', r'잔루 \1루', body)
    body = re.sub(r'(\d)壘安打', r'\1루타', body)
    body = body.replace('內野安打', '내야 안타').replace('場地安打', '그라운드 안타')
    body = body.replace('全壘打', '홈런').replace('再見安打', '끝내기 안타')
    body = re.sub(r'跑者(\S+?)\s*回本壘得分', r'\1 홈인', body)
    body = re.sub(r'跑者(\S+?)\s*上(\d)壘', r'\1 \2루 진루', body)
    body = re.sub(r'跑者(\S+?)出局-盜壘刺', r'\1 도루 실패', body)
    body = re.sub(r'跑者(\S+?)\s*盜壘上(\d)壘', r'\1 \2루 도루 성공', body)
    body = re.sub(r'(\d)壘跑者(\S+?)', r'\1루 주자 \2', body)
    body = body.replace('殘壘', '잔루').replace('上壘', '출루')
    body = body.replace('盜壘', '도루').replace('暴投', '폭투').replace('捕逸', '포일')
    body = body.replace('重播輔助判決-原判', '비디오 판독 - 원심 유지')
    body = body.replace('重播輔助判決-改判', '비디오 판독 - 판정 번복')
    body = body.replace('更換', '교체')
    body = body.replace('，', ', ').replace('。', '. ')
    body = re.sub(r'\s+', ' ', body).strip(' .')
    if head and body:
        return head + ', ' + body
    return head or body


def transfer(text, names):
    """중계 한 줄 → 한국어"""
    s = str(text or '').replace('\r', '').replace('\n', ' ')
    parts = [p for p in re.split(r'。', s) if p.strip()]
    out = []
    for p in parts:
        k = _seg(p, names)
        if k:
            out.append(k)
    r = ' '.join(out)
    r = re.sub(r'(\. )+', '. ', r).strip()
    r = r.replace(' .', '.').replace('..', '.')
    return CJK.sub('', r).strip()


def subs(text, names):
    s = str(text or '').replace('\r', '')
    out = []
    for line in s.split('\n'):
        line = line.strip()
        if not line or '更換' not in line:
            continue
        k = line
        for zh, ko in names:
            k = k.replace(zh, ko)
        for zh, ko in TEAM_KO.items():
            k = k.replace(zh, ko)

        def chg(m):
            kind = {'投手': '투수', '代打': '대타', '代跑': '대주자', '守備': '수비', '選手': '선수'}.get(m.group(1), m.group(1))
            a = m.group(2).strip().rstrip('-').strip()
            b = m.group(3).strip().rstrip('。').strip()
            if kind == '선수':
                # '포수-A => 포수-B' → '포수 교체: A → B'
                ma = re.match(r'^(投手|捕手|一壘手|二壘手|三壘手|游擊手|左外野手|中外野手|右外野手|指定打擊)-(.+)$', a)
                mb = re.match(r'^(投手|捕手|一壘手|二壘手|三壘手|游擊手|左外野手|中外野手|右外野手|指定打擊)-(.+)$', b)
                if ma and mb and ma.group(1) == mb.group(1):
                    return '%s 교체: %s → %s' % (POS_KO.get(ma.group(1), ma.group(1)), ma.group(2).strip(), mb.group(2).strip())
                return '선수 교체: %s → %s' % (a, b)
            return '%s: %s → %s' % (kind, a, b)
        k = re.sub(r'更換(投手|代打|代跑|守備|選手)：([^=＞>]+?)\s*[=＞>]+\s*([^。]+)。?', chg, k)
        k = re.sub(r'更換([^：]{1,4})：', r'\1 교체: ', k)
        k = _pos(k)
        k = k.replace('，', ', ').replace('。', '')
        k = re.sub(r'\s+', ' ', k).strip()
        k = CJK.sub('', k).strip()
        if k:
            out.append(k)
    return out
