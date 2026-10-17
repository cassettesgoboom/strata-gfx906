#include "strata/core/on_device.hpp"

#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int current_device = 0;
int get_error = cudaSuccess;
int set_error = cudaSuccess;
int get_calls = 0;
std::vector<int> set_calls;

void require(bool condition, const std::string& message) {
    if (!condition)
        throw std::runtime_error(message);
}

void reset(int device) {
    current_device = device;
    get_error = cudaSuccess;
    set_error = cudaSuccess;
    get_calls = 0;
    set_calls.clear();
}

} // namespace

extern "C" cudaError_t cudaGetDevice(int* device) {
    ++get_calls;
    if (get_error == cudaSuccess)
        *device = current_device;
    return get_error;
}

extern "C" cudaError_t cudaSetDevice(int device) {
    set_calls.push_back(device);
    if (set_error == cudaSuccess)
        current_device = device;
    return set_error;
}

int main() {
    try {
        reset(0);
        {
            const strata::core::OnDevice outer(2);
            require(current_device == 2,
                    "outer scope did not select its device");
            {
                const strata::core::OnDevice inner(3);
                require(current_device == 3,
                        "nested scope did not select its device");
            }
            require(current_device == 2,
                    "nested scope did not restore its caller device");
        }
        require(current_device == 0,
                "outer scope did not restore its caller device");
        require((set_calls == std::vector<int>{2, 3, 2, 0}),
                "unexpected switch/restore sequence");

        reset(2);
        {
            const strata::core::OnDevice same(2);
            const strata::core::OnDevice unspecified(-1);
            require(current_device == 2,
                    "no-op scope changed the current device");
        }
        require(get_calls == 1,
                "same-device and negative-device scopes queried unexpectedly");
        require(set_calls.empty(),
                "same-device or negative-device scope switched devices");

        reset(1);
        set_error = 1;
        {
            const strata::core::OnDevice failed_switch(4);
            require(current_device == 1,
                    "failed switch changed the current device");
        }
        require(set_calls == std::vector<int>{4},
                "failed switch attempted an unexpected restore");

        reset(1);
        get_error = 1;
        {
            const strata::core::OnDevice failed_query(4);
            require(current_device == 1,
                    "failed query changed the current device");
        }
        require(get_calls == 1 && set_calls.empty(),
                "failed query should not attempt a switch");

        std::cout << "on_device_scope_test: PASS\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "on_device_scope_test: " << error.what() << '\n';
        return 1;
    }
}
