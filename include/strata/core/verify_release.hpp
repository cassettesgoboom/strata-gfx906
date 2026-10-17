#pragma once

#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <mutex>

namespace strata::core {

/// A fixed-lifetime watchdog handle for the mapped flags a verifier exposes to GPU spin waits.
/// The lock covers only flag publication and unregistration, never stream or run completion.
class VerifyReleaseControl {
public:
    using DrainFn = bool (*)(void* stream, void* copy_stream, int device, int timeout_ms);
    enum class BindStatus { bound, occupied, unbinding };

    BindStatus bind(std::atomic<bool>* released, volatile uint32_t* flag, volatile uint32_t* flag_a,
                    volatile uint32_t* flag_b, void* stream, void* copy_stream, int device, DrainFn drain) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (unbinding_) return BindStatus::unbinding;
        if (released_ != nullptr) return BindStatus::occupied;
        accepting_ = true;
        released_ = released;
        flags_[0] = flag;
        flags_[1] = flag_a;
        flags_[2] = flag_b;
        stream_ = stream;
        copy_stream_ = copy_stream;
        device_ = device;
        drain_ = drain;
        return BindStatus::bound;
    }

    void unbind() {
        std::unique_lock<std::mutex> lock(mutex_);
        if (unbinding_) {
            drained_.wait(lock, [&] { return !unbinding_; });
            return;
        }
        unbinding_ = true;
        accepting_ = false;
        drained_.wait(lock, [&] { return active_ == 0; });
        released_ = nullptr;
        for (volatile uint32_t*& flag : flags_) flag = nullptr;
        stream_ = nullptr;
        copy_stream_ = nullptr;
        drain_ = nullptr;
        device_ = -1;
        unbinding_ = false;
        drained_.notify_all();
    }

    bool release(int timeout_ms, bool* registered = nullptr) {
        if (registered != nullptr) *registered = false;
        DrainFn drain;
        void* stream;
        void* copy_stream;
        int device;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (!accepting_ || released_ == nullptr) return false;
            if (registered != nullptr) *registered = true;
            released_->store(true);
            for (volatile uint32_t* flag : flags_)
                if (flag != nullptr) *flag = UINT32_MAX;
            std::atomic_thread_fence(std::memory_order_seq_cst);
            ++active_;
            drain = drain_;
            stream = stream_;
            copy_stream = copy_stream_;
            device = device_;
        }

        const bool done = drain == nullptr || drain(stream, copy_stream, device, timeout_ms);
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (--active_ == 0) drained_.notify_all();
        }
        return done;
    }

private:
    std::mutex mutex_;
    std::condition_variable drained_;
    bool accepting_ = false;
    bool unbinding_ = false;
    unsigned active_ = 0;
    std::atomic<bool>* released_ = nullptr;
    volatile uint32_t* flags_[3] = {};
    void* stream_ = nullptr;
    void* copy_stream_ = nullptr;
    int device_ = -1;
    DrainFn drain_ = nullptr;
};

}  // namespace strata::core
