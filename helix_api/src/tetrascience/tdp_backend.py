from typing import Any, Callable, Optional, TypeVar, Dict
from http import HTTPStatus
import json
import re
import requests
import tempfile
from backend import TDPBackend
from schemas import BenchlingEntity
from ts_ids_core.schema import Pointer, Time, Software, System, User
from fastapi import File, UploadFile
from datetime import datetime

class TDPUploadBackend(TDPBackend):

    def __init__(self):
        super().__init__()

    # def from_dict(self, cls, entity_data: dict):
    #     nms = cls.model_fields.keys()  
    #     nms_data = {key: entity_data[key] for key in nms if key in entity_data}
    #     return cls(**nms_data)

    # def populate_schema(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
    #     ## benchling fields
    #     schema = {}
    #     for nm in ["ngs_run", "ngs_pp", "ngs_type", "project", "entry"]:
    #         schema[nm] = self.from_dict(BenchlingEntity, json_data[nm])
    #     ## other fields
    #     schema["software"] = self.from_dict(Software, json_data["software"])
    #     if "sequencer" in json_data and len(json_data["sequencer"]) > 0:
    #         schema["sequencer"] = self.from_dict(System, json_data["sequencer"])
    #     schema["user"] = self.from_dict(User, json_data["user"])
    #     schema["time"] = self.from_dict(Time, json_data["time"])
    #     ## file pointers
    #     if(len(json_data["files"]) > 0):
    #         ## Pointer expected type_ instead of type
    #         for file in json_data["files"]:
    #             file["type_"] = file.pop("type")  
    #         schema["files"] = [self.from_dict(Pointer, file) for file in json_data["files"]]
        
    #     fields = NGSPipelineMeta(**schema)
    #     return { "fields" : fields } 
        
    def retrieve_file_info(self, file_id: str) -> tuple[Dict, HTTPStatus]:
        
        response = requests.get(
            url = f"{self.settings.api_url}/fileinfo/file/{file_id}",
            headers = {
                "ts-auth-token" : self.settings.jwt_token,
                "x-org-slug" : self.settings.org_slug,
                "accept": "application/json"
            }   
        )
        if response.ok:
            response_json = response.json()
            response_json = {key: response_json[key] for key in ["fileId", "file"]}
        else:
            response_json = {}
            
        return response_json, HTTPStatus(response.status_code)     
        
    def upload_raw_file(self, file_name: str, file_data: bytes, content_type: str, labels: Dict[str, Any]) -> tuple[str, HTTPStatus]: 

        date_time_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")
        labels_json = [
            {"name": "ngs_run_id", "value": labels["ngs_run_id"]}, 
            {"name": "ngs_pp_id", "value": labels["ngs_pp_id"]},
            {"name": "sequencer_type", "value": labels["sequencer_type"]}
        ]
        if 'ngs_sample' in labels:
            labels_json.append({"name": "ngs_sample", "value": labels["ngs_sample"]})
        if 'ngs_fasta_file' in labels:
            labels_json.append({"name": "ngs_fasta_file", "value": labels["ngs_fasta_file"]})
        data = {
            "filename" : f"NGS/{date_time_prefix}_{file_name}",
            "tags": ["NGS", "Clone Pool", labels["sequencer_type"]],
            "sourceType": "ngs-pipeline-output-file",
            "labels": json.dumps(labels_json)
        }
        files = {
            "file": (file_name, file_data, content_type)
        }
        response = requests.post(
            url = f"{self.settings.api_url}/datalake/upload",
            data = data,
            files = files,
            headers = {
                "ts-auth-token" : self.settings.jwt_token,
                "x-org-slug" : self.settings.org_slug,
                "accept": "application/json"
            }
        )
        return str(response.text), HTTPStatus(response.status_code)
        
    def upload_json_meta(self, json_data: Dict[str, Any], labels: Dict[str, Any]) -> tuple[str, HTTPStatus]: 

        ## prepare/run query
        tmp = tempfile.NamedTemporaryFile(mode="w+", suffix = ".json", delete=False)
        json.dump(json_data, tmp)
        tmp_path = tmp.name
        tmp.close()
        
        ## prepare labels
        ngs_run = labels["ngs_run_id"]
        run = re.search(r'(RUN\d+)', ngs_run).group(1)
        ngs_pp = labels["ngs_pp_id"]
        
        data = {
            "filename" : f"NGS/{ngs_pp}_{run}.json",
            "tags": ["NGS", labels["ngs_type"], "Metadata", labels["sequencer_type"]],
            "sourceType": "ngs-pipeline-metadata",
            "labels": json.dumps([                                             ## not working
                {"name": "ngs_run_id", "value": ngs_run}, 
                {"name": "ngs_pp_id", "value": ngs_pp},
                {"name": "sequencer_type", "value": labels["sequencer_type"]}
            ])
        }
        files = {
            "file": open(tmp_path, "rb")
        }
               
        response = requests.post(
            url = f"{self.settings.api_url}/datalake/upload",
            data = data,
            files = files,
            headers = {
            "ts-auth-token" : self.settings.jwt_token,
            "x-org-slug" : self.settings.org_slug,
            "accept": "application/json"
            }
        )

        return str(response.text), HTTPStatus(response.status_code)





