import json
from http import HTTPStatus
from typing import Annotated, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Form, Query
from fastapi.params import Param, Path
from auth import authenticate
from api_exceptions import not_found_exception
from backend import NGSBackend, TDPBackend
from benchling.exceptions import NoAssayRunFoundForNGSRun
from schemas import ClonePoolPrimerInfo, ClonePrimerInfo, MutationAnalysis, MutationPurityAnalysis, NGSRunInfo
from schemas import PrimerInfo, MutationInfo, PurityAnalysis, RepertoireAnalysis, StatusResponse, User
from dependencies import ngs_backend, ts_backend

router = APIRouter(responses={404: {"description": "Not found"}})

@router.get("/info", response_model=StatusResponse)
async def get_info() -> StatusResponse:
    return StatusResponse(info="OK - API WRAPPER IS RUNNING!")

@router.get("/get-ts-fileinfo/{file_id}", response_model=None)
async def get_ts_fileinfo(file_id: str, backend: TDPBackend = Depends(ts_backend)):
    fileinfo, status = backend.retrieve_file_info(
        file_id = file_id
    )
    if not status.is_success:
        raise HTTPException(status_code=status.value)
    return fileinfo

@router.post("/upload-ts-file", response_model=None, status_code=HTTPStatus.CREATED)
async def upload_ts_file(file: UploadFile = File(...), labels: str = Query(...), backend: TDPBackend = Depends(ts_backend)):
    file_data = await file.read()
    fileid, status = backend.upload_raw_file(
        file_name = str(file.filename), 
        file_data = file_data, 
        content_type = str(file.content_type),
        labels = json.loads(labels)
    )
    if not status.is_success:
        raise HTTPException(status_code=status.value)
    return Response(content = fileid, status_code = status.value, media_type = "application/json")

@router.post("/upload-ts-metadata", response_model=None, status_code=HTTPStatus.CREATED)
async def upload_ts_meta(json_data: Dict[str, Any], labels: str = Query(...), backend: TDPBackend = Depends(ts_backend)):
    fileid, status = backend.upload_json_meta(json_data = json_data, labels = json.loads(labels))
    if not status.is_success:
        raise HTTPException(status_code=status.value)
    return Response(content = fileid, status_code = status.value, media_type = "application/json")


@router.get("/primer-information/{pp_id}", response_model=list[ClonePrimerInfo])
async def get_primer_info(pp_id: Annotated[str, Path(pattern="^NGS_PP")], 
                          backend: NGSBackend = Depends(ngs_backend)) -> list[ClonePrimerInfo]:
    return backend.get_primer_info(pp_id=pp_id)


@router.get("/mutation-information/{ngs_run_id}", response_model=list[MutationInfo])
async def get_mutation_info(
    ngs_run_id: Annotated[str, Path(pattern="^NGS_RUN")],
    backend: NGSBackend = Depends(ngs_backend),
) -> list[MutationInfo]:
    return backend.get_mutation_info(ngs_run_id=ngs_run_id)


@router.post("/purity-analysis", response_model=list[PurityAnalysis], status_code=HTTPStatus.CREATED)
async def upload_purity_analysis(purity_analysis: list[PurityAnalysis], backend: NGSBackend = Depends(ngs_backend)):
    try:
        return backend.save_purity_analysis(purity_analysis=purity_analysis)
    except NoAssayRunFoundForNGSRun:
        raise not_found_exception

@router.post("/repertoire-analysis", response_model=list[RepertoireAnalysis], status_code=HTTPStatus.CREATED)
async def upload_repertoire_analysis(repertoire_analysis: list[RepertoireAnalysis], backend: NGSBackend = Depends(ngs_backend)):
    try:
        return backend.save_repertoire_analysis(repertoire_analysis=repertoire_analysis)
    except NoAssayRunFoundForNGSRun:
        raise not_found_exception

@router.post("/purity-mutation-analysis", response_model=list[MutationPurityAnalysis], status_code=HTTPStatus.CREATED)
async def upload_purity_mutation_analysis(mutation_analysis: list[MutationPurityAnalysis], backend: NGSBackend = Depends(ngs_backend)):
    try:
        return backend.save_purity_mutation_analysis(mutation_analysis=mutation_analysis)
    except NoAssayRunFoundForNGSRun:
        raise not_found_exception

@router.get("/clone-pool-primer-information/{ngs_run_id}/{pp_id}")
async def get_clone_pool_primer_info(pp_id: Annotated[str, Path(pattern="^NGS_PP")],
                                     ngs_run_id: Annotated[str, Path(pattern="^NGS_RUN")], 
                                     backend: NGSBackend = Depends(ngs_backend)) -> list[ClonePoolPrimerInfo]:
    return backend.get_clone_pool_primer_info(pp_id=pp_id, ngs_run_id=ngs_run_id)

@router.get("/sample-type/{pp_id}")
async def get_sample_type(pp_id: Annotated[str, Path(pattern="^NGS_PP")],
                          backend: NGSBackend = Depends(ngs_backend)) -> str:
    return backend.get_sample_type(pp_id=pp_id)

@router.get("/ngs-run-information/{ngs_run_id}/{pp_id}")
async def get_ngs_run_info(pp_id: Annotated[str, Path(pattern="^NGS_PP")],
                            ngs_run_id: Annotated[str, Path(pattern="^NGS_RUN")], 
                                backend: NGSBackend = Depends(ngs_backend)) -> Dict[str, Any]:
    return backend.get_ngs_run_info(pp_id=pp_id, ngs_run_id=ngs_run_id)
