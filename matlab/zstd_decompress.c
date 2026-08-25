/*
 * zstd_decompress.c
 *
 * MATLAB MEX function that decompresses a Zstandard-compressed byte buffer.
 *
 * MATLAB usage:
 *   out = zstd_decompress(compressedData)
 *
 * Input:
 *   compressedData - uint8 row/column vector containing Zstandard-compressed bytes.
 *
 * Output:
 *   out - uint8 column vector containing the decompressed bytes.
 *
 * Build (requires libzstd headers/libs installed):
 *   Windows (vcpkg example):
 *     mex zstd_decompress.c -IC:\vcpkg\installed\x64-windows\include ...
 *         C:\vcpkg\installed\x64-windows\lib\zstd.lib
 *
 *   Linux/macOS (system libzstd):
 *     mex zstd_decompress.c -lzstd
 *
 * Requires: libzstd (https://github.com/facebook/zstd)
 */

#include "mex.h"
#include "matrix.h"
#include <zstd.h>
#include <stdint.h>
#include <string.h>

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{
    /* ---- Validate arguments ---- */
    if (nrhs != 1) {
        mexErrMsgIdAndTxt("zstd_decompress:invalidNumInputs",
                           "One input required: compressed uint8 array.");
    }
    if (nlhs > 1) {
        mexErrMsgIdAndTxt("zstd_decompress:invalidNumOutputs",
                           "Too many output arguments.");
    }
    if (!mxIsUint8(prhs[0]) || mxIsComplex(prhs[0])) {
        mexErrMsgIdAndTxt("zstd_decompress:invalidInput",
                           "Input must be a real uint8 array.");
    }

    const uint8_t *srcData = (const uint8_t *)mxGetData(prhs[0]);
    size_t srcSize = (size_t)mxGetNumberOfElements(prhs[0]);

    if (srcSize == 0) {
        /* Nothing to decompress; return empty uint8 array. */
        plhs[0] = mxCreateNumericMatrix(0, 0, mxUINT8_CLASS, mxREAL);
        return;
    }

    /* ---- Determine decompressed size ---- */
    unsigned long long const decompressedSizeHint =
        ZSTD_getFrameContentSize(srcData, srcSize);

    if (decompressedSizeHint == ZSTD_CONTENTSIZE_ERROR) {
        mexErrMsgIdAndTxt("zstd_decompress:notZstd",
                           "Input is not a valid Zstandard-compressed buffer.");
    }
    if (decompressedSizeHint == ZSTD_CONTENTSIZE_UNKNOWN) {
        mexErrMsgIdAndTxt("zstd_decompress:unknownSize",
                           "Decompressed size is unknown; the compressed "
                           "stream must have been created with content size "
                           "written to the frame header.");
    }

    mwSize dstSize = (mwSize)decompressedSizeHint;

    /* ---- Allocate output MATLAB array ---- */
    plhs[0] = mxCreateNumericMatrix(dstSize, 1, mxUINT8_CLASS, mxREAL);
    if (dstSize == 0) {
        return;
    }
    uint8_t *dstData = (uint8_t *)mxGetData(plhs[0]);

    /* ---- Decompress ---- */
    size_t const actualDecompressedSize =
        ZSTD_decompress(dstData, (size_t)dstSize, srcData, srcSize);

    if (ZSTD_isError(actualDecompressedSize)) {
        mexErrMsgIdAndTxt("zstd_decompress:decompressFailed",
                           "Zstandard decompression failed: %s",
                           ZSTD_getErrorName(actualDecompressedSize));
    }

    if (actualDecompressedSize != (size_t)dstSize) {
        /* Resize output to actual decompressed size, if different. */
        mxSetM(plhs[0], actualDecompressedSize);
    }
}
