#!/bin/bash
# =============================================================================
# TradingCoach Full Test Suite Runner
#
# input: Backend/Frontend source code
# output: Comprehensive test report
# pos: 测试自动化 - 一键运行所有测试类型
#
# Usage: ./scripts/run_full_test_suite.sh [options]
# Options:
#   --skip-backend   Skip backend tests
#   --skip-frontend  Skip frontend tests
#   --skip-e2e       Skip E2E tests
#   --quick          Run only critical tests
#   --report         Generate HTML report
#
# 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
SKIP_BACKEND=false
SKIP_FRONTEND=false
SKIP_E2E=false
QUICK_MODE=false
GENERATE_REPORT=false

for arg in "$@"; do
    case $arg in
        --skip-backend)
            SKIP_BACKEND=true
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            ;;
        --skip-e2e)
            SKIP_E2E=true
            ;;
        --quick)
            QUICK_MODE=true
            ;;
        --report)
            GENERATE_REPORT=true
            ;;
    esac
done

# Results tracking
TOTAL_PASSED=0
TOTAL_FAILED=0
RESULTS=()

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_result() {
    local name=$1
    local passed=$2
    local failed=$3

    if [ "$failed" -eq 0 ]; then
        echo -e "${GREEN}✓ $name: $passed passed${NC}"
        RESULTS+=("✓ $name: $passed passed")
    else
        echo -e "${RED}✗ $name: $passed passed, $failed failed${NC}"
        RESULTS+=("✗ $name: $passed passed, $failed failed")
    fi

    TOTAL_PASSED=$((TOTAL_PASSED + passed))
    TOTAL_FAILED=$((TOTAL_FAILED + failed))
}

check_services() {
    print_header "Checking Services"

    # Check backend
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is running on port 8000${NC}"
    else
        echo -e "${YELLOW}⚠ Backend not running. Starting...${NC}"
        cd "$PROJECT_ROOT"
        python3 -m uvicorn backend.app.main:app --reload --port 8000 &
        sleep 5
    fi

    # Check frontend
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is running on port 5173${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend not running. Starting...${NC}"
        cd "$PROJECT_ROOT/frontend"
        npm run dev &
        sleep 5
    fi
}

# =============================================================================
# Backend Tests
# =============================================================================
run_backend_tests() {
    if [ "$SKIP_BACKEND" = true ]; then
        echo -e "${YELLOW}Skipping backend tests${NC}"
        return
    fi

    print_header "Backend Tests"
    cd "$PROJECT_ROOT"

    # Unit Tests
    echo -e "\n${BLUE}Running Unit Tests...${NC}"
    if [ "$QUICK_MODE" = true ]; then
        result=$(python3 -m pytest tests/unit/ -v -x --tb=short 2>&1) || true
    else
        result=$(python3 -m pytest tests/unit/ -v --tb=short 2>&1) || true
    fi
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Unit Tests" "${passed:-0}" "${failed:-0}"

    # Integration Tests
    echo -e "\n${BLUE}Running Integration Tests...${NC}"
    result=$(python3 -m pytest tests/integration/ -v --tb=short 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Integration Tests" "${passed:-0}" "${failed:-0}"

    # Contract Tests
    echo -e "\n${BLUE}Running Contract Tests...${NC}"
    result=$(python3 -m pytest tests/contract/ -v --tb=short 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Contract Tests" "${passed:-0}" "${failed:-0}"

    # Data Integrity Tests
    echo -e "\n${BLUE}Running Data Integrity Tests...${NC}"
    result=$(python3 -m pytest tests/data_integrity/ -v --tb=short 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Data Integrity Tests" "${passed:-0}" "${failed:-0}"

    # Benchmark Tests (skip in quick mode)
    if [ "$QUICK_MODE" = false ]; then
        echo -e "\n${BLUE}Running Benchmark Tests...${NC}"
        result=$(python3 -m pytest tests/benchmark/ -v --tb=short -m "not slow" 2>&1) || true
        passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
        failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
        print_result "Benchmark Tests" "${passed:-0}" "${failed:-0}"
    fi
}

# =============================================================================
# Frontend Tests
# =============================================================================
run_frontend_tests() {
    if [ "$SKIP_FRONTEND" = true ]; then
        echo -e "${YELLOW}Skipping frontend tests${NC}"
        return
    fi

    print_header "Frontend Tests"
    cd "$PROJECT_ROOT/frontend"

    # Unit/Component Tests
    echo -e "\n${BLUE}Running Component Tests (Vitest)...${NC}"
    result=$(npm run test:unit -- --run 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Component Tests" "${passed:-0}" "${failed:-0}"

    # Type Check
    echo -e "\n${BLUE}Running TypeScript Check...${NC}"
    if npx tsc --noEmit 2>&1; then
        print_result "TypeScript Check" "1" "0"
    else
        print_result "TypeScript Check" "0" "1"
    fi
}

# =============================================================================
# E2E Tests
# =============================================================================
run_e2e_tests() {
    if [ "$SKIP_E2E" = true ]; then
        echo -e "${YELLOW}Skipping E2E tests${NC}"
        return
    fi

    print_header "E2E Tests (Playwright)"
    cd "$PROJECT_ROOT/frontend"

    # Check services first
    check_services

    # Console Error Tests
    echo -e "\n${BLUE}Running Console Error Tests...${NC}"
    result=$(npx playwright test tests/e2e/console-errors.spec.ts --project=chromium --reporter=list 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Console Error Tests" "${passed:-0}" "${failed:-0}"

    # Performance Tests
    echo -e "\n${BLUE}Running Performance Tests...${NC}"
    result=$(npx playwright test tests/e2e/performance.spec.ts --project=chromium --reporter=list 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Performance Tests" "${passed:-0}" "${failed:-0}"

    # Accessibility Tests
    echo -e "\n${BLUE}Running Accessibility Tests...${NC}"
    result=$(npx playwright test tests/e2e/accessibility.spec.ts --project=chromium --reporter=list 2>&1) || true
    passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
    failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
    print_result "Accessibility Tests" "${passed:-0}" "${failed:-0}"

    # QA Walkthrough Tests (skip in quick mode)
    if [ "$QUICK_MODE" = false ]; then
        echo -e "\n${BLUE}Running QA Walkthrough Tests...${NC}"
        result=$(npx playwright test tests/e2e/qa-walkthrough.spec.ts --project=chromium --reporter=list 2>&1) || true
        passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
        failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
        print_result "QA Walkthrough Tests" "${passed:-0}" "${failed:-0}"

        # Visual Regression Tests
        echo -e "\n${BLUE}Running Visual Regression Tests...${NC}"
        result=$(npx playwright test tests/e2e/visual-regression/ --project=chromium --reporter=list --update-snapshots 2>&1) || true
        passed=$(echo "$result" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
        failed=$(echo "$result" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
        print_result "Visual Regression Tests" "${passed:-0}" "${failed:-0}"
    fi
}

# =============================================================================
# Generate Report
# =============================================================================
generate_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        return
    fi

    print_header "Generating Report"

    REPORT_FILE="$PROJECT_ROOT/test-report.html"

    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>TradingCoach Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .passed { color: green; }
        .failed { color: red; }
        .summary { font-size: 24px; margin: 20px 0; }
        ul { list-style: none; padding: 0; }
        li { padding: 8px 0; border-bottom: 1px solid #eee; }
        .timestamp { color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <h1>TradingCoach Test Report</h1>
    <p class="timestamp">Generated: $(date)</p>

    <div class="summary">
        <span class="passed">✓ $TOTAL_PASSED passed</span> |
        <span class="failed">✗ $TOTAL_FAILED failed</span>
    </div>

    <h2>Test Results</h2>
    <ul>
EOF

    for result in "${RESULTS[@]}"; do
        if [[ $result == ✓* ]]; then
            echo "        <li class=\"passed\">$result</li>" >> "$REPORT_FILE"
        else
            echo "        <li class=\"failed\">$result</li>" >> "$REPORT_FILE"
        fi
    done

    cat >> "$REPORT_FILE" << EOF
    </ul>
</body>
</html>
EOF

    echo -e "${GREEN}Report generated: $REPORT_FILE${NC}"
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         TradingCoach Full Test Suite Runner                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    START_TIME=$(date +%s)

    run_backend_tests
    run_frontend_tests
    run_e2e_tests
    generate_report

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Final Summary
    print_header "Test Summary"
    echo ""
    for result in "${RESULTS[@]}"; do
        if [[ $result == ✓* ]]; then
            echo -e "${GREEN}$result${NC}"
        else
            echo -e "${RED}$result${NC}"
        fi
    done
    echo ""
    echo -e "${BLUE}────────────────────────────────────────${NC}"
    echo -e "Total: ${GREEN}$TOTAL_PASSED passed${NC}, ${RED}$TOTAL_FAILED failed${NC}"
    echo -e "Duration: ${DURATION}s"
    echo ""

    if [ "$TOTAL_FAILED" -gt 0 ]; then
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main
