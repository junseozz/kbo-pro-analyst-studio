# -*- coding: utf-8 -*-
"""AWB 6개 팀 명단 → 선수별 한국어 이름 사전(names.json) 생성."""
import json, os, sys, re, unicodedata
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from awb_names import KO, jp_name, zh_name, py_one, PY_SPECIAL
from pypinyin import lazy_pinyin, pinyin, Style

TEAMS = ['ZZZ041', 'ZZZ040', 'ZZZ083', 'ZZZ389', 'ZZZ409', 'ZZZ379']
JP_TEAMS = ('ZZZ040', 'ZZZ083')


def _norm_wg(s):
    s = s.lower()
    s = s.replace('hs', 'x').replace('ts', 'z').replace('tz', 'z')
    s = re.sub(r'^ch', 'j', s)
    s = re.sub(r'^chh?', 'q', s)
    s = s.replace("'", '')
    return s


def zh_name_match(hanzi, romaji):
    """한자 이름 + 로마자 표기 → 병음 다의어 중 로마자와 가장 가까운 독음 선택."""
    toks = [t for t in str(romaji).split() if t]
    chars = [c for c in str(hanzi) if '\u4e00' <= c <= '\u9fff']
    out = []
    if len(toks) == len(chars):
        pairs = list(zip(chars, toks))
    else:
        pairs = [(c, '') for c in chars]
    for ch, tok in pairs:
        cands = pinyin(ch, style=Style.NORMAL, heteronym=True)[0] or pinyin(ch, style=Style.NORMAL)
        best, bs = None, -1
        for c in cands:
            base = py_one(c)
            if not base:
                continue
            if not tok:
                s = 1.0
            else:
                s = SequenceMatcher(None, _norm_wg(c), _norm_wg(tok)).ratio()
            if s > bs:
                best, bs = c, s
        out.append(py_one(best) if best else ch)
    return ''.join(out)


def build(raw_dir='raw'):
    names = {}
    for t in TEAMS:
        zh = json.load(open(os.path.join(raw_dir, 'roster_%s_zh.json' % t), encoding='utf-8'))
        enl = json.load(open(os.path.join(raw_dir, 'roster_%s_en.json' % t), encoding='utf-8'))
        en = {x['acnt']: x['name'] for x in enl}
        for x in zh:
            hz, rom = x['name'], en.get(x['acnt'], '')
            if hz in KO:
                ko = KO[hz]
            else:
                # 일본 팀에 있는 대만 선수(예: 黃錦豪)는 한자 병음으로
                is_zh = False
                if t in JP_TEAMS and rom:
                    first = pinyin([c for c in hz if '\u4e00' <= c <= '\u9fff'][0], style=Style.NORMAL)[0][0]
                    is_zh = SequenceMatcher(None, _norm_wg(first), _norm_wg(rom.split()[0])).ratio() > 0.7
                if t in JP_TEAMS and not is_zh:
                    ko = jp_name(rom) if rom else zh_name(hz)
                else:
                    ko = zh_name_match(hz, rom) or zh_name(hz)
            names[x['acnt']] = {'zh': hz, 'en': rom, 'ko': ko, 'team': t,
                                'no': x['no'], 'pos': x['pos']}
    return names


if __name__ == '__main__':
    n = build()
    json.dump(n, open('names.json', 'w'), ensure_ascii=False, indent=0)
    print(len(n))
    for k in list(n)[:0]:
        pass
    # 눈검사용 샘플
    for k, v in n.items():
        if v['team'] in ('ZZZ040', 'ZZZ083', 'ZZZ389', 'ZZZ409', 'ZZZ379'):
            print(v['team'], v['no'], v['zh'], '|', v['en'], '->', v['ko'])
