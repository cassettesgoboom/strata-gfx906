#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "strata/program/native_trace_id.hpp"

namespace strata::program {

// Describes one successfully committed serial verify transaction. Token IDs are
// exactly the ordered IDs emitted by that transaction, not a claim about state
// after each individual token.
inline std::string serial_window_record(const std::string& request_id, int64_t window,
                                       const std::vector<int32_t>& token_ids,
                                       int64_t mtp_accepted, int64_t mtp_offered) {
    if (!NativeTraceId::valid(request_id) || window < 0 || token_ids.empty() ||
        mtp_accepted < 0 || mtp_offered < 0 || mtp_accepted > mtp_offered)
        return {};
    std::string record = "strata correctness: request=" + request_id + " state=native_window_commit window=" +
                         std::to_string(window) + " native_token_ids=";
    for (size_t i = 0; i < token_ids.size(); ++i) {
        if (token_ids[i] < 0) return {};
        if (i != 0) record.push_back(',');
        record += std::to_string(token_ids[i]);
    }
    record += " mtp_accepted=" + std::to_string(mtp_accepted) +
              " mtp_offered=" + std::to_string(mtp_offered);
    return record;
}

}  // namespace strata::program
