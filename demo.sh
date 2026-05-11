#!/usr/bin/env bash
# Demo toggle script for Skills vs MCP comparison.
# Usage:
#   ./demo.sh skill-only   # Skill ON, MCP OFF
#   ./demo.sh both         # Skill ON, MCP ON
#   ./demo.sh off          # Skill OFF, MCP OFF (baseline)
#   ./demo.sh status       # show current state
#   ./demo.sh dataset      # show synthetic dataset summary (audience briefing)
#
# After toggling, RESTART Claude Code (exit + re-open) so it picks up the new
# .mcp.json and .claude/skills state.

set -e
cd "$(dirname "$0")"

MCP_ON=".mcp.json"
MCP_OFF=".mcp.json.off"
SKILL_ON=".claude/skills/bug-triage"
SKILL_OFF=".claude/skills/bug-triage.off"

enable_mcp()  { [ -f "$MCP_OFF" ] && mv "$MCP_OFF" "$MCP_ON"  || true; }
disable_mcp() { [ -f "$MCP_ON" ]  && mv "$MCP_ON"  "$MCP_OFF" || true; }
enable_skill()  { [ -d "$SKILL_OFF" ] && mv "$SKILL_OFF" "$SKILL_ON"  || true; }
disable_skill() { [ -d "$SKILL_ON" ]  && mv "$SKILL_ON"  "$SKILL_OFF" || true; }

mcp_state()   { [ -f "$MCP_ON" ]   && echo "ON " || echo "OFF"; }
skill_state() { [ -d "$SKILL_ON" ] && echo "ON " || echo "OFF"; }

print_status() {
  echo ""
  echo "  ┌─────────────────────────────────────────┐"
  echo "  │  bug-triage  Skill : $(skill_state)              │"
  echo "  │  bug-triage  MCP   : $(mcp_state)              │"
  echo "  └─────────────────────────────────────────┘"
  echo ""
  echo "  ⚠️  변경 후 Claude Code 세션 재시작 필요 (exit → 재진입)"
  echo ""
}

case "${1:-status}" in
  skill-only)
    enable_skill; disable_mcp
    echo "▶ Skill만 활성화"; print_status ;;
  both|all|on)
    enable_skill; enable_mcp
    echo "▶ Skill + MCP 둘 다 활성화"; print_status ;;
  off|none|baseline)
    disable_skill; disable_mcp
    echo "▶ 둘 다 비활성화 (baseline)"; print_status ;;
  status)
    echo "▶ 현재 상태"; print_status ;;
  dataset)
    python3 data/show_dataset.py ;;
  *)
    echo "Usage: $0 {skill-only | both | off | status | dataset}"
    exit 1 ;;
esac
