"""Print a demo-friendly summary of the seeded bugs.db.

Used during recordings to make it clear to the audience that the dataset is
synthetic and what kinds of patterns are intentionally embedded.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "bugs.db"

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📊  데모용 시드 데이터셋 (Synthetic Dataset for Demo)              ║
║                                                                  ║
║   ⚠️  실제 운영 데이터 아님 — SQLite 파일에 직접 입력한 가상 버그       ║
║   📁  /data/bugs.db  ←  /data/seed_db.py 로 생성                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

def main():
    print(BANNER)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) c FROM bugs").fetchone()["c"]
    recent = conn.execute(
        "SELECT COUNT(*) c FROM bugs WHERE created_at >= '2026-05-01'"
    ).fetchone()["c"]

    print(f"  총 버그 건수      : {total}건")
    print(f"  데모 대상 (7일)   : {recent}건")
    print()

    print("  ─── 신고된 severity 분포 (7일) ───")
    rows = conn.execute(
        "SELECT severity, COUNT(*) c FROM bugs "
        "WHERE created_at >= '2026-05-01' GROUP BY severity "
        "ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
        "         WHEN 'medium' THEN 3 ELSE 4 END"
    ).fetchall()
    for r in rows:
        print(f"    {r['severity']:10} {'█' * r['c']} {r['c']}")
    print()

    print("  ─── 의도적으로 심어둔 트랩 ───")
    print("  (Skill이 잡아내야 진짜 가치가 드러나는 케이스)")
    print()
    traps = [
        ("#3", "low",    "🚨 critical", "비밀번호 reset 만료 후 작동",   "인증 우회"),
        ("#4", "medium", "🚨 critical", "관리자 페이지 워크스페이스 누출", "데이터 격리 위반"),
        ("#5", "medium", "🚨 critical", "CSV export 다른 사용자 행 섞임",  "데이터 격리 위반"),
        ("#6", "medium", "📦 cluster",  "검색 중복 (한국어)",             "중복 신고"),
        ("#7", "low",    "📦 cluster",  "Search duplicate (영문)",       "중복 신고"),
        ("#8", "medium", "📦 cluster",  "검색 중복 (내부 신고)",          "중복 신고"),
        ("#9", "low",    "💡 feature",  "다크 모드 요청",                "기능 요청 위장"),
        ("#10","low",    "💡 feature",  "차트 export 요청",              "기능 요청 위장"),
    ]
    print(f"  {'ID':5} {'신고':8} → {'실제':14} {'제목':38} {'유형'}")
    print(f"  {'-'*5} {'-'*8}   {'-'*14} {'-'*38} {'-'*16}")
    for tid, reported, actual, title, kind in traps:
        print(f"  {tid:5} {reported:8} → {actual:14} {title:38} {kind}")
    print()
    print("  ─── 핵심 메시지 ───")
    print("  • 신고된 severity 만 보면 #3, #4, #5는 Top 5에 못 들어감")
    print("  • Skill이 description을 읽고 패턴을 매칭해야 critical 재평가 가능")
    print("  • #6/#7/#8은 같은 이슈를 한·영·내부에서 따로 신고 → 클러스터링 필요")
    print("  • #9/#10은 사실 기능 요청 → 트리아지에서 분리해야 함")
    print()
    conn.close()


if __name__ == "__main__":
    main()
