#include <cassert>
#include <string>
#include <vector>

#include "strata/program/native_window_trace.hpp"

int main() {
    using strata::program::serial_window_record;
    using strata::program::validate_window_trace_config;
    using Error = strata::program::WindowTraceConfigError;
    assert(validate_window_trace_config(false, false, true, true) == Error::none);
    assert(validate_window_trace_config(true, false, true, true) == Error::none);
    assert(validate_window_trace_config(false, true, false, false) == Error::requires_base_trace);
    assert(validate_window_trace_config(true, true, true, false) == Error::unsupported_execution_mode);
    assert(validate_window_trace_config(true, true, false, true) == Error::unsupported_execution_mode);
    assert(validate_window_trace_config(true, true, false, false) == Error::none);

    const std::string id(32, 'a');
    assert(serial_window_record(id, 0, {42, 7, 19}, 2, 3) ==
           "strata correctness: request=" + id + " state=native_window_commit window=0 "
           "native_token_ids=42,7,19 mtp_accepted=2 mtp_offered=3");
    assert(serial_window_record(id, 1, {9}, 0, 0) ==
           "strata correctness: request=" + id + " state=native_window_commit window=1 "
           "native_token_ids=9 mtp_accepted=0 mtp_offered=0");
    assert(serial_window_record("bad", 0, {1}, 0, 0).empty());
    assert(serial_window_record(id, -1, {1}, 0, 0).empty());
    assert(serial_window_record(id, 0, {}, 0, 0).empty());
    assert(serial_window_record(id, 0, {1, -1}, 0, 0).empty());
    assert(serial_window_record(id, 0, {1}, 2, 1).empty());
}
