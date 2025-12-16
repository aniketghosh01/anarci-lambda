from typing import List, Generic, Optional, TypeVar
from uuid import UUID
from pydantic import BaseModel, Field

from ts_ids_core.annotations import Required, Nullable
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.schema import Pointer, Time, Software, System, User

class oauth2User(BaseModel):
    login: str
    id: UUID

class StatusResponse(BaseModel):
    info: str

class PrimerInfo(BaseModel):
    fwdIsSymmetric: bool | None
    fwdIsUnsymetric: bool | None
    fwdRobustness: float | None
    fwdDirection: str
    fwdPrimer: str
    fwdPrimerType: str
    fwdBcSequence: str
    fwdPrimerSequence: str
    revIsSymetric: bool | None
    revIsUnsymetric: bool | None
    revRobustness: float | None
    revDirection: str
    revPrimer: str
    revPrimerType: str
    revBcSequence: str
    revPrimerSequence: str
    pcrPlate: str

class MutationInfo(BaseModel):
    trimLeft: str | None
    trimRight: str | None
    optimizationClonePool: str | None
    referenceAA: str
    referenceDNA: str
    referenceMutations: list

class ClonePrimerInfo(PrimerInfo):
    wellId: str
    CL: str

class ClonePoolPrimerInfo(PrimerInfo):
    CLP: str
    amplicon: Optional[bool]

class Analysis(BaseModel):
    ngsRun: str = Field(alias='NGS Run')

class PurityAnalysis(BaseModel):
    sampleRegistryId: str = Field(alias="Sample Registry ID")
    wellPosition: str = Field(alias="Well Position")
    samplePlateBarcode: str = Field(alias='Sample Plate Barcode')
    sequenceType: str = Field(alias='Sequence Type')
    dnaSequence: str = Field(alias='DNA Sequence')
    mix: str = Field(alias='Mix')
    count: int = Field(alias='Count')
    proc: float = Field(alias='Proc')
    numSeq: int = Field(alias='NumSeq')
    sumCount: int = Field(alias='SumCount')
    inProc: float = Field(alias='InProc')
    score: float = Field(alias='Score')
    score2: float = Field(alias='Score2')

    class Config:
        allow_population_by_alias = True

class RepertoireAnalysis(Analysis):
    platform: str = Field(alias ='Platform')
    clonePool: str = Field(alias = "Clone Pool")
    totalReads: str = Field(alias = "Total Reads")
    pairedReads: str = Field(alias = "Paired Reads")
    passedQC: str = Field(alias = "Passed QC")
    demuxedReads: str = Field(alias = "Demuxed reads")
    distinctSeq: str = Field(alias = "Distinct seq")
    nrZOTU: str = Field(alias = "nr ZOTU")
    ZOTUTotalCount: str = Field(alias = "ZOTU total count")
    nrChimeras: str = Field(alias = "nr Chimeras")
    nrNonChimeras: str = Field(alias = "nr non-Chimeras")
    clusteredSeq: str = Field(alias = "Clustered seq")
    nrClusters: str = Field(alias = "nr Clusters")

class MutationAnalysis(BaseModel):
    clone: str = Field(alias = "Clone")
    wellPosition: str = Field(alias="Well Position")
    samplePlateBarcode: str = Field(alias="Sample Plate Barcode")
    sequenceType: str = Field(alias='Sequence Type')
    CP: str = Field(alias = "CP")
    mix: str = Field(alias = "Mix")
    vhMutNum: int = Field(alias = "VH-MutNum")
    vhMut: str = Field(alias = "VH-Mut")
    expectedMutations: str = Field(alias = "Expected mutations")
    nonExpectedMutations: str = Field(alias = "Non-expected mutations")

# class PurityAnalysisVH(BaseModel):
#     clone: str = Field(alias = "Clone")
#     mix: str = Field(alias = "Mix")
#     DNA: str = Field(alias = "DNA")
#     vhCount: int = Field(alias = "VH-Count")
#     vhProc: float = Field(alias = "VH-Proc")
#     vhNumSeq: int = Field(alias = "VH-NumSeq")
#     vhSumCount: int = Field(alias = "VH-SumCount")
#     vhInProc: float = Field(alias = "VH-InProc")
#     vhScore: float = Field(alias = "VH-Score")
#     vhScore2: float = Field(alias = "VH-Score2")

class MutationPurityAnalysis(Analysis):
    mutationAnalysis: list[MutationAnalysis] = Field(alias = "mutation_analysis")
    purityAnalysis: list[PurityAnalysis] = Field(alias = "purity_analysis")

class BenchlingEntity(IdsElement):
    """Benchling entity schema

    :field name: benchling entity name
    :field benchling_api_id: benchling api id  
    :field benchling_registry_id: benchling registry id
    :field benchling_schema_id: benchling schema id
    """
    name: Required[str]
    benchling_api_id: Nullable[str]
    benchling_registry_id: Nullable[str]
    benchling_schema_id: Nullable[str]

class NGSRunInfo(IdsElement):
    """NGS-run benchling meta data 
    
    :field ngs_run: Benchling NGS RUN
    :field ngs_pp: Benchling NGS PP
    :field ngs_type: Benchling NGS type (Clone/Clone Pool)
    :field project: Benchling project
    :field entry: Benchling notebook entry
    """
    ngs_run: Required[BenchlingEntity]
    ngs_pp: Required[BenchlingEntity]
    ngs_type: Required[BenchlingEntity]
    project: Required[BenchlingEntity]
    entry: Required[BenchlingEntity]
    user: Required[User]
