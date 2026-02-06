#!/usr/bin/env bash
# ============================================================================
# LinkedIn MCP — ChatGPT POC Validation Script
#
# Usage:
#   chmod +x test_poc.sh
#   ./test_poc.sh [BASE_URL]
#
# Default BASE_URL: http://localhost:8000
# ============================================================================

BASE="${1:-http://localhost:8000}"
MCP="${BASE}/mcp/"
PASS=0
FAIL=0
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

green()  { printf "\033[32m%s\033[0m\n" "$*"; }
red()    { printf "\033[31m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }

pass() { green "  PASS  $1"; PASS=$((PASS+1)); }
fail() { red   "  FAIL  $1"; FAIL=$((FAIL+1)); }

echo ""
echo "========================================"
echo " LinkedIn MCP — POC Validation"
echo " Base URL: $BASE"
echo " MCP URL:  $MCP"
echo "========================================"
echo ""

# --- 1. Health check ---
echo "--- 1. Health check ---"
curl -s "${BASE}/health" -o "$TMPDIR/health.json"
if grep -q '"status":"ok"' "$TMPDIR/health.json" 2>/dev/null; then
    pass "GET /health returns status:ok"
else
    fail "GET /health — unexpected response"
fi

# --- 2. Landing page ---
echo "--- 2. Landing page ---"
curl -s "${BASE}/" -o "$TMPDIR/landing.html"
if grep -qi 'ChatGPT POC' "$TMPDIR/landing.html" 2>/dev/null; then
    pass "GET / returns HTML with ChatGPT POC content"
else
    fail "GET / — missing ChatGPT POC content"
fi

# --- 3. Auth status ---
echo "--- 3. Auth status ---"
curl -s "${BASE}/auth/status" -o "$TMPDIR/authstatus.json"
if grep -q 'authenticated' "$TMPDIR/authstatus.json" 2>/dev/null; then
    pass "GET /auth/status returns JSON with authenticated fields"
else
    fail "GET /auth/status — unexpected response"
fi

# --- 4. /me endpoint ---
echo "--- 4. /me endpoint ---"
curl -s "${BASE}/me" -o "$TMPDIR/me.json"
if grep -q 'logged_in' "$TMPDIR/me.json" 2>/dev/null; then
    pass "GET /me returns JSON with logged_in field"
else
    fail "GET /me — unexpected response"
fi

# --- 5. Auth login ---
echo "--- 5. Auth login ---"
LOGIN_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/auth/login")
case "$LOGIN_STATUS" in
    307|302) pass "GET /auth/login returns $LOGIN_STATUS (redirect to LinkedIn)" ;;
    500)     pass "GET /auth/login returns 500 (no LINKEDIN_CLIENT_ID — expected in test)" ;;
    *)       fail "GET /auth/login returned unexpected $LOGIN_STATUS" ;;
esac

# --- 6. MCP endpoint exists ---
echo "--- 6. MCP endpoint exists ---"
MCP_GET_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/mcp")
if [ "$MCP_GET_STATUS" = "307" ]; then
    pass "GET /mcp returns 307 redirect (mount active)"
else
    fail "GET /mcp returned $MCP_GET_STATUS (expected 307)"
fi

# --- 7. MCP initialize ---
echo "--- 7. MCP initialize (JSON-RPC) ---"
curl -s -X POST "$MCP" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test-poc","version":"0.1"}}}' \
    -o "$TMPDIR/init.sse"

if grep -q 'serverInfo' "$TMPDIR/init.sse" 2>/dev/null; then
    pass "POST /mcp/ initialize returns serverInfo"
else
    fail "POST /mcp/ initialize — no serverInfo in response"
fi

if grep -q 'LinkedIn MCP' "$TMPDIR/init.sse" 2>/dev/null; then
    pass "Server name contains 'LinkedIn MCP'"
else
    fail "Server name not found in response"
fi

# --- 8. MCP tools/list ---
echo "--- 8. MCP tools/list ---"
curl -s -X POST "$MCP" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
    -o "$TMPDIR/tools.sse"

for tool in get_profile list_connections create_post search_people; do
    if grep -q "$tool" "$TMPDIR/tools.sse" 2>/dev/null; then
        pass "tools/list contains $tool"
    else
        fail "tools/list missing $tool"
    fi
done

# --- 9. MCP tool call without auth ---
echo "--- 9. Tool call without auth (should guide to login) ---"
curl -s -X POST "$MCP" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_profile","arguments":{}}}' \
    -o "$TMPDIR/toolcall.sse"

if grep -q 'login_required' "$TMPDIR/toolcall.sse" 2>/dev/null; then
    pass "get_profile without auth returns login_required"
else
    fail "get_profile without auth — no login_required in response"
fi

if grep -q '/auth/login' "$TMPDIR/toolcall.sse" 2>/dev/null; then
    pass "get_profile without auth includes login URL"
else
    fail "get_profile without auth — no login URL in response"
fi

echo ""
echo "========================================"
echo " Results: $PASS passed, $FAIL failed"
echo "========================================"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    yellow "Some tests failed. Make sure the server is running:"
    yellow "  linkedin-api"
    yellow "  # or: PYTHONPATH=src uvicorn linkedin_mcp.fastapi_app:app --port 8000"
    exit 1
fi

echo ""
green "All checks passed!"
echo ""
echo "Next steps:"
echo "  1. Open ${BASE}/auth/login in your browser to authenticate with LinkedIn"
echo "  2. Check ${BASE}/me to verify your session"
echo "  3. Connect ChatGPT to ${BASE}/mcp (No Auth connector)"
echo "  4. Try: 'Get my LinkedIn profile' in ChatGPT"
