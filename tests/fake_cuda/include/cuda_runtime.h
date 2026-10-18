#pragma once

using cudaError_t = int;
inline constexpr cudaError_t cudaSuccess = 0;

extern "C" cudaError_t cudaGetDevice(int* device);
extern "C" cudaError_t cudaSetDevice(int device);
