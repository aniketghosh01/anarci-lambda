from typing import Dict, Any, List
import pandas as pd
import json
import time
from benchling.benchling_api import BenchlingAPIBackend

## helper functions
def map_uuid_id(uuids: List[str], lookup: pd.DataFrame):
    uuid_df = pd.DataFrame({ "uuid": uuids })
    uuid_df = pd.merge(uuid_df, lookup[["uuid", "id"]], on = "uuid", how = "left")
    ids = uuid_df["id"]
    ids = ids.where(pd.notna(ids), None).tolist()
    return ids

def map_field_id(values: List[str], lookup: pd.DataFrame):
    value_df = pd.DataFrame({ "name": values })
    value_df = pd.merge(value_df, lookup[["name", "id"]], on = "name", how = "left")
    ids = value_df["id"]
    ids = ids.where(pd.notna(ids), None).tolist()
    return ids

def map_uuid_id_multi(uuids: List, lookup: pd.DataFrame):
    uuids_res = uuids.copy()
    for i in range(len(uuids)):
        if uuids[i] is not None:
            ids = pd.merge(pd.DataFrame({"uuid": uuids[i]}), lookup[["uuid", "id"]], on = "uuid")
            if ids.shape[0] == len(uuids[i]):
                uuids_res[i] = ids["id"].tolist()
            else:
                uuids_res[i] = None
    return uuids_res

def map_field_id_multi(values: List, lookup: pd.DataFrame):
    values_res = values.copy()
    for i in range(len(values)):
        if values[i] is not None:
            ids = pd.merge(pd.DataFrame({"name": values[i]}), lookup[["name", "id"]], on = "name")
            if ids.shape[0] == len(values[i]):
                values_res[i] = ids["id"].tolist()
            else:
                values_res[i] = None
    return values_res

def map_error_uuid(response: Dict[str, Any], body: Dict[str, Any]):
    err_df = pd.DataFrame({
        "idx": [entity["index"] for entity in response],
        "message": [entity["message"] for entity in response]
    })
    err_df = err_df.groupby("idx")["message"].agg("; ".join).reset_index()    
    uuid_df = pd.DataFrame({
        "idx": list(range(len(body))),
        # "id": [entity["id"] for entity in body],
        "uuid": [entity["customFields"]["UUID"]["value"] for entity in body] # TODO: adjust to id
    })
    err_df = pd.merge(err_df, uuid_df, on = "idx", how = "left")
    return err_df[["uuid", "idx", "message"]]

def query_loop(benchling: BenchlingAPIBackend, body: Dict[str, Any], endpoint: str, sleep: int = 30):
    query = benchling.benchling.api.post_response(
        url = f"api/v2/{endpoint}",
        body = body
    )
    if query.status_code != 202:
        raise ValueError(f"POST query failed with status code: {query.status_code}")
    taskId = json.loads(query.content)["taskId"]
    while True:
        res = benchling.benchling.api.get_response(
            url = f"api/v2/tasks/{taskId}"
        )
        if res.status_code != 200:
            raise ValueError(f"Task ID query failed with status code: {res.status_code}")
        result = res.parsed
        status = result["status"]
        print(f"status: {status}")
        if status == "RUNNING": 
            time.sleep(sleep)   ## check again after 30s
        else:
            break
    return result   
