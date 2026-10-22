#!/bin/bash
# P1.1 (issue #55): penalties inside batch windows - solo-vs-batch token parity WITH penalties in play,
# Swift IQ3_XXS, gfx906, on the exactness recipe (same arms' shape as P0.2).
# Three arms, batch 4 / 4 prompts / 64 tokens each:
#   control   - no sampling keys: must reproduce P0.2's IDENTICAL on every slot.
#   sampled   - temperature + repetition penalty WITH seed=1234: the batch sampler now penalises each row from
#               its own slot's history (staged per window); before #55 the engine zeroed the penalty and this
#               arm DIFFERED from solo - after the change it must be IDENTICAL.  The seed is part of the arm:
#               an unseeded request draws from a fresh steady_clock-keyed stream (generate.cpp:11854), so solo
#               and batch are two different runs and DIFFER BY DESIGN (witnessed 2026-10-21: an unseeded
#               sampled arm differs at token 0 with no penalty involved); a seeded one replays the same Philox
#               draws and is what tests the penalty path.  Greedy arms need no seed: they draw no random numbers.
#   greedy    - penalty with no temperature: a greedy row that asks for a penalty samples through the
#               sampler kernel (the window graph's argmax sees no history; the solo greedy path DOES
#               penalise), so this arm pins that replacement too.
# ONE ENGINE AT A TIME (SVM crash rule): refuses while any strata/vllm engine is alive, and under 65 GiB free.
set -u
cd "$(dirname "$0")/../.."
TS=$(date +%Y%m%d-%H%M%S)
REC=benchmarks/gfx906/receipts
mkdir -p logs "$REC"
if pgrep -f "engine/strata|vllm" >/dev/null 2>&1; then
    echo "refusing: another engine is alive - one HIP engine at a time (SVM crash rule)"; exit 3
fi
AVAIL=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
if [ "$AVAIL" -lt $((65 * 1024 * 1024)) ]; then
    echo "refusing: $((AVAIL / 1024 / 1024)) GiB available, the engine load wants >= 65 GiB"; exit 3
fi
EXTRA="--gpu 1 --pcie-frac 0 --adapt-every 1000000 --no-prefill-borrow"
PY=/root/.pyenv/versions/venv312/bin/python3
rc=0
run_arm() {
    local name="$1" keys="$2"
    echo "=== p1.1 $name start $(date +%T) (RAM avail $(free -g | awk '/Mem/{print $7}') GiB) ==="
    if [ -n "$keys" ]; then
        BATCH_TEST_LOG="logs/p1.1-${name}-${TS}.log" \
        $PY tools/batch_test.py --exe engine/strata --config strata-swift-iq3_xxs.json \
            --batch 4 --n 4 --max-new 64 --extra "$EXTRA" --keys "$keys" \
            2>&1 | tee "logs/p1.1-${name}-stdout-${TS}.log"
    else
        BATCH_TEST_LOG="logs/p1.1-${name}-${TS}.log" \
        $PY tools/batch_test.py --exe engine/strata --config strata-swift-iq3_xxs.json \
            --batch 4 --n 4 --max-new 64 --extra "$EXTRA" \
            2>&1 | tee "logs/p1.1-${name}-stdout-${TS}.log"
    fi
    local code=${PIPESTATUS[0]}
    echo "arm $name exit=$code  (expect: every slot IDENTICAL, penalty arms included)"
    [ "$code" -ne 0 ] && rc=$code
}
run_arm "control" ""
run_arm "sampled" "temperature=0.7 top_k=20 repetition_penalty=1.1 penalty_last_n=32 seed=1234"
run_arm "greedy" "repetition_penalty=1.1 penalty_last_n=32"
echo "=== P1.1 penalty witness done rc=$rc logs: logs/p1.1-*-${TS}.log ==="
exit $rc
