# KBO Pro Analyst Studio — live data

KBO 분석 스튜디오 앱(v21.0 이상)이 열릴 때 자동으로 읽는 데이터 패치입니다.

- `data/live_patch.json` — 본문(JSON). 앱은 `raw.githubusercontent.com` 에서 직접 읽습니다.
- `data/live_patch.js` — 같은 내용을 `window.V210_RECEIVE(...)` 로 감싼 사본.
  (파일을 `file://` 로 열었을 때 브라우저가 fetch 를 막는 경우의 대체 로더용)

## 갱신 방법

1. 아래 항목만 덮어쓰면 앱이 다음에 열릴 때 반영합니다. 빈 배열은 "변경 없음"입니다.
2. `updated_at` 을 반드시 갱신합니다.
3. 확인된 공식 발표만 적습니다(추정·가상 값 금지).

```json
{
  "schema_version": 1,
  "app_version": "v21.0",
  "updated_at": "2026-11-21T09:45:00+09:00",
  "data_through": "2026-11-21",
  "player_patches": [
    { "pid": "68242", "name": "정철원", "league": "KBO1",
      "team": "키움", "status": "트레이드", "number": "",
      "prev_team": "롯데", "move_date": "2026-11-20", "move_note": "…" }
  ],
  "notices": [
    { "date": "2026-11-20", "team": "롯데↔키움", "type": "트레이드",
      "player": "[오피셜] 정철원 ↔ 임지열 1대1 트레이드", "detail": "…", "src": "…" }
  ],
  "games": [
    { "pool": "practice", "id": "practice_20261121_LOTDOO", "add": true,
      "data": { "date": "11.21(토)", "date_iso": "20261121", "time": "13:00",
                "away": "롯데", "home": "두산", "as": 4, "hs": 7, "status": "종료" } }
  ],
  "ai_facts": [
    { "id": "fa2027-yang", "date": "2026-11-17", "keywords": ["양의지"],
      "label": "2027 FA 계약", "text": "두산 잔류 · 2년 최대 55억", "src": "두산 보도자료" }
  ]
}
```

- `player_patches` 는 `pid` 단독 매칭입니다. 같은 `pid` 가 1군·퓨처스에 함께 있으면 `league`(`KBO1`/`FUTURES`)로 구분합니다.
  `career[]`(과거 시즌 소속)는 건드리지 않으므로 2026 시즌 소속 기준 팀 집계(v20.8)는 그대로 유지됩니다.
- `notices` 는 `date`+`player` 로 중복을 막습니다.
- `games` 의 `pool` 은 `kbo1` · `futures` · `practice` · `intl` 이고, `id` 가 있으면 그 경기를 갱신, 없으면 `add:true` 일 때 추가합니다.
- `ai_facts` 는 `keywords` 가 모두 들어간 질문에 AI 비서 답변 아래에 한 줄로 붙습니다.
