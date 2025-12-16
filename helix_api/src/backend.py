from typing import Dict, Any
from schemas import ClonePoolPrimerInfo, ClonePrimerInfo, MutationPurityAnalysis, MutationInfo, PurityAnalysis, RepertoireAnalysis
from http import HTTPStatus
from caching import CacheManager
from config import get_settings, get_tdp_settings
from fastapi import UploadFile
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling

class BenchlingBackend:

    def __init__(self):
        settings=get_settings()
        auth_method = ClientCredentialsOAuth2(
            client_id=settings.client_id, client_secret=settings.client_secret
        )
        self.benchling = Benchling(url=settings.base_url, auth_method=auth_method)
        self.settings = settings

class NGSBackend(BenchlingBackend):
    
    cache_manager: CacheManager
    
    def get_primer_info(self, pp_id: str) -> list[ClonePrimerInfo]:
        pass

    def get_clone_pool_primer_info(self, pp_id: str, ngs_run_id: str) -> list[ClonePoolPrimerInfo]:
        pass

    def get_sample_type(self, pp_id: str) -> str:
        pass

    def get_mutation_info(self, ngs_run_id: str) -> list[MutationInfo]:
        pass

    def get_ngs_run_info(self, pp_id: str, ngs_run_id: str) -> Dict[str, Any]:
        pass

    def save_purity_analysis(self, purity_analysis: list[PurityAnalysis]) -> list[PurityAnalysis]:
        pass

    def save_repertoire_analysis(self, repertoire_analysis: list[RepertoireAnalysis]) -> list[RepertoireAnalysis]:
        pass

    def save_purity_mutation_analysis(self, mutation_analysis: list[MutationPurityAnalysis]) -> list[MutationPurityAnalysis]:
        pass

class TDPBackend:

    def __init__(self):
        self.settings=get_tdp_settings()

    def retrieve_file_info(self, file_id: str) -> tuple[Dict, HTTPStatus]:
        pass

    def upload_raw_file(self, file_name: str, file_data: bytes, content_type: str, labels: Dict) -> tuple[Dict, HTTPStatus]:
        pass

    def upload_json_meta(self, json_data: Dict[str, Any], labels: Dict) -> tuple[str, HTTPStatus]:
        pass
    