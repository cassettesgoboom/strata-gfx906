#include "strata/core/verify_release.hpp"

#include <memory>
#include <initializer_list>
#include <thread>

using strata::core::VerifyReleaseControl;
using BindStatus = VerifyReleaseControl::BindStatus;

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (false)

bool immediate_drain(void*, void*, int, int) { return true; }
bool failed_drain(void*, void*, int, int) { return false; }

struct PausedDrain {
    std::atomic<bool> entered{false};
    std::atomic<bool> finish{false};
};

bool paused_drain(void* context, void*, int, int) {
    auto* pause = static_cast<PausedDrain*>(context);
    pause->entered.store(true, std::memory_order_release);
    while (!pause->finish.load(std::memory_order_acquire)) std::this_thread::yield();
    return true;
}

int main() {
    VerifyReleaseControl control;
    std::atomic<bool> released{false};
    uint32_t flags[3] = {0, 0, 0};
    CHECK(control.bind(&released, flags, flags + 1, flags + 2, nullptr, nullptr, 0, &immediate_drain) ==
          BindStatus::bound);
    CHECK(control.bind(&released, flags, flags + 1, flags + 2, nullptr, nullptr, 0, &immediate_drain) ==
          BindStatus::occupied);
    CHECK(control.release(5000));
    CHECK(released.load());
    for (uint32_t flag : flags) CHECK(flag == UINT32_MAX);
    control.unbind();

    released.store(false);
    for (uint32_t& flag : flags) flag = 0;
    CHECK(control.bind(&released, flags, flags + 1, flags + 2, nullptr, nullptr, 0, &failed_drain) == BindStatus::bound);
    bool registered = false;
    CHECK(!control.release(5000, &registered));
    CHECK(registered && released.load());
    for (uint32_t flag : flags) CHECK(flag == UINT32_MAX);
    control.unbind();

    // The flags publish before the drain callback waits; unregistration pins their storage until that drain ends.
    for (int n = 0; n < 100; ++n) {
        auto owned_released = std::make_unique<std::atomic<bool>>(false);
        auto owned_flags = std::make_unique<uint32_t[]>(3);
        PausedDrain pause;
        CHECK(control.bind(owned_released.get(), owned_flags.get(), owned_flags.get() + 1, owned_flags.get() + 2,
                           &pause, nullptr, 0, &paused_drain) == BindStatus::bound);

        std::atomic<bool> release_ok{false};
        std::thread watchdog([&] { release_ok.store(control.release(5000), std::memory_order_release); });
        while (!pause.entered.load(std::memory_order_acquire)) std::this_thread::yield();
        const bool published = owned_released->load();
        bool flags_published = true;
        for (uint32_t flag : {owned_flags[0], owned_flags[1], owned_flags[2]})
            flags_published = flags_published && flag == UINT32_MAX;

        std::atomic<bool> unbind_done{false};
        std::thread destroyer([&] {
            control.unbind();
            unbind_done.store(true, std::memory_order_release);
        });

        auto next_released = std::make_unique<std::atomic<bool>>(false);
        auto next_flags = std::make_unique<uint32_t[]>(3);
        BindStatus during_unbind;
        do {
            during_unbind = control.bind(next_released.get(), next_flags.get(), next_flags.get() + 1,
                                         next_flags.get() + 2, nullptr, nullptr, 0, &immediate_drain);
            if (during_unbind == BindStatus::occupied) std::this_thread::yield();
        } while (during_unbind == BindStatus::occupied);
        const bool unbound_early = unbind_done.load();
        pause.finish.store(true, std::memory_order_release);
        watchdog.join();
        destroyer.join();
        owned_flags.reset();
        owned_released.reset();
        CHECK(published && flags_published && !unbound_early && during_unbind == BindStatus::unbinding &&
              release_ok.load() && unbind_done.load());
        CHECK(control.bind(next_released.get(), next_flags.get(), next_flags.get() + 1, next_flags.get() + 2,
                           nullptr, nullptr, 0, &immediate_drain) == BindStatus::bound);
        CHECK(control.release(5000));
        CHECK(next_released->load());
        for (uint32_t flag : {next_flags[0], next_flags[1], next_flags[2]}) CHECK(flag == UINT32_MAX);
        control.unbind();
        next_flags.reset();
        next_released.reset();
    }
}
