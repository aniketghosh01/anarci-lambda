# The following imports are necessary for type-checking and editor integration.
from __future__ import annotations
import typing as t
import gzip
import csv

if t.TYPE_CHECKING:
   import ts_sdk.task as ts
# End imports related to type-checking and editor integration.

import json

def main(input: dict, context: ts.Context):

    ## constants
    IDSNAMESPACE = input["ids_namespace"]
    IDSTYPE = input["ids_type"]
    IDSVERSION = input["ids_version"]

    ## Add your logic
    file = context.read_file(input["input_file"])
    input_dict = json.loads(file["body"].decode("UTF-8"))
    
    input_dict["@idsNamespace"] = IDSNAMESPACE
    input_dict["@idsType"] = IDSTYPE
    input_dict["@idsVersion"] = IDSVERSION

    # Validate against IDS
    context.validate_ids(input_dict, IDSNAMESPACE, IDSTYPE, IDSVERSION)

    # write the IDS JSON to the data lake
    ngs_run = input_dict["fields"]["ngs_run"]["name"]
    ngs_pp = input_dict["fields"]["ngs_pp"]["name"]
    
    output = context.write_file(
        content=json.dumps(input_dict, indent=2, allow_nan=False),
        file_name=f"{ngs_run}_{ngs_pp}_meta_data.json",
        file_category="IDS",
        ids=f"{IDSNAMESPACE}/{IDSTYPE}:{IDSVERSION}",
    )

    print(output)
    return output
