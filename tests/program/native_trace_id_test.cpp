#include <cassert>
#include <string>

#include "strata/program/native_trace_id.hpp"

int main() {
    using strata::program::NativeTraceId;
    const std::string id(32, 'a');

    NativeTraceId absent;
    assert(absent.validate(false) == NativeTraceId::Error::none);
    assert(absent.validate(true) == NativeTraceId::Error::missing);

    NativeTraceId good;
    assert(good.add(id));
    assert(good.validate(true) == NativeTraceId::Error::none);
    assert(good.value() == id);

    NativeTraceId malformed;
    assert(!malformed.add("Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));
    assert(malformed.validate(true) == NativeTraceId::Error::malformed);

    NativeTraceId duplicate;
    assert(duplicate.add(id));
    assert(!duplicate.add(id));
    assert(duplicate.validate(true) == NativeTraceId::Error::duplicate);

    const std::string text_suffix = " temperature=0.2 trace_id=" + id + " 17,18";
    assert(strata::program::rewrite_batch_admission(false, text_suffix) ==
           "GEN 1 temperature=0.2 trace_id=" + id + " 17,18");
    const std::string image_suffix = " trace_id=" + id + " emb.bin 17,18";
    assert(strata::program::rewrite_batch_admission(true, image_suffix) ==
           "GENI 1 trace_id=" + id + " emb.bin 17,18");
    assert(strata::program::rewrite_batch_admission(false, " 17,18") == "GEN 1 17,18");
}
