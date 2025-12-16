### author: joris.chau.ext@bayer.com

from typing import Dict, Any
import os
import logging
import tempfile
import pandas as pd
from pathlib import Path
from task_script_utils.workflow_logging import setup_ts_log_handler
from io import BytesIO

## for testing
is_context_defined = True
try:
    context
except NameError:
    is_context_defined = False 

if not is_context_defined:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path = os.path.join(os.getcwd(), ".env"))

## DEV
entity_ids = {
    "registry_id": "src_dlAQySkQ",
    "folder_id": "lib_zOUTY6UY",
    "author_id": ["ent_5pFSwAFU", "ent_zxs060cj"],   ## Stelios + Jonas
    "scfv_run_schema_id": "assaysch_oedNJoG6",
    "feature_aa_schema_id": "ts_RcJul02H",
    "variable_region_schema_id": "ts_hFEAmeKW",
    "function_vh_id": "sfso_ecN5bXaX",
    "function_vl_id": "sfso_ARafpQ72"
}

## QA
# entity_ids = {
#     "registry_id": "src_YfjrZwrO",
#     "folder_id": "lib_V5iEOG50",
#     "author_id": ["ent_ZzgQvYNc", "ent_KCLuukw5"],   ## Stelios + Jonas
#     "scfv_run_schema_id": "assaysch_ft2eK29l",
#     "feature_aa_schema_id": "ts_7PBsIdck",
#     "variable_region_schema_id": "ts_MvhZgIRm",
#     "function_vh_id": "sfso_tTEZucdK",
#     "function_vl_id": "sfso_jgCEQ7uA"
# }

## helpers
def read_fasta_to_df(fasta_bytes: BytesIO):
    """
    Reads a FASTA file into a pandas DataFrame with 'name' and 'seq' columns.

    Parameters:
        fasta_bytes (BytesIO): FASTA file content.

    Returns:
        Dict with lists 'name' and 'seq'.
    """
    headers = []
    sequences = []
    current_seq = []
    current_header = None

    for line in fasta_bytes:
        line = line.decode("utf-8").strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_header:
                headers.append(current_header)
                sequences.append("".join(current_seq))
            current_header = line[1:]  # remove '>'
            current_seq = []
        else:
            current_seq.append(line)

    # append final sequence
    if current_header:
        headers.append(current_header)
        sequences.append("".join(current_seq))

    return {'name': headers, 'seq': sequences}

def split_scfv(sequence, linker, logger, orientation_vhvl=True):
    """
    Splits a scFv amino acid sequence into VH and VL domains using the linker.

    Parameters:
        sequence (str): Full scFv amino acid sequence.
        linker (str): Amino acid sequence of the linker.
        orientation_vhvl (bool): Is orientation VH-linker-VL? Alternative is VL-linker-VH

    Returns:
        tuple: (VH, VL) if linker is found, else returns ('', '').
    """
    sequence = sequence.strip().upper()
    linker_pos = sequence.find(linker)

    if linker_pos == -1:
        logger.error(f"Linker `{linker}` not found in `{sequence}`.")
        return '', ''

    if orientation_vhvl:
        vh = sequence[:linker_pos]
        vl = sequence[linker_pos + len(linker):]
    else: 
        vl = sequence[:linker_pos]
        vh = sequence[linker_pos + len(linker):]

    return vh, vl


def get_label(label_name, labels_list):
    return list(filter(lambda x: x['name'] == label_name, labels_list))[0]['value']
    
def get_assay_run(benchling_sdk, schema_id, notebook_id, filename):
    iterator = benchling_sdk.assay_runs.list(
        schema_id = schema_id
    )
    assay_run = None
    for page in iterator:
        for run in page:
            ## match filename
            run_filename = run.fields["sharepoint_filename_fasta"].text_value or ""
            if run_filename == filename:
                ## match notebook id
                run_notebook = benchling_sdk.entries.get_entry_by_id(run.entry_id)
                if run_notebook.display_id == notebook_id:
                    if assay_run is None:
                        assay_run = run 
                    elif run.created_at > assay_run.created_at:
                        assay_run = run
    return assay_run

def resolve_msg_vr_ids(benchling_sdk, result, schema_id):    
    import re
    import pandas as pd
    msg = [entity["message"] for entity in result["errors"]]
    res_df = pd.DataFrame()
    for i in range(len(result["errors"])):
        msg = result["errors"][i]["message"]
        vr_name = re.findall(r'"(.*?)"', msg)[0]
        vr_name = re.sub(r"\s*\(.*\)", "", vr_name)
        query = benchling_sdk.custom_entities.list(
            name = vr_name,
            schema_id = schema_id
        )
        vr_id = query.first()
        new_row = pd.DataFrame({
           "index": [result["errors"][i]["index"]], 
           "vr_id": [vr_id.id]
        })
        res_df = pd.concat([res_df, new_row], ignore_index = True)
    return res_df 

def register_entities(benchling_sdk, type, data, entity_ids, logger):
    import pandas as pd
    def complete_response(benchling_sdk, body, result, schema_id, prefix="", newcol=True):
        import pandas as pd
        if result["status"] == 'SUCCEEDED':
            response = result["response"]
            res_df = pd.DataFrame({
                "seq": [entity["aminoAcids"] for entity in response["aaSequences"]],
                "id": [entity["id"] for entity in response["aaSequences"]],
                "new": [True] * len(response["aaSequences"])
            })
        else:
            failed_ids = [entity["index"] for entity in result["errors"]]
            res_df = pd.DataFrame()
            for i in range(len(failed_ids)):
                query = benchling_sdk.aa_sequences.list(
                    amino_acids=body[failed_ids[i]]["aminoAcids"],
                    schema_id=schema_id
                )
                entity = query.first()
                new_row = pd.DataFrame({
                    "seq": [entity.amino_acids],
                    "id": [entity.id],
                    "new": [False]
                })
                res_df = pd.concat([res_df, new_row], ignore_index=True)
        if not newcol:
            res_df = res_df.drop(columns = ["new"])
        res_df.columns = prefix + res_df.columns
        return res_df    
    def complete_task(benchling_sdk, query, endpoint, logger):
        import json
        import time
        if query.status_code != 202:
            raise ConnectionError(f"{endpoint} failed with status: {query.status_code}")
        taskId = json.loads(query.content)["taskId"]
        while True:
            res= benchling_sdk.api.get_response(url=f"api/v2/tasks/{taskId}")
            if res.status_code != 200:
                raise ConnectionError(f"api/v2/tasks/{taskId} query failed with status: {res.status_code}")
            result = res.parsed
            status = result["status"]
            logger.info(f"task status: {status}")
            if status == "RUNNING": 
                time.sleep(5)  
            else:
                if status != 'SUCCEEDED':
                    logger.info(f"{endpoint} failed with message(s): {result['errors'][0]['message']}")
                break
        return result
    def resolve_msg_vr_ids(benchling_sdk, result, schema_id):    
        import re
        import pandas as pd
        msg=[entity["message"] for entity in result["errors"]]
        res_df=pd.DataFrame()
        for i in range(len(result["errors"])):
            msg=result["errors"][i]["message"]
            vr_name=re.findall(r'"(.*?)"', msg)[0]
            vr_name=re.sub(r"\s*\(.*\)", "", vr_name)
            query=benchling_sdk.custom_entities.list(
                name=vr_name,
                schema_id=schema_id
            )
            vr_id=query.first()
            new_row=pd.DataFrame({
            "index": [result["errors"][i]["index"]], 
            "vr_id": [vr_id.id]
            })
            res_df=pd.concat([res_df, new_row], ignore_index=True)
        return res_df 
    
    df = data.copy(deep=True)
    body = []
    for i in range(df.shape[0]):
        if type!="vr":
            schema_id=entity_ids["feature_aa_schema_id"]
            namingStrategy="NEW_IDS"
            aminoAcids=df[type][i]
            if type =="vh":
                prefix="[VH][AA] "
                fields={"Function(s)": {"value": entity_ids["function_vh_id"]}}
            else:
                prefix="[VL][AA] "
                fields={"Function(s)": {"value": entity_ids["function_vl_id"]}}
        else:
            prefix=""
            namingStrategy="DELETE_NAMES"
            schema_id=entity_ids["variable_region_schema_id"]
            fields={"VH": {"value": df["vh_id"][i]}, "VL": {"value": df["vl_id"][i]}}
            aminoAcids=None
        entry={
            "name": prefix + df["name"][i],
            "aliases": [],
            "authorIds": entity_ids["author_id"],
            "fields": fields,
            "folderId": entity_ids["folder_id"],
            "schemaId": schema_id,
            "registryId": entity_ids["registry_id"],
            "namingStrategy": namingStrategy,
            "aminoAcids": aminoAcids
        }
        if type=="vr":
            del entry["aminoAcids"]
        body.append(entry)
        
    endpoint = "api/v2/custom-entities:bulk-create" if type=="vr" else "api/v2/aa-sequences:bulk-create" 
    query_body = {"customEntities": body} if type=="vr" else {"aaSequences": body}
    query = benchling_sdk.api.post_response(
        url = endpoint,
        body = query_body
    )
    result = complete_task(benchling_sdk, query, endpoint, logger)
    if result["status"] != "SUCCEEDED":
        logger.info(result)
    if type!="vr":
        df1 = complete_response(benchling_sdk, body, result, entity_ids["feature_aa_schema_id"], prefix=type+"_")
        df = pd.merge(df, df1, left_on = type, right_on = type + "_seq", how = "left")
        df = df.drop(columns = type + "_seq")
    else:
        if result["status"] != "SUCCEEDED":
            vr_ids = resolve_msg_vr_ids(benchling_sdk, result, entity_ids["variable_region_schema_id"])
            df["vr_id"] = pd.NA
            df["vr_new"] = pd.NA
            for id in range(vr_ids.shape[0]):
                df.loc[vr_ids.loc[id, "index"], "vr_id"] = vr_ids.loc[id, "vr_id"]
                df.loc[vr_ids.loc[id, "index"], "vr_new"] = False
        else:
            entities = result["response"]["customEntities"]
            df1 = pd.DataFrame({
                "vr_id": [entity["id"] for entity in entities],
                "vh_id": [entity["fields"]["VH"]["value"] for entity in entities],
                "vl_id": [entity["fields"]["VL"]["value"] for entity in entities],
                "vr_new": [True] * len(entities)
            })
            df = pd.merge(df, df1, on = ["vh_id", "vl_id"], how = "left")  
    ## re-register
    if df[type+"_id"].isna().any():
        new_ids = df[df[type+"_id"].isna()].index
        new_body = [body[i] for i in new_ids]
        query_body = {"customEntities": new_body} if type=="vr" else {"aaSequences": new_body}
        query = benchling_sdk.api.post_response(url=endpoint, body=query_body)
        result = complete_task(benchling_sdk, query, endpoint, logger)
        if type!="vr":
            df1 = complete_response(benchling_sdk, new_body, result, entity_ids["feature_aa_schema_id"], prefix=type+"_", newcol=False)
            df = pd.merge(df, df1, left_on = type, right_on = type+"_seq", how = "left", suffixes=("_x", "_y"))
            df[type+"_id"] = df[[type+"_id_x", type+"_id_y"]].bfill(axis=1).iloc[:, 0]
            df.drop(columns = [type+"_id_x", type+"_id_y"], inplace = True)
        else:
            entities = result["response"]["customEntities"]
            df_vr = pd.DataFrame({
                "vr_id": [entity["id"] for entity in entities],
                "vh_id": [entity["fields"]["VH"]["value"] for entity in entities],
                "vl_id": [entity["fields"]["VL"]["value"] for entity in entities],
            })
            df = pd.merge(df, df_vr, on = ["vh_id", "vl_id"], how = "left", suffixes=("_x", "_y")) 
            df["vr_id"] = df[["vr_id_x", "vr_id_y"]].bfill(axis=1).iloc[:, 0]
            df.drop(columns = ["vr_id_x", "vr_id_y"], inplace = True)
    df[type+"_new"] = df[type+"_new"].fillna(True)
    return df
    
## setup
if is_context_defined:
    benchling_sdk = benchling.sdk
    setup_ts_log_handler(context.get_logger(), __name__)
    logg = logging.getLogger(__name__)
else:
    from benchling_sdk.benchling import Benchling
    from benchling_sdk.auth.api_key_auth import ApiKeyAuth
    auth_method = ApiKeyAuth(api_key = os.getenv("BENCHLING_API_KEY", ""))
    benchling_sdk = Benchling(url="https://bayer-dev.benchling.com", auth_method=auth_method)
    benchling = None   ## not available
    logg = logging.getLogger()
    logg.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    if not logg.hasHandlers():
        logg.addHandler(console_handler)

## context data
if is_context_defined:
    input_file_pointer = context.input_file
    file = context.read_file(input_file_pointer, form='body')
    filename = context.get_file_name(input_file_pointer)
    labels = context.get_labels(input_file_pointer)
else:
    ## for testing
    with open("dummy_scfv10.fasta", "rb") as file:
        byte_array = file.read() 
    file = {"body": byte_array}
    filename = "dummy_scfv10.fasta"
    labels = [{"name": "notebook_id", "value": "EXP25000345"}]
    
## parse fasta content   
df = read_fasta_to_df(BytesIO(file["body"]))
df = pd.DataFrame(df)
logg.info(df.head())

## fetch parameters from benchling
notebook_id = get_label("notebook_id", labels)
assay_run = get_assay_run(benchling_sdk, entity_ids["scfv_run_schema_id"], notebook_id, filename)
if assay_run is None:
    raise ValueError("No associated benchling assay run found")
logg.info(assay_run)
orientation_vhvl = (assay_run.fields["orientation_vh_vl"].text_value == 'true')
linker = benchling_sdk.aa_sequences.get_by_id(assay_run.fields["linker"].value)
linker = linker.amino_acids
logg.info({
    "orientation VH-VL": orientation_vhvl,
    "linker": linker,
    "notebook_id": notebook_id
})

## split sequences
vh_list = []
vl_list = []
for seq in df["seq"]:
    vh, vl = split_scfv(seq, logger = logg, orientation_vhvl = orientation_vhvl, linker = linker)
    if vh == '':
        raise ValueError(f"Linker {linker} not found in {seq}.")
    vh_list.append(vh)
    vl_list.append(vl)
df["vh"] = vh_list
df["vl"] = vl_list
df["linker"] = assay_run.fields["linker"].value
logg.info(df.head())

## register VH sequences
df = register_entities(
    benchling_sdk=benchling_sdk,
    type="vh",
    data=df,
    entity_ids=entity_ids,
    logger=logg
)
logg.info(df.head())

## register VL sequences
df = register_entities(
    benchling_sdk=benchling_sdk,
    type="vl",
    data=df,
    entity_ids=entity_ids,
    logger=logg
)
logg.info(df.head())

## register variable regions
df = register_entities(
    benchling_sdk=benchling_sdk,
    type="vr",
    data=df,
    entity_ids=entity_ids,
    logger=logg
)
logg.info(df.head())

## create blob
filename_csv=os.path.splitext(filename)[0] + '.csv'
df["comment"]=df.apply(lambda row: "".join([
        "VH already registered; " if not row["vh_new"] else "",
        "VL already registered; " if not row["vl_new"] else "",
        "VR already registered" if not row["vr_new"] else "VR newly registered" if not row["vh_new"] or not row["vl_new"] else ""
    ]).strip("; "),
    axis=1)
blob_df=df[["name","vh_id","vl_id","linker","vr_id","comment"]]
if len(assay_run.fields["ngs_run"].value):
    ngs_runs=assay_run.fields["ngs_run"].value
    if isinstance(ngs_runs, list):
        ngs_runs=",".join(ngs_runs)
    blob_df.insert(0,"ngs_run",str(ngs_runs))
with tempfile.NamedTemporaryFile(mode='w',delete=False,suffix='.csv') as tmpfile:
    blob_df.to_csv(tmpfile.name,index=False)
    blob=benchling_sdk.blobs.create_from_file(file_path = Path(tmpfile.name), name = filename_csv)

## write blob to lab autorun
if is_context_defined:
    task = benchling.process_output(
        run=assay_run.id,
        name="ScFv Output File",
        blob=blob.id
    )

logg.info('Completed successfully')