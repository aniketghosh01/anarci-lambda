import json
from pathlib import Path
from typing import ClassVar, List, Literal, Any, Dict
from dataclasses import dataclass, fields

from ts_ids_core.annotations import Required, Nullable
from ts_ids_core.base.ids_element import IdsElement, SchemaExtraMetadataType
from ts_ids_core.schema import IdsField, IdsSchema, RelatedFile, Time, Software, System, User

## Create schema
## -------------

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
    
class SequencerType(IdsElement):
    """Sequencer type
    
    :field name: type name (e.g. Illumina/Pacbio)
    :field serial_number: sequencer serial number  
    """
    name: Required[str]
    serial_number: Nullable[str]

class KumoFile(IdsElement):
    """Kumo file path
    
    :field name: kumo object path relative to s3 bucket 
    :field bucket: kumo s3 bucket path
    """
    name: Required[str]
    bucket: Required[str]
    
class NGSPipelineResults(IdsElement):
    """NGS-pipeline meta data fields
    
    :field ngs_run: Benchling NGS RUN
    :field ngs_pp: Benchling NGS PP
    :field ngs_type: Benchling NGS type (Clone/Clone Pool)
    :field project: Benchling project
    :field entry: Benchling notebook entry
    :field software: NGS-pipeline version
    :field sequencer: Sequencer details
    :field user: User details
    :field time: Creation time 
    :field kumo_files: List of NGS RUN files in Kumo
    :field related_files: List of NGS RUN related files in TDP
    """
    ngs_run: Required[BenchlingEntity]
    ngs_pp: Required[BenchlingEntity]
    ngs_type: Required[BenchlingEntity]
    project: Required[BenchlingEntity]
    entry: Required[BenchlingEntity]
    software: Required[Software]
    sequencer: SequencerType
    user: Required[User]
    time: Required[Time]
    kumo_files: List[KumoFile]
    related_files: List[RelatedFile]
    
class NGSPipelineSchema(IdsSchema):
    """NGS-pipeline meta data schema."""

    schema_extra_metadata: ClassVar[SchemaExtraMetadataType] = {
        "$id": "https://ids.tetrascience.com/private-bayer/ngs-pipeline/v2.0.0/schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
    }

    ids_namespace: Required[Literal["private-bayer"]] = IdsField(
        default="private-bayer", alias="@idsNamespace"
    )
    ids_type: Required[Literal["ngs-pipeline"]] = IdsField(
        default="ngs-pipeline", alias="@idsType"
    )
    ids_version: Required[Literal["v2.0.0"]] = IdsField(
        default="v2.0.0", alias="@idsVersion"
    )

    fields: Required[NGSPipelineResults]
    
## Export schema
## -------------

model_schema: Dict[str, Any] = NGSPipelineSchema.model_json_schema()
json_schema = json.dumps(model_schema, indent=2)

#print(json_schema)

output_path = Path("./files").joinpath("schema.json")
output_path.write_text(json_schema)

## Populate schema
## ---------------

## helper functions
def from_dict(cls, entity_data: dict):
        nms = cls.model_fields.keys()  
        nms_data = {key: entity_data[key] for key in nms if key in entity_data}
        return cls(**nms_data)

def populate_schema(data: Dict[str, Any]):
    ## benchling fields
    results = {}
    for nm in ["ngs_run", "ngs_pp", "ngs_type", "project", "entry"]:
        results[nm] = from_dict(BenchlingEntity, data[nm])
    ## other fields
    results["software"] = from_dict(Software, data["software"])
    if(len(data["sequencer"]) > 0):
        results["sequencer"] = from_dict(System, data["sequencer"])
    results["user"] = from_dict(User, data["user"])
    results["time"] = from_dict(Time, data["time"])
    ## file pointers
    if(len(data["files"]) > 0):
        ## Pointer expected type_ instead of type
        for file in data["files"]:
            file["type_"] = file.pop("type")  
        results["files"] = [from_dict(Pointer, file) for file in data["files"]]
    
    fields = NGSPipelineResults(**results)
    return NGSPipelineSchema(fields = fields)
    
## read json
data = json.loads(Path("./scripts/tdp/files/dummy_meta_data.json").read_text())

## populate schema
instance = populate_schema(data)
instance_json = instance.model_dump_json(indent = 2)  

## dump to file  
output_path = Path("./scripts/tdp/files").joinpath("ids_schema_data.json")
output_path.write_text(instance_json)
