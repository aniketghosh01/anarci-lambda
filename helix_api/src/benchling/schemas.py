from typing import Any, Dict, List
from pydantic import BaseModel

from dataclasses import dataclass, fields
from dataclasses_json import config
from benchling_sdk.helpers.serialization_helpers import DeserializableModel, SerializableModel

class NGSPPPlate(BaseModel):
    pcr_plate: str
    plate_id: str

class PCRPlateMatch(BaseModel):
    fwd_plate: str
    rev_plate: str
    sample_plate: str

class FwdRevPrimerInfo(BaseModel):
    isSymetric: bool | None
    isUnsymetric: bool | None
    robustness: float | None
    direction: str
    primer: str
    primerType: str
    bcSequence: str
    primerSequence: str

class FwdRevClonePrimerInfo(FwdRevPrimerInfo):
    wellId: str
    pcrPlate: str
    
    def __init__(self, primerInfo: FwdRevPrimerInfo, wellId: str, pcrPlate: str):
        super().__init__(isSymetric = primerInfo.isSymetric,
        isUnsymetric = primerInfo.isUnsymetric,
        robustness = primerInfo.robustness,
        direction = primerInfo.direction,
        primer = primerInfo.primer,
        primerType = primerInfo.primerType,
        bcSequence = primerInfo.bcSequence,
        primerSequence = primerInfo.primerSequence,
        wellId=wellId, pcrPlate=pcrPlate)

# class ReferenceData(BaseModel):
#     sequenceAA: str = ""
#     sequenceDNA: str = ""
#     mutations: list[str] = []

class SamplePrimerInfo(BaseModel):
    wellId: str
    CL: str


@dataclass
class BaseEntityPost(SerializableModel):
    name: str
    aliases: List[str] 
    authorIds: List[str]
    fields: Dict[str, Any]
    customFields: Dict[str, Any]
    folderId: str
    schemaId: str
    registryId: str
    namingStrategy: str

    @classmethod
    def from_dict(cls, data: dict):
        nms = {f.name for f in fields(cls)}  
        nms_data = {key: data[key] for key in nms if key in data}
        return cls(**nms_data)

@dataclass
class BaseEntityGet(DeserializableModel):
    ## attributes to return 
    id: str
    name: str
    folderId: str

@dataclass 
class SequenceAAPost(BaseEntityPost):
    aminoAcids: str
    annotations: List[Dict]

@dataclass
class SequenceDNAPost(BaseEntityPost):
    bases: str
    isCircular: bool
    