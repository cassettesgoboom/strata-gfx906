#pragma once

// CPU-owned lifecycle contract for one batch-window row slice. This type deliberately does not
// launch or poll GPU work; the runtime integration must call mark_complete only after its poll has
// observed completion and copied the target results.

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>

namespace strata::core {

inline constexpr int kBatchTransactionSlices = 2;
inline constexpr int kBatchTransactionSliceRows = 4;
inline constexpr int kBatchTransactionMaxRows = 4;
inline constexpr int kBatchTransactionMaxSlots = 8;

struct BatchTransactionSnapshot {
    int row_base = 0;
    int row_count = 0;
    uint32_t generation = 0;
    std::array<int, kBatchTransactionMaxRows> slots{};
    std::array<int32_t, kBatchTransactionMaxRows> tokens{};
    std::array<int64_t, kBatchTransactionMaxRows> positions{};
    std::array<int32_t, kBatchTransactionMaxRows> results{};
};

/// Opaque caller token. It carries identity only; lifecycle and completion state stay registry-owned.
class BatchTransactionHandle {
public:
    BatchTransactionHandle() = default;
    bool valid() const { return id_ != 0; }

private:
    friend class BatchTransactionRegistry;
    BatchTransactionHandle(int slice, uint64_t id, uint32_t generation, uint64_t registry_id)
        : slice_(slice), id_(id), generation_(generation), registry_id_(registry_id) {}

    int slice_ = -1;
    uint64_t id_ = 0;
    uint32_t generation_ = 0;
    uint64_t registry_id_ = 0;
};

/// Host-side state machine for two disjoint four-row slices (row bases 0 and 4).
/// One registry is owned by one verifier stage. Calls are expected to be serialized by its host owner.
class BatchTransactionRegistry {
public:
    enum class State { Stale, Prepared, Launched, Complete, Committing, Failed, Aborted, Committed };

    BatchTransactionRegistry() : registry_id_(allocate_registry_id()) {}
    BatchTransactionRegistry(const BatchTransactionRegistry&) = delete;
    BatchTransactionRegistry& operator=(const BatchTransactionRegistry&) = delete;
    BatchTransactionRegistry(BatchTransactionRegistry&&) = delete;
    BatchTransactionRegistry& operator=(BatchTransactionRegistry&&) = delete;

    bool prepare(uint32_t generation, int row_base, const int* slots, const int32_t* tokens,
                 const int64_t* positions, int row_count, BatchTransactionHandle& out, std::string& err) {
        out = BatchTransactionHandle{};
        if (generation == 0) return reject(err, "batch transaction generation zero is reserved");
        if (row_base != 0 && row_base != kBatchTransactionSliceRows)
            return reject(err, "batch transaction row base must be 0 or 4");
        if (row_count < 1 || row_count > kBatchTransactionMaxRows)
            return reject(err, "batch transaction row count must be 1..4");
        if (slots == nullptr || tokens == nullptr || positions == nullptr)
            return reject(err, "batch transaction snapshot input is null");
        const int slice = row_base / kBatchTransactionSliceRows;
        Record& rec = records_[slice];
        if (rec.active) return reject(err, "batch transaction slice is still owned");
        for (int other = 0; other < kBatchTransactionSlices; ++other)
            if (other != slice && records_[other].active && records_[other].handle_generation == generation)
                return reject(err, "batch transaction generation is already active on another slice");

        BatchTransactionSnapshot snapshot;
        snapshot.row_base = row_base;
        snapshot.row_count = row_count;
        snapshot.generation = generation;
        for (int i = 0; i < row_count; ++i) {
            if (slots[i] < 0 || slots[i] >= kBatchTransactionMaxSlots)
                return reject(err, "batch transaction slot is out of range");
            if (positions[i] < 0) return reject(err, "batch transaction position is negative");
            if (i > 0 && slots[i] == slots[i - 1]) {
                if (positions[i - 1] == std::numeric_limits<int64_t>::max())
                    return reject(err, "batch transaction consecutive position would overflow");
                if (positions[i] != positions[i - 1] + 1)
                    return reject(err, "batch transaction slot rows need consecutive positions");
            }
            for (int j = 0; j < i - 1; ++j)
                if (slots[j] == slots[i] && slots[i - 1] != slots[i])
                    return reject(err, "batch transaction slot rows must be contiguous");
            snapshot.slots[(size_t) i] = slots[i];
            snapshot.tokens[(size_t) i] = tokens[i];
            snapshot.positions[(size_t) i] = positions[i];
        }
        for (int other = 0; other < kBatchTransactionSlices; ++other) {
            if (other == slice || !records_[other].active) continue;
            const BatchTransactionSnapshot& active = records_[other].snapshot;
            for (int i = 0; i < row_count; ++i)
                for (int j = 0; j < active.row_count; ++j)
                    if (snapshot.slots[(size_t) i] == active.slots[(size_t) j])
                        return reject(err, "batch transaction slot is already owned by another active slice");
        }

        rec.active = true;
        rec.state = State::Prepared;
        rec.drained = false;
        rec.id = next_id_++;
        if (rec.id == 0) rec.id = next_id_++;
        rec.snapshot = snapshot;
        rec.handle_generation = generation;
        out = BatchTransactionHandle(slice, rec.id, generation, registry_id_);
        return true;
    }

    bool mark_launched(const BatchTransactionHandle& handle, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || rec->state != State::Prepared)
            return reject(err, "batch transaction launch requires its live prepared handle");
        rec->state = State::Launched;
        return true;
    }

    /// Trust boundary: the runtime owner must independently observe successful GPU poll completion and copy that
    /// transaction's target results before calling this method. The registry owns lifecycle state; it cannot verify
    /// device completion itself. This transition is the sole source of Complete state (there is no caller flag).
    bool mark_complete(const BatchTransactionHandle& handle, const int32_t* results, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || rec->state != State::Launched)
            return reject(err, "batch transaction completion requires its live launched handle");
        if (results == nullptr) return reject(err, "batch transaction results are null");
        for (int i = 0; i < rec->snapshot.row_count; ++i)
            rec->snapshot.results[(size_t) i] = results[i];
        rec->drained = true;
        rec->state = State::Complete;
        return true;
    }

    bool mark_failed(const BatchTransactionHandle& handle, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || (rec->state != State::Prepared && rec->state != State::Launched))
            return reject(err, "batch transaction failure requires a live prepared or launched handle");
        const bool compute_may_have_mutated_state = rec->state == State::Launched;
        rec->drained = rec->state == State::Prepared;
        rec->recovery_required = rec->recovery_required || compute_may_have_mutated_state;
        rec->state = State::Failed;
        return true;
    }

    bool abort(const BatchTransactionHandle& handle, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || (rec->state != State::Prepared && rec->state != State::Launched &&
                               rec->state != State::Complete && rec->state != State::Committing))
            return reject(err, "batch transaction abort requires a live uncommitted handle");
        const bool work_may_have_mutated_state = rec->state != State::Prepared;
        rec->drained = rec->state == State::Prepared || rec->state == State::Complete;
        rec->recovery_required = rec->recovery_required || work_may_have_mutated_state;
        rec->state = State::Aborted;
        return true;
    }

    /// Trust boundary: the runtime owner must independently verify that device work and waits are drained before
    /// calling this method. The registry cannot observe a GPU stream; this explicit acknowledgement gates retirement.
    bool mark_drained(const BatchTransactionHandle& handle, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || (rec->state != State::Failed && rec->state != State::Aborted))
            return reject(err, "only a failed or aborted transaction can be marked drained");
        rec->drained = true;
        return true;
    }

    /// Validate and record accepted prefixes, then enter Committing. This is intent only: callers must
    /// execute the device commit and call finish_commit after observing its result.
    bool begin_commit(const BatchTransactionHandle& handle, const int* accepted_by_slot, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || rec->state != State::Complete || !rec->drained)
            return reject(err, "batch transaction commit requires completed and drained work");
        if (accepted_by_slot == nullptr) return reject(err, "batch transaction accepted-prefix input is null");
        for (int i = 0; i < rec->snapshot.row_count;) {
            const int first = i;
            while (i < rec->snapshot.row_count && rec->snapshot.slots[(size_t) i] == rec->snapshot.slots[(size_t) first])
                ++i;
            const int keep = accepted_by_slot[rec->snapshot.slots[(size_t) first]];
            if (keep < 1 || keep > i - first)
                return reject(err, "batch transaction accepted prefix is outside its slot group");
        }
        for (int i = 0; i < rec->snapshot.row_count;) {
            const int first = i;
            while (i < rec->snapshot.row_count && rec->snapshot.slots[(size_t) i] == rec->snapshot.slots[(size_t) first])
                ++i;
            const int keep = accepted_by_slot[rec->snapshot.slots[(size_t) first]];
            rec->accepted_by_slot[(size_t) rec->snapshot.slots[(size_t) first]] = keep;
        }
        rec->state = State::Committing;
        rec->drained = false;
        return true;
    }

    /// Trust boundary: call only after the runtime observes successful completion of the selective device commit.
    /// A failed device commit may have partially mutated session state and therefore requires both stream drain and
    /// caller-owned recovery/discard acknowledgement before this slice can be retired.
    bool finish_commit(const BatchTransactionHandle& handle, bool succeeded, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || rec->state != State::Committing)
            return reject(err, "batch transaction commit result requires its live committing handle");
        if (succeeded) {
            rec->state = State::Committed;
            rec->drained = true;
            return true;
        }
        rec->state = State::Failed;
        rec->drained = false;
        rec->recovery_required = true;
        return true;
    }

    /// Trust boundary: after a failed/aborted commit has drained, the runtime must restore the saved session state
    /// or discard the affected session before acknowledging recovery. Drain alone does not imply rollback.
    bool mark_recovered(const BatchTransactionHandle& handle, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || (rec->state != State::Failed && rec->state != State::Aborted) || !rec->drained ||
            !rec->recovery_required)
            return reject(err, "transaction recovery requires a drained failed or aborted commit");
        rec->recovery_required = false;
        return true;
    }

    /// Copy the registry-owned, validated accepted-prefix intent. Available only after begin_commit succeeds.
    bool accepted_prefixes(const BatchTransactionHandle& handle,
                           std::array<int, kBatchTransactionMaxSlots>& out, std::string& err) const {
        const Record* rec = find(handle);
        if (rec == nullptr || (rec->state != State::Committing && rec->state != State::Committed))
            return reject(err, "accepted prefixes require a live committing or committed handle");
        out = rec->accepted_by_slot;
        return true;
    }

    /// Release a committed slice, or a failed/aborted slice after explicit drain. Handles then become stale.
    bool retire(const BatchTransactionHandle& handle, std::string& err) {
        Record* rec = find(handle);
        if (rec == nullptr || (rec->state != State::Committed &&
                               !((rec->state == State::Failed || rec->state == State::Aborted) && rec->drained &&
                                 !rec->recovery_required)))
            return reject(err, "batch transaction retirement requires commit or a drained failure/abort");
        *rec = Record{};
        return true;
    }

    bool snapshot(const BatchTransactionHandle& handle, BatchTransactionSnapshot& out, std::string& err) const {
        const Record* rec = find(handle);
        if (rec == nullptr) return reject(err, "batch transaction snapshot handle is stale");
        out = rec->snapshot;
        return true;
    }

    State state(const BatchTransactionHandle& handle) const {
        const Record* rec = find(handle);
        return rec == nullptr ? State::Stale : rec->state;
    }

    bool drained(const BatchTransactionHandle& handle) const {
        const Record* rec = find(handle);
        return rec != nullptr && rec->drained;
    }

private:
    struct Record {
        bool active = false;
        State state = State::Stale;
        bool drained = false;
        bool recovery_required = false;
        uint64_t id = 0;
        uint32_t handle_generation = 0;
        BatchTransactionSnapshot snapshot{};
        std::array<int, kBatchTransactionMaxSlots> accepted_by_slot{};
    };

    static bool reject(std::string& err, const char* message) {
        err = message;
        return false;
    }

    Record* find(const BatchTransactionHandle& handle) {
        if (!handle.valid() || handle.registry_id_ != registry_id_ || handle.slice_ < 0 ||
            handle.slice_ >= kBatchTransactionSlices) return nullptr;
        Record& rec = records_[handle.slice_];
        return rec.active && rec.id == handle.id_ && rec.handle_generation == handle.generation_ ? &rec : nullptr;
    }

    const Record* find(const BatchTransactionHandle& handle) const {
        if (!handle.valid() || handle.registry_id_ != registry_id_ || handle.slice_ < 0 ||
            handle.slice_ >= kBatchTransactionSlices) return nullptr;
        const Record& rec = records_[handle.slice_];
        return rec.active && rec.id == handle.id_ && rec.handle_generation == handle.generation_ ? &rec : nullptr;
    }

    std::array<Record, kBatchTransactionSlices> records_{};
    inline static std::atomic<uint64_t> next_registry_id_{1};
    static uint64_t allocate_registry_id() {
        uint64_t id = next_registry_id_.fetch_add(1, std::memory_order_relaxed);
        if (id == 0) id = next_registry_id_.fetch_add(1, std::memory_order_relaxed);
        return id;
    }
    uint64_t registry_id_ = 0;
    uint64_t next_id_ = 1;
};

}  // namespace strata::core
