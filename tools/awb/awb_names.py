# -*- coding: utf-8 -*-
"""이름 한국어 표기 — KBO 연합팀은 공식 로마자 표기와 대조한 한글 이름,
일본 선수는 로마자→한글 음역, 대만 선수는 한자→병음→한글 음역."""
import re

# 1) KBO 연합팀 — AWB 공식 로마자 표기 + KBO 등록 한글 이름 대조
KO = {
    '李明鍾': '이명종', '李康俊': '이강준', '丁炫瑀': '정현우', '金潤何': '김윤하',
    '曺永健': '조영건', '金星眞': '김성진', '崔炫旴': '최현우', '洪敏基': '홍민기',
    '李鍾旼': '이종민', '李鍾旼': '이종민', '丁茶勛': '정다훈', '河炫丞': '하현승',
    '金序俊': '김서준', '李太陽': '이태양', '辛東建': '신동건', '林璡默': '임진묵',
    '林璡默': '임진묵', '白晉守': '백진수', '朴世埈': '박세준', '金東爀': '김동혁',
    '金眠隽': '김민준', '金廷炫': '김정현', '金大承': '김대승', '金侀錄': '김경록',
    '李沅鍈': '이원영', '金兌彦': '김태언', '朴凖鍵': '박준건', '金類彬': '김유빈',
    '鄭文赫': '정문혁', '金時仰': '김시앙', '金東憲': '김동헌', '金智晟': '김지성',
    '金주영': '김주영', '程大善': '정대선', '李昇沅': '이승원', '李昇沅': '이승원',
    '金熊斌': '김웅빈', '崔宰榮': '최재영', '廉承沅': '염승원', '廉承沅': '염승원',
    '崔佑準': '최우준', '裵廷昊': '배정호', '呂東煜': '여동욱', '呂東煜': '여동욱',
    '柳程擇': '유정택', '李主形': '이주형', '張栽榮': '장재영', '玄彬': '현빈',
    '秋材賢': '추재현', '朴燦爀': '박찬혁', '趙禧成': '조희성', '朴彩鬱': '박채울',
    '田太鉉': '전태현',
    # 코칭스태프
    '薛鍾鎭': '설종진', '李想景': '이상경', '文燦宗': '문찬종', '金俊完': '김준완',
    '姜炳植': '강병식', '盧炳娛': '노병오', '盧炳娛': '노병오', '陳該受': '진해수',
    '李性烈': '이성열', '朴度炫': '박도현', '金守經': '김수경', '金壽經': '김수경',
}

# 2) 로마자 → 한글 (일본 선수 이름)
CHO = {'g': 0, 'k': 15, 'n': 2, 'd': 3, 't': 16, 'r': 5, 'l': 5, 'm': 6, 'b': 7,
       'p': 17, 'f': 17, 'v': 7, 's': 9, 'z': 12, 'j': 12, 'h': 18, 'y': 11, 'w': 11,
       'ch': 14, 'sh': 9, 'ts': 14, 'tz': 12, '': 11}
JUNG = {'a': 0, 'i': 20, 'u': 13, 'e': 5, 'o': 8, 'ya': 2, 'yu': 17, 'yo': 12,
        'ye': 6, 'wa': 9, 'wo': 14, 'we': 15, 'wi': 16, 'u': 13, 'ai': 0, 'ei': 5,
        'ou': 8, 'au': 0, 'aa': 0, 'ii': 20, 'uu': 13, 'ee': 5, 'oo': 8}
JONG = {'n': 4, 'ng': 21, 'm': 16}

JP_SYL = [
    ('kya', '캬'), ('kyu', '큐'), ('kyo', '쿄'), ('sha', '샤'), ('shu', '슈'), ('sho', '쇼'),
    ('she', '셰'), ('shi', '시'), ('cha', '차'), ('chu', '추'), ('cho', '초'), ('che', '체'),
    ('chi', '치'), ('tsu', '쓰'), ('nya', '냐'), ('nyu', '뉴'), ('nyo', '뇨'), ('hya', '햐'),
    ('hyu', '휴'), ('hyo', '효'), ('rya', '랴'), ('ryu', '류'), ('ryo', '료'), ('gya', '갸'),
    ('gyu', '규'), ('gyo', '교'), ('ja', '자'), ('ju', '주'), ('jo', '조'), ('je', '제'),
    ('ji', '지'), ('bya', '뱌'), ('byu', '뷰'), ('byo', '뵤'), ('pya', '퍄'), ('pyu', '퓨'),
    ('pyo', '표'), ('ka', '카'), ('ki', '키'), ('ku', '쿠'), ('ke', '케'), ('ko', '코'),
    ('sa', '사'), ('su', '스'), ('se', '세'), ('so', '소'), ('ta', '타'), ('chi', '치'),
    ('te', '테'), ('to', '토'), ('tu', '투'), ('na', '나'), ('ni', '니'), ('nu', '누'),
    ('ne', '네'), ('no', '노'), ('ha', '하'), ('hi', '히'), ('fu', '후'), ('hu', '후'),
    ('he', '헤'), ('ho', '호'), ('ma', '마'), ('mi', '미'), ('mu', '무'), ('me', '메'),
    ('mo', '모'), ('ya', '야'), ('yu', '유'), ('yo', '요'), ('ra', '라'), ('ri', '리'),
    ('ru', '루'), ('re', '레'), ('ro', '로'), ('wa', '와'), ('wo', '오'), ('ga', '가'),
    ('gi', '기'), ('gu', '구'), ('ge', '게'), ('go', '고'), ('za', '자'), ('zu', '즈'),
    ('ze', '제'), ('zo', '조'), ('da', '다'), ('de', '데'), ('do', '도'), ('ba', '바'),
    ('bi', '비'), ('bu', '부'), ('be', '베'), ('bo', '보'), ('pa', '파'), ('pi', '피'),
    ('pu', '푸'), ('pe', '페'), ('po', '포'), ('a', '아'), ('i', '이'), ('u', '우'),
    ('e', '에'), ('o', '오'),
]
JP_SYL.sort(key=lambda x: -len(x[0]))


def _add_jong(out, jong):
    if not out:
        return out
    code = ord(out[-1]) - 0xAC00
    if 0 <= code < 11172:
        a, j = divmod(code, 28)
        cho, jung = divmod(a, 21)
        if j == 0:
            return out[:-1] + chr(0xAC00 + (cho * 21 + jung) * 28 + jong)
    return out


def jp_one(word):
    """한 단어(예: 'Takahiro') 로마자 → 한글"""
    w = word.lower().replace('-', '').replace(' ', '')
    out = ''
    i, n = 0, len(w)
    while i < n:
        if w[i] == 'n' and (i + 1 >= n or w[i + 1] not in 'aeiouy'):
            out = _add_jong(out, 16 if (i + 1 < n and w[i + 1] in 'bmp') else 4)
            i += 1
            continue
        if w[i] in 'kstpc' and i + 1 < n and w[i + 1] == w[i]:
            out = _add_jong(out, {'k': 1, 's': 19, 't': 19, 'p': 17, 'c': 19}.get(w[i], 19))
            i += 1
            continue
        for k, ko in JP_SYL:
            if w.startswith(k, i):
                out += ko
                i += len(k)
                break
        else:
            i += 1
    return out


def jp_name(romaji):
    """'CHIBA Takahiro' → '치바 다카히로'"""
    parts = str(romaji).split()
    if len(parts) >= 2:
        return jp_one(parts[0]) + ' ' + jp_one(''.join(parts[1:]))
    return jp_one(romaji)


# 3) 병음 → 한글 (대만 선수 이름)
PY_INIT = {'b': 7, 'p': 17, 'm': 6, 'f': 17, 'd': 3, 't': 16, 'n': 2, 'l': 5,
           'g': 0, 'k': 15, 'h': 18, 'j': 12, 'q': 14, 'x': 9, 'zh': 12, 'ch': 14,
           'sh': 9, 'r': 5, 'z': 12, 'c': 14, 's': 9, 'y': 11, 'w': 11, '': 11}
# final → (모음 index 목록, 받침)
PY_FIN = {
    'a': ([0], 0), 'o': ([8], 0), 'e': ([4], 0), 'i': ([20], 0), 'u': ([13], 0),
    'v': ([16], 0), 'ai': ([0, 20], 0), 'ei': ([5, 20], 0), 'ao': ([0, 8], 0),
    'ou': ([8, 13], 0), 'an': ([0], 4), 'en': ([4], 4), 'ang': ([0], 21),
    'eng': ([4], 21), 'ong': ([13], 21), 'er': ([4], 7), 'ia': ([2], 0),
    'ie': ([6], 0), 'iao': ([2, 8], 0), 'iu': ([17], 0), 'ian': ([6], 4),
    'in': ([20], 4), 'iang': ([2], 21), 'ing': ([20], 21), 'iong': ([17], 21),
    'ua': ([9], 0), 'uo': ([14], 0), 'uai': ([9, 20], 0), 'ui': ([16], 0),
    'uan': ([9], 4), 'un': ([14], 4), 'uang': ([9], 21), 'ueng': ([14], 21),
    've': ([15], 0), 'van': ([15], 4), 'vn': ([16], 4), 'ue': ([15], 0),
    'uei': ([15, 20], 0), 'iou': ([17], 0), 'uen': ([14], 4), 'n': ([], 4),
    'ng': ([], 21), 'r': ([4], 7),
}
PY_SPECIAL = {
    'yi': '이', 'ya': '야', 'ye': '예', 'yao': '야오', 'you': '유', 'yan': '옌',
    'yin': '인', 'yang': '양', 'ying': '잉', 'yong': '융', 'yu': '위', 'yue': '웨',
    'yuan': '위안', 'yun': '윈', 'wu': '우', 'wa': '와', 'wo': '워', 'wai': '와이',
    'wei': '웨이', 'wan': '완', 'wen': '원', 'wang': '왕', 'weng': '웡',
    'zhi': '즈', 'chi': '츠', 'shi': '스', 'ri': '르', 'zi': '즈', 'ci': '츠', 'si': '스',
    'er': '얼', 'n': '은', 'ng': '응', 'm': '음',
}
PY_FIN_ORDER = sorted(PY_FIN, key=len, reverse=True)
PY_INIT_ORDER = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k',
                 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w']


def _syl(cho, jung, jong):
    return chr(0xAC00 + (cho * 21 + jung) * 28 + jong)


def py_one(syl):
    s = syl.lower().replace('ü', 'v')
    if s in PY_SPECIAL:
        return PY_SPECIAL[s]
    ini = ''
    for i in PY_INIT_ORDER:
        if s.startswith(i) and len(s) > len(i):
            ini = i
            break
    rest = s[len(ini):]
    cho = PY_INIT.get(ini, 11)
    best = None
    for f in PY_FIN_ORDER:
        if rest == f:
            best = f
            break
    if best is None:
        return ''
    v, j = PY_FIN[best]
    if not v:
        return {4: '은', 21: '응'}.get(j, '')
    if best == 'ie':
        return _syl(cho, 20, 0) + _syl(11, 5, 0)
    out = _syl(cho, v[0], j)
    for x in v[1:]:
        out += _syl(11, x, 0)
    return out


def zh_name(hanzi):
    """'潘瑋祥' → '판웨이샹'"""
    try:
        from pypinyin import lazy_pinyin
    except Exception:
        return ''
    out = []
    for ch in str(hanzi):
        if ch.strip() == '':
            out.append(' ')
            continue
        py = lazy_pinyin(ch)
        if not py:
            out.append(ch)
            continue
        k = py_one(py[0])
        out.append(k or ch)
    return ''.join(out).replace('  ', ' ').strip()


if __name__ == '__main__':
    for w in ['CHIBA Takahiro', 'WATANABE Issei', 'SUZUKI Keishin', 'NAKAMURA Yuto',
              'MATSUNAGA Daiki', 'SHIMOKAWA Shunsuke', 'KAWASHIMO Masahiro', 'AIDA Yushi',
              'MURANAKA Kyohei', 'KINOSHITA Motoya', 'SATO Ryuga', 'INUI Kento']:
        print(w, '->', jp_name(w))
    for h in ['潘瑋祥', '陳品宏', '高聖恩', '黃劼希', '郭天信', '王念好', '張仁瑋', '董子恩', '林岳谷', '廖昭雄']:
        print(h, '->', zh_name(h))
