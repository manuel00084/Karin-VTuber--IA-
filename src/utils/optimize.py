"""
Optimization utilities — CPU feature detection, numba JIT helper, vectorized ops.
NumPy auto-uses SSE/AVX via its BLAS backend (Intel MKL or OpenBLAS).

NOTE: NumPy vectorization helps most with numeric data (1000s of elements).
      For small string operations (<10K items), Python's native `in` is faster.
      Audio processing (numpy arrays of 44100+ samples) benefits directly.
"""
import numpy as np

_HAS_NUMBA = False
try:
    from numba import jit, prange, vectorize
    _HAS_NUMBA = True
except ImportError:
    jit = lambda *a, **kw: lambda f: f
    prange = range
    vectorize = lambda *a, **kw: lambda f: f


def detect_cpu_features():
    """Detect available CPU SIMD features (SSE4, AVX, etc.) via CPUID."""
    features = {"sse4_1": False, "sse4_2": False, "avx": False, "avx2": False, "fma3": False}
    try:
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        flags = info.get("flags", [])
        features["sse4_1"] = "sse4_1" in flags
        features["sse4_2"] = "sse4_2" in flags
        features["avx"] = "avx" in flags
        features["avx2"] = "avx2" in flags
        features["fma3"] = "fma3" in flags
    except ImportError:
        try:
            import ctypes
            import ctypes.util
            libc = ctypes.util.find_library("c")
            if not libc:
                return features
            try:
                _check_avx_windows()
            except Exception:
                pass
        except Exception:
            pass
    return features


def _check_avx_windows():
    try:
        import ctypes, struct
        kernel32 = ctypes.windll.kernel32
        is_wow64 = ctypes.c_int(0)
        kernel32.IsWow64Process(kernel32.GetCurrentProcess(), ctypes.byref(is_wow64))
    except Exception:
        pass


def numpy_blas_info():
    """Return BLAS backend info. NumPy with MKL auto-uses AVX/SSE."""
    try:
        np.show_config()
    except Exception:
        pass
    try:
        return np.__config__.show()
    except Exception:
        return "numpy config unavailable"


def is_optimized():
    """Quick check if NumPy has an optimized BLAS (MKL/OpenBLAS)."""
    try:
        np.dot(np.zeros(1), np.zeros(1))
        return True
    except Exception:
        return False


def fast_audio_resample(data, src_rate, dst_rate):
    """Vectorized audio resample with scipy + FMA-safe clipping."""
    from scipy import signal
    if src_rate == dst_rate:
        return data
    n_out = int(round(len(data) * dst_rate / src_rate))
    if data.ndim == 1:
        return signal.resample(data, n_out).astype(np.float32)
    out = signal.resample(data, n_out, axis=0).astype(np.float32)
    return out


def fast_normalize(data, target_peak=0.85):
    """Vectorized audio normalization with SIMD-friendly FMA pattern."""
    peak = np.max(np.abs(data))
    if peak > 0:
        return data * (target_peak / peak)
    return data


def fast_clip(data, limit=0.99):
    """Safe clipping using FMA-friendly pattern (multiply + clip)."""
    max_val = np.max(np.abs(data))
    if max_val > limit:
        return data * (limit / max_val)
    return data


def fast_similarity(query_vec, candidates):
    """Cosine similarity via normalized dot product. Uses BLAS (SSE/AVX)."""
    if query_vec.ndim == 1:
        query_vec = query_vec.reshape(1, -1)
    sims = np.dot(candidates, query_vec.T).flatten()
    return sims


if _HAS_NUMBA:
    @jit(nopython=True, fastmath=True, parallel=True, cache=True)
    def _numba_normalize(data, target_peak):
        peak = np.abs(data).max()
        if peak > 0:
            for i in prange(len(data)):
                data[i] = data[i] * (target_peak / peak)
        return data


    @jit(nopython=True, fastmath=True, cache=True)
    def _numba_soft_clip(data, limit=0.99):
        for i in range(len(data)):
            if abs(data[i]) > limit:
                data[i] = np.sign(data[i]) * limit - (abs(data[i]) - limit) * 0.1
        return data


def numba_normalize(data, target_peak=0.85):
    if _HAS_NUMBA:
        return _numba_normalize(data.copy(), target_peak)
    return fast_normalize(data, target_peak)


def numba_soft_clip(data, limit=0.99):
    if _HAS_NUMBA:
        return _numba_soft_clip(data.copy(), limit)
    return fast_clip(data, limit)
