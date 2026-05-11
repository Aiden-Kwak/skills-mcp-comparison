"""
Seeds bugs.db with realistic SaaS bug data for the Skills vs MCP demo.

Design intent:
- ~100 bugs across 30 days
- Mix of clearly-critical, hidden-critical (mislabeled), duplicates, and feature-requests
- The triage Skill should be able to detect mislabels and duplicates from descriptions
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "bugs.db"

SCHEMA = """
CREATE TABLE bugs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    component TEXT NOT NULL,
    reporter TEXT NOT NULL,
    reporter_type TEXT NOT NULL,
    customer_tier TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX idx_status ON bugs(status);
CREATE INDEX idx_severity ON bugs(severity);
CREATE INDEX idx_component ON bugs(component);
CREATE INDEX idx_created_at ON bugs(created_at);
"""

# Hand-crafted bugs designed to expose Skill value
# Recent ones (last 7 days) are what the demo will query
NOW = datetime(2026, 5, 8, 14, 0, 0)

CURATED_BUGS = [
    # === 명백한 크리티컬 (Skill이 식별 잘 함) ===
    {
        "title": "결제 처리 중 500 에러 - 카드 청구는 됐으나 주문 미생성",
        "description": "Enterprise 고객 3곳에서 동일 증상 보고. Stripe webhook은 charge.succeeded 받았으나 우리 DB에 order row 없음. 환불 처리 수동으로 진행 중. 지난 24시간 약 $47K 영향.",
        "severity": "critical", "status": "open", "component": "payments",
        "reporter": "support@acme.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 1,
    },
    {
        "title": "Production DB 응답 시간 30초 이상 - 일부 쿼리 timeout",
        "description": "오후 3시부터 /api/dashboard 엔드포인트 응답 P95가 30초 초과. 고객 대시보드 로딩 실패 다수.",
        "severity": "critical", "status": "in_progress", "component": "database",
        "reporter": "oncall-bot", "reporter_type": "automated", "customer_tier": None,
        "days_ago": 2,
    },

    # === 숨은 크리티컬 (low/medium으로 잘못 분류된 보안/데이터 이슈 - Skill이 잡아내야 함) ===
    {
        "title": "비밀번호 재설정 링크가 만료 후에도 작동",
        "description": "QA에서 발견. 24시간 만료 토큰이 만료 시간 지난 후에도 1번까지 사용 가능. 보안 영향 가능성 있음.",
        "severity": "low", "status": "open", "component": "auth",
        "reporter": "qa-team", "reporter_type": "qa", "customer_tier": None,
        "days_ago": 3,
    },
    {
        "title": "관리자 페이지에서 다른 워크스페이스 데이터가 잠깐 보임",
        "description": "Admin 사용자가 새로고침 시 약 1초 동안 다른 회사의 데이터가 노출됨. 캐시 키 문제로 보임. UI 깜박임 정도라 우선순위 낮게 잡았음.",
        "severity": "medium", "status": "open", "component": "ui",
        "reporter": "internal-admin", "reporter_type": "internal", "customer_tier": None,
        "days_ago": 2,
    },
    {
        "title": "CSV export 시 다른 사용자 행이 1~2개 섞임",
        "description": "재현 가능. 큰 export(>10K rows) 시 마지막 페이지에 다른 워크스페이스의 row가 포함됨. 데이터 격리 문제.",
        "severity": "medium", "status": "open", "component": "api",
        "reporter": "support@globex.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 4,
    },

    # === 중복 (Skill이 묶어내야 함) ===
    {
        "title": "검색 결과 중복으로 표시됨",
        "description": "검색하면 같은 결과가 2~3번씩 나옴. Chrome 최신 버전.",
        "severity": "medium", "status": "open", "component": "search",
        "reporter": "user1@startup.io", "reporter_type": "customer", "customer_tier": "pro",
        "days_ago": 5,
    },
    {
        "title": "Search returning duplicate items",
        "description": "Same item appears 2 or 3 times in search results. Started this week. Using Safari.",
        "severity": "low", "status": "open", "component": "search",
        "reporter": "user2@otherco.com", "reporter_type": "customer", "customer_tier": "free",
        "days_ago": 4,
    },
    {
        "title": "검색 결과 페이지 - 동일 항목 여러 번 나옴",
        "description": "고객 3명에게서 같은 보고. 검색 후 결과 리스트에 중복 표시.",
        "severity": "medium", "status": "open", "component": "search",
        "reporter": "support-team", "reporter_type": "internal", "customer_tier": None,
        "days_ago": 3,
    },

    # === 사실 기능 요청 (Skill이 트리아지에서 분리해야 함) ===
    {
        "title": "다크 모드가 없어서 불편함",
        "description": "다크 모드 옵션이 있으면 좋겠습니다. 밤에 작업할 때 눈이 아픕니다.",
        "severity": "low", "status": "open", "component": "ui",
        "reporter": "user3@design.co", "reporter_type": "customer", "customer_tier": "pro",
        "days_ago": 6,
    },
    {
        "title": "엑셀 내보내기에 차트도 포함되었으면",
        "description": "현재 CSV로만 내보내짐. 차트 이미지도 같이 export 되면 좋겠음.",
        "severity": "low", "status": "open", "component": "api",
        "reporter": "user4@bigcorp.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 5,
    },

    # === 일반적 high/medium ===
    {
        "title": "모바일 Safari에서 로그인 후 화이트 스크린",
        "description": "iOS 17 Safari. 로그인 성공 후 대시보드 라우팅에서 흰 화면. 새로고침하면 정상.",
        "severity": "high", "status": "open", "component": "mobile",
        "reporter": "user5@mobile.io", "reporter_type": "customer", "customer_tier": "pro",
        "days_ago": 2,
    },
    {
        "title": "Slack 알림이 약 5분 지연",
        "description": "@channel 알림이 평균 5분 지연 발생. 작업 코멘트도 동일.",
        "severity": "high", "status": "in_progress", "component": "notifications",
        "reporter": "support@techstart.io", "reporter_type": "customer", "customer_tier": "pro",
        "days_ago": 4,
    },
    {
        "title": "대시보드 차트에서 0 값이 누락됨",
        "description": "일별 매출 차트에 매출 0인 날짜가 빠져서 그래프가 잘못 보임.",
        "severity": "medium", "status": "open", "component": "ui",
        "reporter": "qa-team", "reporter_type": "qa", "customer_tier": None,
        "days_ago": 3,
    },
    {
        "title": "API rate limit 헤더가 잘못된 값 반환",
        "description": "X-RateLimit-Remaining이 항상 999 반환. 실제 limit은 100/분.",
        "severity": "medium", "status": "open", "component": "api",
        "reporter": "developer@partner.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 6,
    },
    {
        "title": "회원가입 시 이메일 검증 메일 가끔 안 옴",
        "description": "약 5% 확률로 가입 인증 메일 미발송. SendGrid 로그상 발송은 됨. 스팸함도 아님.",
        "severity": "high", "status": "open", "component": "auth",
        "reporter": "support-team", "reporter_type": "internal", "customer_tier": None,
        "days_ago": 1,
    },
    {
        "title": "검색 결과 정렬이 가끔 무작위로 보임",
        "description": "정렬 기준 '최신순' 선택해도 가끔 옛날 결과가 위로 옴.",
        "severity": "medium", "status": "open", "component": "search",
        "reporter": "user6@misc.com", "reporter_type": "customer", "customer_tier": "free",
        "days_ago": 5,
    },
    {
        "title": "결제 내역 페이지 페이지네이션 깨짐",
        "description": "다음 페이지 클릭하면 항상 빈 결과. URL은 page=2로 변경됨.",
        "severity": "medium", "status": "open", "component": "payments",
        "reporter": "user7@cust.com", "reporter_type": "customer", "customer_tier": "pro",
        "days_ago": 4,
    },
    {
        "title": "툴팁 위치가 우측 상단에서 잘림",
        "description": "헤더 메뉴에 마우스 올렸을 때 툴팁이 화면 밖으로 나감.",
        "severity": "low", "status": "open", "component": "ui",
        "reporter": "qa-team", "reporter_type": "qa", "customer_tier": None,
        "days_ago": 7,
    },
    {
        "title": "데이터 임포트 진행률 표시가 100%에서 멈춤",
        "description": "임포트 완료 됐는데 진행률 바가 100%에서 사라지지 않음. 새로고침하면 정상.",
        "severity": "low", "status": "open", "component": "ui",
        "reporter": "user8@data.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 6,
    },
    {
        "title": "Webhook 재시도 로직이 동작 안 함",
        "description": "Webhook 실패 시 3회 재시도 명세인데 1회만 시도하고 멈춤.",
        "severity": "high", "status": "open", "component": "api",
        "reporter": "developer@integ.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 3,
    },
    {
        "title": "프로필 사진 업로드 후 캐시 갱신 안 됨",
        "description": "업로드 성공해도 페이지에 옛날 사진 보임. 강제 새로고침하면 보임.",
        "severity": "low", "status": "open", "component": "ui",
        "reporter": "user9@profile.com", "reporter_type": "customer", "customer_tier": "free",
        "days_ago": 7,
    },
    {
        "title": "작업 댓글에 @멘션이 alphabetical 정렬 안 됨",
        "description": "사용자 멘션 자동완성이 가나다순/abc순이 아닌 임의 순서.",
        "severity": "low", "status": "open", "component": "ui",
        "reporter": "user10@team.io", "reporter_type": "customer", "customer_tier": "pro",
        "days_ago": 5,
    },
    {
        "title": "통합 페이지에서 GitHub 연결 끊기 버튼 작동 안 함",
        "description": "Settings > Integrations > GitHub Disconnect 클릭해도 반응 없음. 콘솔 에러 없음.",
        "severity": "medium", "status": "open", "component": "ui",
        "reporter": "support-team", "reporter_type": "internal", "customer_tier": None,
        "days_ago": 2,
    },
    {
        "title": "API 응답 latency 평균 200ms → 800ms로 증가",
        "description": "지난 화요일 배포 이후 /api/v2/projects 평균 응답 시간 4배 증가. 관련 변경: ORM 쿼리 리팩토링.",
        "severity": "high", "status": "open", "component": "api",
        "reporter": "oncall-bot", "reporter_type": "automated", "customer_tier": None,
        "days_ago": 4,
    },
    {
        "title": "비밀번호 변경 후 모든 세션 로그아웃 안 됨",
        "description": "비밀번호 변경했는데 다른 디바이스의 세션이 그대로 유효. 보안 정책상 모두 로그아웃 되어야 함.",
        "severity": "medium", "status": "open", "component": "auth",
        "reporter": "qa-team", "reporter_type": "qa", "customer_tier": None,
        "days_ago": 5,
    },

    # === resolved/closed 일부 (전체 통계용) ===
    {
        "title": "초대 메일 링크 만료 시간 잘못됨",
        "description": "초대 링크가 24시간 명세인데 1시간 만에 만료. 환경변수 설정 오류.",
        "severity": "medium", "status": "resolved", "component": "auth",
        "reporter": "support-team", "reporter_type": "internal", "customer_tier": None,
        "days_ago": 8,
    },
    {
        "title": "검색 인덱싱 지연 30분 초과",
        "description": "신규 작성 항목이 검색에 30분 이상 안 잡힘.",
        "severity": "high", "status": "resolved", "component": "search",
        "reporter": "support@enterprise.com", "reporter_type": "customer", "customer_tier": "enterprise",
        "days_ago": 10,
    },
]


def random_old_bug(days_ago: int) -> dict:
    """Filler bugs to make stats realistic (older than 7 days, mostly resolved/closed)."""
    components = ["auth", "payments", "search", "ui", "api", "database", "notifications", "mobile"]
    severities = ["low", "low", "low", "medium", "medium", "high"]
    statuses = ["resolved", "resolved", "closed", "closed", "in_progress"]
    reporters = [
        ("user@cust.com", "customer", random.choice(["free", "pro", "enterprise"])),
        ("qa-team", "qa", None),
        ("oncall-bot", "automated", None),
        ("support-team", "internal", None),
    ]
    rep, rep_type, tier = random.choice(reporters)
    return {
        "title": f"[Old bug #{random.randint(1000,9999)}] sample issue",
        "description": "Filler bug for realistic distribution. Not used in 7-day demo window.",
        "severity": random.choice(severities),
        "status": random.choice(statuses),
        "component": random.choice(components),
        "reporter": rep,
        "reporter_type": rep_type,
        "customer_tier": tier,
        "days_ago": days_ago,
    }


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    rows = []
    for bug in CURATED_BUGS:
        created = NOW - timedelta(days=bug["days_ago"], hours=random.randint(0, 23))
        updated = created + timedelta(hours=random.randint(0, 24))
        rows.append((
            bug["title"], bug["description"], bug["severity"], bug["status"],
            bug["component"], bug["reporter"], bug["reporter_type"],
            bug["customer_tier"], created.isoformat(), updated.isoformat(),
        ))

    # Filler old bugs (8~30 days ago)
    random.seed(42)
    for _ in range(70):
        bug = random_old_bug(random.randint(8, 30))
        created = NOW - timedelta(days=bug["days_ago"], hours=random.randint(0, 23))
        updated = created + timedelta(hours=random.randint(0, 48))
        rows.append((
            bug["title"], bug["description"], bug["severity"], bug["status"],
            bug["component"], bug["reporter"], bug["reporter_type"],
            bug["customer_tier"], created.isoformat(), updated.isoformat(),
        ))

    conn.executemany(
        "INSERT INTO bugs (title, description, severity, status, component, reporter, reporter_type, customer_tier, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()

    cur = conn.execute("SELECT COUNT(*) FROM bugs")
    total = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM bugs WHERE created_at >= ?", ((NOW - timedelta(days=7)).isoformat(),))
    recent = cur.fetchone()[0]
    print(f"Seeded {total} bugs ({recent} in last 7 days) to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
