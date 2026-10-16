// CPU-only lifecycle checks for the opt-in batch transaction contract.
#include "strata/core/batch_transaction.hpp"

#include <cstdio>
#include <cstdlib>
#include <limits>
#include <type_traits>

using strata::core::BatchTransactionHandle;
using strata::core::BatchTransactionRegistry;
using strata::core::BatchTransactionSnapshot;

template <class T>
concept HasPublicCompletionFlag = requires(T value) { value.complete; };
static_assert(!std::is_aggregate_v<BatchTransactionHandle>);
static_assert(!HasPublicCompletionFlag<BatchTransactionHandle>);

namespace {
int failures = 0;

void check(bool ok, const char* what) {
    std::printf("  %-74s %s\n", what, ok ? "ok" : "FAIL");
    if (!ok) ++failures;
}

bool prepare(BatchTransactionRegistry& registry, uint32_t generation, int row_base, const int* slots,
             const int32_t* tokens, const int64_t* positions, int count, BatchTransactionHandle& handle) {
    std::string err;
    const bool ok = registry.prepare(generation, row_base, slots, tokens, positions, count, handle, err);
    if (!ok) std::fprintf(stderr, "prepare: %s\n", err.c_str());
    return ok;
}
}  // namespace

int main() {
    std::printf("batch_transaction_test\n");
    BatchTransactionRegistry registry;
    BatchTransactionHandle ab, cd;
    const int ab_slots[] = {0, 0, 1, 1};
    const int32_t ab_tokens[] = {10, 11, 20, 21};
    const int64_t ab_positions[] = {100, 101, 200, 201};
    const int cd_slots[] = {2, 2, 3, 3};
    const int32_t cd_tokens[] = {30, 31, 40, 41};
    const int64_t cd_positions[] = {300, 301, 400, 401};

    check(prepare(registry, 1, 0, ab_slots, ab_tokens, ab_positions, 4, ab), "prepare AB slice");
    check(prepare(registry, 2, 4, cd_slots, cd_tokens, cd_positions, 4, cd), "prepare disjoint CD slice concurrently");
    check(registry.state(ab) == BatchTransactionRegistry::State::Prepared &&
          registry.state(cd) == BatchTransactionRegistry::State::Prepared, "both slice states are registry-owned");

    BatchTransactionHandle duplicate;
    std::string err;
    check(!registry.prepare(3, 0, ab_slots, ab_tokens, ab_positions, 4, duplicate, err),
          "same slice cannot be prepared while owned");

    BatchTransactionSnapshot saved;
    check(registry.snapshot(ab, saved, err), "read immutable AB snapshot copy");
    check(saved.generation == 1 && saved.row_base == 0 && saved.row_count == 4 &&
          saved.slots[2] == 1 && saved.tokens[3] == 21 && saved.positions[1] == 101,
          "snapshot preserves generation, slot, token, and position identity");
    saved.tokens[0] = -99;
    BatchTransactionSnapshot saved_again;
    check(registry.snapshot(ab, saved_again, err) && saved_again.tokens[0] == 10,
          "mutating a caller snapshot copy cannot change registry identity");

    const int32_t cd_results[] = {32, 33, 42, 43};
    check(registry.mark_launched(cd, err), "CD launches independently while AB remains prepared");
    check(registry.mark_complete(cd, cd_results, err), "CD completes while AB remains active");
    check(registry.state(ab) == BatchTransactionRegistry::State::Prepared &&
          registry.state(cd) == BatchTransactionRegistry::State::Complete,
          "CD completion does not overwrite AB state");
    int keep_cd[8] = {};
    keep_cd[2] = 0;
    keep_cd[3] = 1;
    check(!registry.commit(cd, keep_cd, err), "later-group accepted prefix zero is rejected");
    keep_cd[2] = 3;
    check(!registry.commit(cd, keep_cd, err), "later-group prefix beyond its row group is rejected");
    keep_cd[2] = 2;
    check(registry.commit(cd, keep_cd, err), "later-group valid accepted prefixes commit");
    check(registry.retire(cd, err) && registry.state(ab) == BatchTransactionRegistry::State::Prepared,
          "CD retirement leaves AB slice ownership intact");
    const int alias_slots[] = {0, 0};
    const int32_t alias_tokens[] = {50, 51};
    const int64_t alias_positions[] = {500, 501};
    check(!registry.prepare(3, 4, alias_slots, alias_tokens, alias_positions, 2, duplicate, err) &&
          err.find("already owned") != std::string::npos,
          "active slices cannot own the same slot");

    const int32_t ab_results[] = {12, 13, 22, 23};
    check(!registry.mark_complete(ab, ab_results, err), "completion cannot be forged before launch");
    check(registry.state(ab) == BatchTransactionRegistry::State::Prepared && !registry.drained(ab),
          "rejected forged completion leaves state prepared and undrained");
    check(registry.mark_launched(ab, err), "prepared AB transitions to launched");
    check(!registry.mark_launched(ab, err), "duplicate launch is rejected");
    check(registry.mark_complete(ab, ab_results, err), "launched AB completes with target results");
    check(registry.drained(ab), "completion records drained work");
    check(registry.snapshot(ab, saved_again, err) && saved_again.results[0] == 12 && saved_again.results[3] == 23,
          "target results are captured in the registry snapshot");

    int keep[8] = {};
    keep[0] = 0;
    keep[1] = 1;
    check(!registry.commit(ab, keep, err), "accepted prefix zero is rejected");
    keep[0] = 3;
    check(!registry.commit(ab, keep, err), "accepted prefix beyond its two-row slot group is rejected");
    keep[0] = 2;
    keep[1] = 1;
    check(registry.commit(ab, keep, err), "valid per-slot accepted prefixes commit");
    check(!registry.commit(ab, keep, err), "duplicate commit is rejected");
    check(!prepare(registry, 3, 0, ab_slots, ab_tokens, ab_positions, 4, duplicate),
          "committed slice stays owned until retirement");
    check(registry.retire(ab, err), "committed slice retires");
    check(registry.state(ab) == BatchTransactionRegistry::State::Stale, "retired handle becomes stale");

    BatchTransactionHandle replacement;
    check(prepare(registry, 1, 0, ab_slots, ab_tokens, ab_positions, 4, replacement),
          "retired slice can be reused with a new transaction ID");
    check(!registry.mark_launched(ab, err), "old handle cannot act on replacement with same generation");
    check(registry.mark_launched(replacement, err), "replacement handle launches");
    check(registry.abort(replacement, err), "launched transaction can be aborted");
    check(!registry.retire(replacement, err), "aborted launched work cannot retire before drain");
    check(!prepare(registry, 3, 0, ab_slots, ab_tokens, ab_positions, 4, duplicate),
          "aborted slice cannot be reused before drain");
    check(registry.mark_drained(replacement, err), "abort becomes reusable only after explicit drain");
    check(registry.retire(replacement, err), "drained abort retires");

    BatchTransactionHandle failed;
    check(prepare(registry, 4, 0, ab_slots, ab_tokens, ab_positions, 4, failed), "prepare failure-path transaction");
    check(registry.mark_launched(failed, err), "failure-path transaction launches");
    check(registry.mark_failed(failed, err), "launched transaction enters failed state");
    check(!registry.retire(failed, err), "failed launched work cannot retire before drain");
    check(registry.mark_drained(failed, err) && registry.retire(failed, err), "drained failure retires");

    BatchTransactionHandle bad;
    const int noncontiguous[] = {0, 1, 0};
    const int32_t three_tokens[] = {1, 2, 3};
    const int64_t three_positions[] = {7, 8, 9};
    check(!prepare(registry, 5, 0, noncontiguous, three_tokens, three_positions, 3, bad),
          "noncontiguous rows for one slot are rejected");
    const int64_t bad_positions[] = {7, 9};
    const int same_slot[] = {0, 0};
    check(!prepare(registry, 5, 0, same_slot, three_tokens, bad_positions, 2, bad),
          "nonconsecutive positions for one slot are rejected");
    const int64_t max_then_wrap[] = {std::numeric_limits<int64_t>::max(), 0};
    check(!registry.prepare(5, 0, same_slot, three_tokens, max_then_wrap, 2, bad, err) &&
          err.find("overflow") != std::string::npos,
          "consecutive-position check rejects signed overflow");
    check(!prepare(registry, 5, 2, ab_slots, ab_tokens, ab_positions, 4, bad), "unsupported slice base is rejected");
    check(!prepare(registry, 0, 0, ab_slots, ab_tokens, ab_positions, 4, bad), "zero generation is rejected");

    // A second slice may not reuse an active generation, even though row ownership is disjoint.
    BatchTransactionHandle generation_owner;
    check(prepare(registry, 9, 0, ab_slots, ab_tokens, ab_positions, 4, generation_owner), "prepare generation owner");
    const bool duplicate_generation_rejected =
        !registry.prepare(9, 4, cd_slots, cd_tokens, cd_positions, 4, bad, err) &&
        err.find("generation") != std::string::npos;
    check(duplicate_generation_rejected, "active generation cannot identify two transactions");
    check(registry.abort(generation_owner, err) && registry.retire(generation_owner, err),
          "unlaunched abort retires without device drain");

    BatchTransactionRegistry registry_one;
    BatchTransactionRegistry registry_two;
    BatchTransactionHandle local_one, local_two;
    check(prepare(registry_one, 11, 0, ab_slots, ab_tokens, ab_positions, 4, local_one) &&
          prepare(registry_two, 11, 0, ab_slots, ab_tokens, ab_positions, 4, local_two),
          "independent registries issue local transaction handles");
    check(!registry_two.mark_launched(local_one, err) &&
          registry_two.state(local_one) == BatchTransactionRegistry::State::Stale,
          "a handle cannot be replayed against another registry");

    return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
