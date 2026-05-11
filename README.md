# Skills 와 MCP: LLM 에이전트의 능력·지식 증강에 관한 통제 비교

LLM 에이전트를 보강하는 두 메커니즘 — Model Context Protocol(MCP)과 Claude *Skills* — 의 기여를 분리하기 위해, 과업과 기반 모델을 고정한 채 두 요소의 가용성만을 토글하는 자체 완결형 재현 실험.

> 시연 영상 및 관련 해설: <https://me.aiden-kwak.workers.dev/blog/mcp-vs-skills-bug-triage/>

## 초록

현대 LLM 에이전트의 증강은 대체로 직교하는 두 축을 따라 이루어진다. 하나는 **능력(capability)** 축으로, 도구 호출 프로토콜(예: MCP)을 통해 외부 시스템과 데이터에 접근할 수 있게 하는 부분이다. 다른 하나는 **지식(knowledge)** 축으로, 도메인 절차 지식을 패키징한 Skill에 해당한다. 두 축이 최종 과업 성능에 기여하는 상대적 비중은 단일 축만을 평가하는 기존 보고들에서는 충분히 드러나지 않는다. 본 저장소는 동일한 자연어 요청을 동일한 기반 모델에 대해 `{무증강}`, `{Skill만}`, `{MCP만}`, `{Skill + MCP}` 의 네 조건으로 발화하는 2×2 절제(ablation) 실험을 구현한다. 시드 버그 트래커 데이터셋에는 명목 심각도(reported severity)와 잠재 심각도(latent severity)를 구분하기 위한 패턴들이 의도적으로 삽입되어 있다. 데이터셋, 서버, Skill 정의, 조건별 기대 출력이 모두 포함되어 있다.

## 과업 정의

최근에 보고된 버그 모음이 주어졌을 때, 운영상 가장 시급한 다섯 건을 식별하고 각 건에 대해 권고 조치를 산출한다. 모든 조건에서 동일한 프롬프트를 사용한다.

> *"지난 7일간 들어온 버그를 트리아지해서 가장 시급한 5개와 처리 권고안을 작성해줘."*

## 실험 조건

| 조건 | MCP 서버 | Skill | 기대 동작 |
|---|---|---|---|
| C1 | — | — | 데이터 접근·절차 모두 부재. 거절 혹은 환각 |
| C2 | — | 있음 | 절차는 알지만 데이터 접근 불가. 추상적 방법론 응답 |
| C3 | 있음 | — | 데이터는 인출하나, 신고된 `severity` 필드에 따라 순위가 결정됨 |
| C4 | 있음 | 있음 | 잠재 크리티컬 패턴 복원, 중복 클러스터링, 기능 요청 분리 |

## 데이터셋

합성 버그 트래커를 SQLite 에 시드한다. 모든 엔티티는 가상이며 실제 운영 데이터는 사용되지 않는다.

| 항목 | 값 |
|---|---|
| 총 레코드 | 97 건 (최근 30일 윈도우) |
| 평가 윈도우 | 24 건 (최근 7일 윈도우) |
| 생성기 | `data/seed_db.py` (결정론적) |
| 저장소 | `data/bugs.db` (SQLite 3) |

여덟 건의 레코드는 C3 와 C4 의 결과를 구분짓기 위한 검정 항목으로 의도적으로 삽입되었다. 그 중 세 건은 데이터 격리 위반 또는 인증 우회 조건을 은폐하는 형태로 심각도가 과소 보고되어 있다(워크스페이스 누출, 비밀번호 reset 이후 세션 유지, CSV export 행 혼합). 세 건은 동일한 결함을 언어 변이에 따라 다중 보고한 중복 클러스터이며, 두 건은 버그로 잘못 분류된 기능 요청이다. 삽입된 패턴의 상세 명세는 `DATASET.md` 에 기술되어 있다.

## 시스템 구성

```
.
├── mcp_server/
│   └── bug_triage_server.py     # MCP 서버 (stdio JSON-RPC, 외부 의존 없음)
├── skill/
│   └── bug-triage/SKILL.md      # Skill 정의 (트리아지 절차)
├── data/
│   ├── seed_db.py               # 결정론적 시드 스크립트
│   └── bugs.db                  # 생성된 SQLite 데이터베이스
├── scenarios/
│   └── SCENARIOS.md             # 조건별 실행 프로토콜
├── expected_outputs/            # 조건별 기준 출력
│   ├── scenario_1_baseline.md
│   ├── scenario_2_skill_only.md
│   ├── scenario_3_mcp_only.md
│   └── scenario_4_both.md
├── DATASET.md                   # 데이터셋 명세 및 삽입 패턴
├── REPORT.md                    # 관측 출력에 대한 분석
└── RUNBOOK.md                   # 재현 절차
```

### MCP 서버

MCP 의 최소 표면(`initialize`, `tools/list`, `tools/call`)을 stdio JSON-RPC 위에 구현하고, SQLite 저장소에 대해 `list_bugs`, `get_bug`, `search_bugs`, `get_stats` 네 개의 도구를 노출한다. 구현은 Python 3.10+ 표준 라이브러리에만 의존한다.

### Skill

Skill 은 네 단계의 트리아지 절차를 부호화한다. (1) 카테고리 분리 — 진성 결함, 중복 신고, 기능 요청, 정보 부족 의 구분. (2) 잠재 크리티컬 탐지 — description 필드에 대한 패턴 매칭(데이터 격리 위반, 인증 우회, 자금 영향, 규제 노출). (3) 우선순위 점수 — `impact × urgency × scope` 와 신고자 유형(엔터프라이즈 고객, 모니터링 봇)에 따른 가산 계수. (4) 권고 액션 선택.

## 재현

### 사전 요건

- Python ≥ 3.10
- MCP 를 지원하는 Claude Code CLI

### 1. 데이터셋 구축

```bash
python3 data/seed_db.py
```

### 2. MCP 서버 동작 확인

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_stats","arguments":{"since_days":7}}}' \
  | python3 mcp_server/bug_triage_server.py
```

기대 응답: `total_in_window: 23`.

### 3. MCP 서버 등록

```bash
claude mcp add bug-triage -- python3 "$(pwd)/mcp_server/bug_triage_server.py"
```

또는 `.claude/settings.json` 에 직접 기재한다.

```json
{
  "mcpServers": {
    "bug-triage": {
      "command": "python3",
      "args": ["./mcp_server/bug_triage_server.py"]
    }
  }
}
```

### 4. Skill 등록

프로젝트 스코프:

```bash
mkdir -p .claude/skills
cp -r skill/bug-triage .claude/skills/
```

사용자 스코프:

```bash
mkdir -p ~/.claude/skills
cp -r skill/bug-triage ~/.claude/skills/
```

### 5. 네 조건 실행

각 조건에 대해 위 표에 따라 MCP 등록 여부와 Skill 가용성을 토글한 뒤 고정 프롬프트를 발화한다. 조건별 상세 프로토콜은 `scenarios/SCENARIOS.md` 에 기술되어 있으며, 기준 출력은 `expected_outputs/` 에 수록되어 있다.

## 결과

조건별 정성적 결과를 아래에 요약한다. 전체 트랜스크립트는 `expected_outputs/` 에 있다.

| 조건 | Top-5 에 삽입된 잠재 크리티컬(#3, #4, #5) 포함 | 중복 클러스터 식별 | 기능 요청 분리 |
|---|---|---|---|
| C1 | n/a (출력 없음) | n/a | n/a |
| C2 | n/a (데이터 접근 불가) | n/a | n/a |
| C3 | 아니오 | 아니오 | 아니오 |
| C4 | 예 | 예 | 예 |

C3 → C4 의 대비는 Skill 의 기여를 국소화한다. 데이터와 모델이 동일한 상태에서 순위 결과가 달라진다. C1 → C3 의 대비는 MCP 의 기여를 국소화한다. 절차적 추론 능력은 같은 상태에서 접근 표면만이 달라진다.

## 논의

두 증강이 동시에 활성화된 조건만이 삽입된 잠재 크리티컬을 Top-5 로 복원한다. 이는 MCP 와 Skill 을 대체 관계가 아니라 보완 관계로 보는 해석과 일치한다. MCP 는 증거를 인출할 *능력* 을, Skill 은 그 증거를 해석할 *기준* 을 제공한다. 본 과업에서 둘 중 어느 하나만으로는 충분하지 않다.

이 구조는 버그 트래커라는 기반에 한정되지 않는다. MCP 서버를 다른 시스템(Jira, Linear, GitHub Issues, 사내 데이터 웨어하우스 등) 으로 치환하고 Skill 을 다른 도메인 절차(고객 컴플레인 분류, 리드 스코어링, 이상 거래 검토 등) 로 치환하더라도 능력과 지식의 분리는 그대로 보존된다.

## 주요 파일

- `mcp_server/bug_triage_server.py` — MCP 서버 구현
- `skill/bug-triage/SKILL.md` — Skill 정의
- `data/seed_db.py` — 데이터셋 생성기
- `scenarios/SCENARIOS.md` — 조건별 실행 프로토콜
- `expected_outputs/scenario_{1..4}_*.md` — 기준 출력
- `REPORT.md` — 분석
- `RUNBOOK.md` — 재현 노트

## 라이선스

본 저장소는 연구 및 교육 목적으로 제공된다.
