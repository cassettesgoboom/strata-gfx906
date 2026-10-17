#pragma once

#include <string>
#include <string_view>

namespace strata::program {

class NativeTraceId {
public:
    enum class Error { none, missing, malformed, duplicate };

    bool add(std::string_view value) {
        if (seen_) {
            error_ = Error::duplicate;
            return false;
        }
        seen_ = true;
        if (!valid(value)) {
            error_ = Error::malformed;
            return false;
        }
        value_.assign(value);
        return true;
    }

    Error validate(bool required) const {
        if (error_ != Error::none) return error_;
        return required && !seen_ ? Error::missing : Error::none;
    }

    const std::string& value() const { return value_; }

    static bool valid(std::string_view value) {
        if (value.size() != 32) return false;
        for (const unsigned char c : value)
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
        return true;
    }

    static const char* error_text(Error error) {
        switch (error) {
            case Error::missing: return "missing";
            case Error::malformed: return "invalid";
            case Error::duplicate: return "duplicate";
            case Error::none: return "";
        }
        return "invalid";
    }

private:
    bool seen_ = false;
    Error error_ = Error::none;
    std::string value_;
};

inline std::string rewrite_batch_admission(bool image, std::string_view suffix) {
    std::string line = image ? "GENI 1" : "GEN 1";
    line.append(suffix);
    return line;
}

}  // namespace strata::program
