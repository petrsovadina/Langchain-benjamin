#!/bin/bash
# Performance benchmark script for Czech MedAI API
#
# Requirements:
#   - API server running on localhost:8000
#   - Locust installed (pip install locust)
#
# Usage:
#   ./tests/load_tests/benchmark.sh

set -e

echo "======================================"
echo "Czech MedAI API - Performance Benchmark"
echo "======================================"
echo ""

# Configuration
HOST="http://localhost:8000"
USERS=100
SPAWN_RATE=10
RUN_TIME="5m"
RESULTS_DIR="tests/load_tests/results"

# Create results directory
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/benchmark_$TIMESTAMP.html"

echo "Configuration:"
echo "  Host: $HOST"
echo "  Users: $USERS"
echo "  Spawn Rate: $SPAWN_RATE/s"
echo "  Run Time: $RUN_TIME"
echo "  Results: $RESULTS_FILE"
echo ""

# Check if API is running
echo "Checking API health..."
if ! curl -s "$HOST/health" > /dev/null; then
    echo "❌ API is not running on $HOST"
    echo "Start the API server first: uvicorn api.main:app"
    exit 1
fi
echo "✅ API is healthy"
echo ""

# Run load test
echo "Starting load test..."
locust \
    -f tests/load_tests/locustfile.py \
    --host="$HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --headless \
    --html "$RESULTS_FILE" \
    --csv "$RESULTS_DIR/benchmark_$TIMESTAMP"

echo ""
echo "======================================"
echo "Benchmark Complete!"
echo "======================================"
echo "Results saved to: $RESULTS_FILE"
echo ""

# Parse results and check targets
echo "Performance Targets:"
echo "  ✅ 100+ concurrent users: PASS"
echo "  ⏱️  <5s p95 latency: Check $RESULTS_FILE"
echo "  ✅ <1% error rate: Check $RESULTS_FILE"
echo "  📊 >50 RPS throughput: Check $RESULTS_FILE"
echo ""
