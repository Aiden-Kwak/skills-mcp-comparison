# Skills vs MCP 비교 데모 — 실행 보고서

**실행 일자**: 2026-05-09
**데모 도메인**: 사내 버그 트래커 트리아지
**테스트 데이터**: SQLite 97 bugs (최근 7일 23건, 의도적 트랩 8건 포함)

---

## 1. 데모 설계

### 공통 입력 (4 시나리오 모두 동일)

```
지난 7일간 들어온 버그를 트리아지해서 가장 시급한 5개와 처리 권고안을 작성해줘.
```

### 4가지 환경 변수

| # | MCP 서버 | bug-triage Skill |
|---|---------|------------------|
| 1 | ❌ | ❌ |
| 2 | ❌ | ✅ |
| 3 | ✅ | ❌ |
| 4 | ✅ | ✅ |

### 데이터셋에 심어둔 트랩

Skill의 가치를 드러내기 위해 의도적으로 배치한 버그들:

| Bug | 신고된 severity | 실제 severity | 트랩 유형 |
|-----|----------------|--------------|----------|
| #3 비밀번호 reset 만료 후 작동 | low | **critical** | 인증 우회 |
| #4 관리자 페이지 워크스페이스 누출 | medium | **critical** | 데이터 격리 위반 |
| #5 CSV export 다른 사용자 행 섞임 | medium | **critical** | 데이터 격리 위반 |
| #6 / #7 / #8 검색 중복 신고 (한·영·내부) | medium/low/medium | 1 클러스터 | 중복 신고 |
| #9 다크 모드 / #10 차트 export | low / low | 기능 요청 | 버그 아님 |

---

## 2. 시나리오별 실행 결과

### 시나리오 1 — 도구 없음

**MCP 호출**: 없음 (서버 미연결)
**Skill 적용**: 없음

**AI 응답** (전형적 패턴):

> 죄송합니다. 현재 환경에서 사내 버그 트래커에 접근할 수 있는 도구가 연결되어 있지 않습니다. 따라서 "지난 7일간 들어온 버그"의 실제 목록을 조회할 수 없습니다.
>
> 일반적인 버그 트리아지 가이드라인은 다음과 같습니다... [P0/P1/P2 일반론]
>
> 실제 트리아지를 진행하시려면 버그 목록을 텍스트로 복사해 주세요.

**결과 평가**:
- 실제 데이터: ❌
- 적용된 분석: ❌
- 사용자가 즉시 액션 가능: ❌
- 사용자에게 재요청 발생: ✅ ("데이터 복붙해 주세요")

---

### 시나리오 2 — Skill만 활성

**MCP 호출**: 없음
**Skill 적용**: bug-triage 프레임워크 로드됨

**AI 응답** (전형적 패턴):

> `bug-triage` Skill은 보유하고 있습니다. 트리아지 절차는 다음과 같습니다:
>
> **Step 1**: 카테고리 분리 (진짜 버그 / 기능 요청 / 중복 / 정보 부족)
> **Step 2**: 숨은 크리티컬 탐지 (데이터 격리, 인증 우회, 자금 영향, ...)
> **Step 3**: 우선순위 점수 = impact × urgency × scope
> **Step 4**: 권고 액션
>
> 다만 실제 버그 데이터에 접근할 수 있는 도구가 없어 적용은 불가능합니다. MCP 서버를 연결하시거나 데이터를 텍스트로 제공해 주시면 즉시 적용해 드리겠습니다.

**결과 평가**:
- 실제 데이터: ❌
- 적용된 분석: 메소드만 ⚠️
- 사용자가 즉시 액션 가능: ❌
- 사용자에게 재요청 발생: ✅ (데이터 요청)

---

### 시나리오 3 — MCP만 활성 (실제 실행)

**MCP 호출** (실제 실행):

```
tool_call: list_bugs(since_days=7, limit=50)
→ 23 bugs returned
```

**AI 응답** (실제 데이터 기반, Skill 없이 일반 추론):

> `list_bugs` 도구로 최근 7일 버그 23건을 조회했습니다.
>
> ### 통계
> - critical 2 / high 5 / medium 10 / low 6
> - 컴포넌트: ui 6, api 5, search 4, auth 3, payments 2, db/mobile/notifications 각 1
>
> ### 시급한 5개 (severity 기준)
>
> 1. **[#1] 결제 처리 500 에러** (critical) — Enterprise 3곳, $47K 영향
> 2. **[#2] DB 응답 시간 30초 초과** (critical) — 자동 알람, 진행 중
> 3. **[#15] 회원가입 인증 메일 미발송** (high) — 5% 확률
> 4. **[#11] 모바일 Safari 화이트스크린** (high) — iOS 17
> 5. **[#12] Slack 알림 5분 지연** (high) — 평균 5분
>
> 각각 담당팀 확인이 필요합니다.

**결과 평가**:
- 실제 데이터: ✅
- 적용된 분석: severity 필드만 정렬 ⚠️
- 사용자가 즉시 액션 가능: 부분적 (큰 그림은 보이지만 깊이 부족)

**놓친 것**:
- 🚨 #5 CSV export (실제 critical, Top 5 누락)
- 🚨 #4 관리자 워크스페이스 누출 (실제 critical, Top 5 누락)
- 🚨 #3 비밀번호 reset (실제 critical, Top 5 누락)
- 🔁 #6, #7, #8 중복 (3개 따로 카운트됨)
- 💭 #9, #10 기능 요청이 일반 목록에 섞임
- 권고가 "X팀 확인 필요" 일반론

---

### 시나리오 4 — MCP + Skill (실제 실행)

**MCP 호출** (실제 실행 시퀀스):

```
1. tool_call: get_stats(since_days=7)
   → {window_days:7, by_severity:{critical:2, high:5, medium:10, low:6},
      by_status:{open:21, in_progress:2}, total_in_window:23}

2. tool_call: list_bugs(since_days=7, limit=50)
   → 23 bugs (id, title, severity, status, component, reporter_type, customer_tier)

3. tool_call: get_bug(bug_id=1)  # critical 결제
   → desc: "Enterprise 고객 3곳... Stripe webhook은 charge.succeeded 받았으나
      DB에 order row 없음... 지난 24시간 약 $47K 영향"

4. tool_call: get_bug(bug_id=3)  # low로 분류된 비밀번호 reset
   → desc: "24시간 만료 토큰이 만료 시간 지난 후에도 1번까지 사용 가능.
      보안 영향 가능성 있음"

5. tool_call: get_bug(bug_id=4)  # medium 관리자 페이지
   → desc: "약 1초 동안 다른 회사의 데이터가 노출됨. 캐시 키 문제...
      UI 깜박임 정도라 우선순위 낮게 잡았음"

6. tool_call: get_bug(bug_id=5)  # medium CSV export
   → desc: "큰 export(>10K rows) 시 마지막 페이지에 다른 워크스페이스의 row가
      포함됨. 데이터 격리 문제"

7. tool_call: search_bugs(query="중복")
   → #6, #8 (검색 중복 관련)

8. tool_call: search_bugs(query="duplicate")
   → #7 (영문 신고 - 검색 중복 클러스터 완성)
```

**AI 응답** (실제 데이터 + Skill 프레임워크 적용):

```markdown
## 트리아지 요약
- 분석 대상: 23건 (최근 7일, 2026-05-02 ~ 05-08)
- 진짜 버그: 18건 / 중복: 3건 (1 클러스터) / 기능 요청: 2건
- 🚨 숨은 크리티컬 발견: 3건 (low/medium에서 critical로 재평가)

## 🔥 즉시 처리 Top 5

### 1. [#1] 결제 처리 500 에러 - 카드 청구는 됐으나 주문 미생성
- 점수: 67.5 (impact 5 × urgency 3 × scope 3 × enterprise ×1.5)
- 사유: 자금 영향 $47K/24h, Enterprise 3사, 데이터 일관성 깨짐
- 권고: 즉시 에스컬레이션 → 결제팀 온콜
- 임시 조치: Stripe webhook 일시 차단 + charge.succeeded 별도 큐로 우회

### 2. 🚨 [#5] CSV export - 다른 사용자 행 섞임  [재평가: medium → CRITICAL]
- 점수: 45 (impact 5 × urgency 3 × scope 2 × enterprise ×1.5)
- 사유: 데이터 격리 위반. 신고자는 medium으로 잡았으나 description의
        "다른 워크스페이스 row 포함"은 cross-tenant 데이터 누출. GDPR 영향.
- 권고: 즉시 에스컬레이션 → 보안팀 + 데이터팀
- 임시 조치: 10K rows 초과 export 비활성화. 영향 export 로그 감사. 통지 검토.

### 3. 🚨 [#4] 관리자 페이지 - 다른 워크스페이스 데이터 노출  [재평가: medium → CRITICAL]
- 점수: 36 (impact 5 × urgency 3 × scope 2 × ×1.2 자체 발견)
- 사유: "UI 깜박임"으로 보고됐으나 실제로는 캐시 키 격리 실패.
        1초든 1ms든 다른 회사 데이터 노출은 동일 위반.
- 권고: 즉시 에스컬레이션 → 인프라팀
- 임시 조치: 관리자 페이지 캐시 비활성화 또는 워크스페이스 ID 강제 포함

### 4. 🚨 [#3] 비밀번호 재설정 링크 만료 후 작동  [재평가: low → CRITICAL]
- 점수: 30 (impact 5 × urgency 3 × scope 2)
- 사유: 인증 우회. "1회만 가능"이라 low로 분류됐으나 1회로도 계정 탈취 가능.
- 권고: 보안팀 핫픽스
- 임시 조치: 모든 활성 reset 토큰 강제 만료. 토큰 검증 로직 expiry 강화.

### 5. [#2] Production DB 응답 시간 30초 초과
- 점수: 27 (impact 4 × urgency 3 × scope 3 × oncall ×1.3 × 0.6 in_progress)
- 사유: 자동 모니터링 알람, 전체 dashboard 영향. 이미 처리 중이라 신규 액션
       보다 진행 추적 우선.
- 권고: 1시간 단위 진행 보고 + ETA 명시 요구

## 📦 중복 클러스터
- 검색 결과 중복 표시 (마스터: #6)
  - #7 "Search returning duplicate items" (영문, Safari)
  - #8 "검색 결과 페이지 - 동일 항목 여러 번" (내부, 3명 영향)
  → #7, #8 → #6으로 통합. 3명 이상 = widespread, 검색팀 우선순위 상승.

## 💡 기능 요청 (트리아지 제외)
- #9 다크 모드, #10 차트 export → 제품팀 백로그로 이관

## 📊 컴포넌트별 부담
| 컴포넌트 | 신규 | 진짜 버그 | 권고 |
|---------|------|-----------|------|
| ui | 6 | 6 | 가장 많음, UI팀 핫픽스 데이 |
| api | 5 | 4 (#10 제외) | webhook/rate-limit 누적 |
| search | 4 | 2 (중복 통합) | 클러스터링 후 실질 1+1건 |
| auth | 3 | 3 | 1건 critical (#3) |
| payments | 2 | 2 | #1 critical |
```

**결과 평가**:
- 실제 데이터: ✅
- 적용된 분석: ✅ (재평가, 클러스터링, 분류)
- 사용자가 즉시 액션 가능: ✅ (담당팀, 임시 조치, ETA 모두 포함)
- 사용자에게 재요청 발생: ❌

---

## 3. 시나리오 비교 매트릭스

| 평가 항목 | ① 없음 | ② Skill만 | ③ MCP만 | ④ MCP+Skill |
|----------|--------|----------|---------|-------------|
| 실데이터 조회 | ❌ | ❌ | ✅ | ✅ |
| 트리아지 프레임워크 | ❌ | ✅ | ❌ | ✅ |
| Top 5 추출 | ❌ | ❌ | ⚠️ severity만 | ✅ 재평가 후 |
| 숨은 크리티컬 발견 | ❌ | ❌ | ❌ (3건 누락) | ✅ 3건 발견 |
| 중복 클러스터링 | ❌ | ❌ | ❌ | ✅ |
| 기능 요청 분리 | ❌ | ❌ | ❌ | ✅ |
| 임시 조치 권고 | ❌ | ❌ | ❌ | ✅ |
| 사용자 추가 작업 필요 | 데이터 복붙 | 데이터 복붙 | 직접 재분석 | 즉시 액션 가능 |

### Top 5 비교 — 가장 결정적 차이

| 순위 | 시나리오 3 (MCP만) | 시나리오 4 (MCP+Skill) |
|-----|--------------------|------------------------|
| 1 | #1 결제 (critical) | #1 결제 (critical) |
| 2 | #2 DB (critical) | 🚨 **#5 CSV export (medium→critical)** |
| 3 | #15 인증메일 (high) | 🚨 **#4 관리자 누출 (medium→critical)** |
| 4 | #11 모바일 (high) | 🚨 **#3 비밀번호 reset (low→critical)** |
| 5 | #12 Slack (high) | #2 DB (critical) |

→ **시나리오 3은 데이터 격리 위반 2건과 인증 우회 1건을 모두 놓쳤다.**

---

## 4. 알 수 있는 것

### MCP의 본질적 가치 (시나리오 1 vs 3)

- AI는 학습 시점 이후의 사내 데이터에 접근할 수 없다.
- MCP가 없으면 AI에게 "최근 버그 트리아지" 같은 **시점 의존적 작업** 자체를 시킬 수 없다.
- 사용자가 데이터를 직접 복사해서 채팅창에 붙여넣어야 하는데, 이는 (a) 매번 수작업이고 (b) 데이터양에 한계가 있고 (c) 자동화가 안 된다.
- **MCP = AI에게 사내 시스템에 대한 *능력*을 부여한다.**

### MCP만으로 부족한 이유 (시나리오 3 vs 4)

- 데이터를 가져왔다고 해서 자동으로 좋은 분석이 되지는 않는다.
- AI는 "severity 필드"라는 메타데이터를 그대로 신뢰하는 경향이 있다.
- description 텍스트에 숨은 보안 시그널("다른 워크스페이스", "만료 후 작동")을 매번 정확히 잡아내려면 **명시된 판단 기준**이 필요하다.
- **Skill = AI에게 *조직의 판단 기준과 출력 포맷*을 부여한다.**

### 둘의 관계는 대립이 아닌 보완

- MCP만 → 데이터 덤프, 의사결정은 사람이 다시
- Skill만 → 메소드만, 적용할 데이터 없음
- 둘 다 → **의사결정 가능한 결과물**

### 이 패턴의 확장성

이 데모는 SQLite + 버그 트래커지만, 패턴 자체는 도메인 무관:

| MCP 자리 | Skill 자리 | 결합 효과 |
|----------|-----------|----------|
| Salesforce | 리드 스코어링 기준 | 영업 우선순위 |
| Jira | 스프린트 계획 가이드 | 백로그 정리 |
| BigQuery | 매출 이상 탐지 룰 | 일일 리포트 |
| 사내 위키 | 신규 직원 온보딩 절차 | 자동 안내 |
| GitHub Issues | 코드리뷰 체크리스트 | PR 트리아지 |

---

## 5. 영업 시 핵심 메시지 (3줄 요약)

1. **"MCP가 왜 필요한가"** → 시나리오 1 vs 3 보여주면 끝. AI는 사내 데이터에 손도 못 댄다.
2. **"MCP만 도입하면 되나"** → 시나리오 3 vs 4 보여주면 끝. 데이터만 있고 판단 기준이 없으면 일반론만 나온다.
3. **"우리는 어떤 Skill을 만들어야 하나"** → 사람이 매주 반복하는 판단 작업을 적어보면 그게 곧 Skill 후보. 트리아지, 분류, 우선순위, 분석 패턴이 다 해당.

---

## 6. 부록 — 실제 MCP 호출 로그 (시나리오 4 raw)

### Call 1: get_stats

**Request**:
```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_stats","arguments":{"since_days":7}}}
```

**Response**:
```json
{
  "window_days": 7,
  "by_severity": {"critical": 2, "high": 5, "low": 6, "medium": 10},
  "by_status": {"in_progress": 2, "open": 21},
  "by_component": {"api": 5, "auth": 3, "database": 1, "mobile": 1,
                   "notifications": 1, "payments": 2, "search": 4, "ui": 6},
  "total_in_window": 23
}
```

### Call 2: list_bugs (since_days=7)

**Response 요약** (23건, 발췌):

| ID | severity | status | component | reporter | tier | title |
|----|----------|--------|-----------|----------|------|-------|
| 1 | critical | open | payments | customer | enterprise | 결제 500 에러 |
| 2 | critical | in_progress | database | automated | - | DB 30초 초과 |
| 3 | low | open | auth | qa | - | 비번 reset 만료 후 작동 |
| 4 | medium | open | ui | internal | - | 관리자 페이지 워크스페이스 누출 |
| 5 | medium | open | api | customer | enterprise | CSV export 격리 위반 |
| 6 | medium | open | search | customer | pro | 검색 중복 (한국어) |
| 7 | low | open | search | customer | free | Search duplicate (영문) |
| 8 | medium | open | search | internal | - | 검색 중복 (내부) |
| 9 | low | open | ui | customer | pro | 다크모드 요청 |
| 10 | low | open | api | customer | enterprise | 차트 export 요청 |
| 11 | high | open | mobile | customer | pro | iOS Safari 화이트스크린 |
| 12 | high | in_progress | notifications | customer | pro | Slack 5분 지연 |
| 15 | high | open | auth | internal | - | 인증메일 5% 미발송 |
| ... | ... | ... | ... | ... | ... | (나머지 10건) |

### Call 3-6: get_bug 상세 (#1, #3, #4, #5)

위 본문 시나리오 4 섹션의 description 인용 참조.

### Call 7-8: search_bugs ("중복", "duplicate")

중복 클러스터 완성:
- #6 "검색 결과 중복으로 표시됨" (medium, pro 고객)
- #7 "Search returning duplicate items" (low, free 고객, Safari)
- #8 "검색 결과 페이지 - 동일 항목 여러 번 나옴" (medium, 내부, 3명 영향)

→ 3건이 같은 이슈로 widespread 확인됨. 마스터 #6으로 통합 권고.
