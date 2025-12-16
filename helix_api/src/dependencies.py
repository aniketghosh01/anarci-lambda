from backend import (
    NGSBackend,
    BenchlingBackend,
    TDPBackend
)
from benchling.benchling_api import BenchlingAPIBackend
from benchling.ngs_backend import NGSBenchlingBackend
from caching import CacheManager
from tetrascience.tdp_backend import TDPUploadBackend

def cache_manager() -> CacheManager:
    return CacheManager()

def ngs_backend() -> NGSBackend:
    return NGSBenchlingBackend(cache_manager=cache_manager())

def benchling_api_backend() -> BenchlingBackend:
    return BenchlingAPIBackend()

def ts_backend() -> TDPBackend:
    return TDPUploadBackend()

