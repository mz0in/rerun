#include <optional>
#include <rerun/archetypes/tensor.hpp>
#include <rerun/datatypes/tensor_data.hpp>
#include <rerun/recording_stream.hpp>

namespace rr = rerun;

int main(int argc, char** argv) {
    auto rec = rr::RecordingStream("rerun_example_roundtrip_tensor");
    rec.save(argv[1]).throw_on_failure();

    std::vector<rr::datatypes::TensorDimension> dimensions{
        rr::datatypes::TensorDimension{3, std::nullopt},
        rr::datatypes::TensorDimension{4, std::nullopt},
        rr::datatypes::TensorDimension{5, std::nullopt},
        rr::datatypes::TensorDimension{6, std::nullopt}};

    std::vector<int32_t> data;
    for (auto i = 0; i < 360; ++i) {
        data.push_back(i);
    }

    // TODO(jleibs) Tensor data can't actually be logged yet because C++ Unions
    // don't supported nested list-types.
    rec.log(
        "tensor",
        rr::archetypes::Tensor(
            rr::datatypes::TensorData{dimensions, rr::datatypes::TensorBuffer::i32(data)}
        )
    );
}
