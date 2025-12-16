import os

from helix_api.src import annotation
root_folder = os.path.join(os.path.expanduser("~"), "git", "biologics-research-helix-wrapper-api")
os.chdir(os.path.join(root_folder, "helix_api", "src"))

import pandas as pd
from dotenv import load_dotenv
from benchling.benchling_api import BenchlingAPIBackend
from anarci.anarci import annotate_seq, ANARCI_IMAGE, get_anarci_species, get_anarci_chain_type
from helpers import query_loop, map_error_uuid
import json

## env with Benchling IDs
load_dotenv()#dotenv_path = os.path.join(os.getcwd(), ".env"))
benchling = BenchlingAPIBackend()


def get_featureAA_species(dpp: pd.DataFrame, variable_region: pd.DataFrame, featureAA: pd.DataFrame) -> pd.DataFrame:
    """
    Determine species for a featureAA sequence.

    1. Based on featureAA
    2. Based variable region
    3. Based on dpp

    Args:
        - dpp: DataFrame
          - dpp_id
          - species
          - var_region_id
        - variable_regsion: DataFrame
          - var_region_id
          - species
          - featureAA_id
        - featureAA DataFrame:
          - featureAAid
          - species
    Return:
        - featureAAid
        - Species

    Example:
    dpp = pd.DataFrame({
        'id': ['dpp_id_1',  'dpp_id_1'],
        'species': ['Homo Sapiens', 'Mouse'],
        'var_region_id': ['var_region_id_1', 'var_region_id_2']
    })

    variable_region = pd.DataFrame({
        'id': ['var_region_id_1',  'var_region_id_2'],
        'species': ['Homo Sapiens', None],
        'featureAA_id': ['featureAA_id_1', 'featureAA_id_2']
    })


    featureAA = pd.DataFrame({
        'id': ['featureAA_id_1', 'featureAA_id_2'],
        'species': ['Homo Sapiens', None],
    })
    """
    AA_with_region = pd.merge(
        featureAA,  
        variable_region,
        how='left',
        left_on = ['id'],
        right_on = ['featureAA_id'],
        suffixes = ['', '_var_region'])
    AA_with_region_and_dpp = pd.merge(
        AA_with_region,
        dpp,
        how='left',
        left_on = ['id_var_region'],
        right_on = ['var_region_id'],
        suffixes = ['', '_dpp'])
    AA_with_combined_species = (AA_with_region_and_dpp[['id', 'species']]
        .combine_first(AA_with_region_and_dpp[['id', 'species_var_region']].rename(columns={'species_var_region': 'species'}))
        .combine_first(AA_with_region_and_dpp[['id', 'species_dpp']].rename(columns={'species_dpp': 'species'}))
    )

    # Arbitrarely take first species in case of contradictions between multiple entities
    # E.g. contradicting dpp's as an example
    AA_unique_species = AA_with_combined_species.sort_values(by=['id','species'])
    AA_unique_species= AA_unique_species.drop_duplicates(subset='id', keep='first')
    return AA_unique_species


def get_dpps(benchling=None, protein_type = 'Antibody') -> pd.DataFrame:
    """
    Get desired product proteins from benchling

    Args
      - benchling: BenchlingAPIBackend
    Returns:
      - DataFrame
    """
    if benchling is None:
        benchling = BenchlingAPIBackend()
    
    # Get filter for protein_type
    protein_type_id = benchling.settings.dropdown_id_protein_type
    dropdown_values = benchling.benchling.dropdowns.get_by_id(protein_type_id)
    dropdown_values = pd.DataFrame(dropdown_values.to_dict()['options'])
    protein_type_id = dropdown_values[dropdown_values['name'] == protein_type]['id'].iloc[0]

    ## resolve all dpp ids
    lst = benchling.benchling.custom_entities.list(
        schema_id = benchling.settings.schema_id_dpp,
        schema_fields={'Protein Type': protein_type_id}
    )

    dpps = pd.DataFrame()

    for page in lst:
        for entity in page:
            dpp_entity = pd.DataFrame({
                "id": entity.id,
                "name": entity.name,
                "protein_type": entity.fields.get("Protein Type").text_value,
                "variable_regions": entity.fields.get("Antibody - Variable Region(s)").value,
                "species": entity.fields.get("Species").text_value
            })
            dpps = pd.concat([dpps, dpp_entity], axis = 0)
    return dpps


def get_variable_regions(ids, benchling=None)-> pd.DataFrame:
    """
    Get variable_regions from benchling

    Args
      - benchling: BenchlingAPIBackend
      - ids (str[]): list of ids
    Returns:
      - DataFrame
    """
    if benchling is None:
        benchling = BenchlingAPIBackend()

    batch_size = 100
    batches = len(ids) // batch_size + 1

    variable_regions = pd.DataFrame()

    for i in range(batches):
        print(f"Batch {i + 1}/{batches}")

        variable_regions_ids_batch = ids[(i * batch_size) : min((i + 1) * batch_size, len(ids))]

        batch_query = benchling.benchling.custom_entities.bulk_get(
            variable_regions_ids_batch
        ) 

        batch_variable_regions = [[
            entity.id,
            entity.name,
            entity.fields.get("VH").value,
            entity.fields.get("VL").value,
            entity.fields.get("Species").text_value
            ] for entity in batch_query]
        batch_variable_regions = pd.DataFrame(batch_variable_regions, columns = ["var_region_id", "var_region_name", "VH", "VL", "species"])
        variable_regions = pd.concat([variable_regions, batch_variable_regions], axis = 0)

    variable_regions = variable_regions.reset_index()
    variable_regions = variable_regions.melt(
        id_vars = ['var_region_id','var_region_name', 'species'],
        value_vars= ['VH', 'VL'],
        value_name = 'featureAA_id')
    
    return variable_regions


def get_featureAA(ids, benchling=None) -> pd.DataFrame:
    """
    Get featureAA from benchling

    Args
      - benchling: BenchlingAPIBackend
      - ids (str[]): list of ids
    Returns:
      - DataFrame
    """
    if benchling is None:
        benchling = BenchlingAPIBackend()
    #resolve FeatureAA id to obtain the sequences to annotate
    batch_size = 100
    featureAA_ids = list(filter(lambda x: x is not None, ids))
    batches = len(featureAA_ids) // batch_size + 1

    featureAA = pd.DataFrame()

    for i in range(batches):
        print(f"Batch {i + 1}/{batches}")

        featureAA_ids_batch = featureAA_ids[(i * batch_size) : min((i + 1) * batch_size, len(featureAA_ids))]

        batch_query = benchling.benchling.aa_sequences.bulk_get(
            featureAA_ids_batch
        )

        batch_featureAA = [[
            entity.id, 
            entity.name,
            entity.amino_acids,
            entity.fields.get("Species").text_value,
            entity.fields.get("Function(s)").text_value,
            entity.fields.get("CDR1_IMGT").text_value,
            entity.fields.get("CDR2_IMGT").text_value,
            entity.fields.get("CDR3_IMGT").text_value,
            entity.fields.get("FR1_IMGT").text_value,
            entity.fields.get("FR2_IMGT").text_value,
            entity.fields.get("FR3_IMGT").text_value,
            entity.fields.get("FR4_IMGT").text_value,
            entity.fields.get("CDR1_Kabat").text_value,
            entity.fields.get("CDR2_Kabat").text_value,
            entity.fields.get("CDR3_Kabat").text_value,
            entity.fields.get("FR1_Kabat").text_value,
            entity.fields.get("FR2_Kabat").text_value,
            entity.fields.get("FR3_Kabat").text_value,
            entity.fields.get("FR4_Kabat").text_value
        ] for entity in batch_query]
        batch_featureAA = pd.DataFrame(
            batch_featureAA,
            columns = [
                "featureAA_id",
                "featureAA_name",
                "AA",
                "species",
                "function",
                "CDR1_IMGT",
                "CDR2_IMGT",
                "CDR3_IMGT",
                "FR1_IMGT",
                "FR2_IMGT",
                "FR3_IMGT",
                "FR4_IMGT",
                "CDR1_Kabat",
                "CDR2_Kabat",
                "CDR3_Kabat",
                "FR1_Kabat",
                "FR2_Kabat",
                "FR3_Kabat",
                "FR4_Kabat",
                ])
        featureAA = pd.concat([featureAA, batch_featureAA], axis = 0, ignore_index=True)
    return featureAA


def exclude_fully_annotated(featureAA:pd.DataFrame) -> pd.DataFrame:
    """
    Exclude fully anotated sequences

    Args: 
        - featureAA(DataFrame)
    Returns
        - featureAA(DataFrame)
    """
    # Exclude fully annotated sequences
    featureAA = featureAA[~(
                ~featureAA["CDR1_IMGT"].isnull() &
                ~featureAA["CDR2_IMGT"].isnull() &
                ~featureAA["CDR3_IMGT"].isnull() &
                ~featureAA["FR1_IMGT"].isnull() &
                ~featureAA["FR2_IMGT"].isnull() &
                ~featureAA["FR3_IMGT"].isnull() &
                ~featureAA["FR4_IMGT"].isnull() &
                ~featureAA["CDR1_Kabat"].isnull() &
                ~featureAA["CDR2_Kabat"].isnull() &
                ~featureAA["CDR3_Kabat"].isnull() &
                ~featureAA["FR1_Kabat"].isnull() &
                ~featureAA["FR2_Kabat"].isnull() &
                ~featureAA["FR3_Kabat"].isnull() &
                ~featureAA["FR4_Kabat"].isnull()
    )]

    return featureAA


def determine_species(
        featureAA:pd.DataFrame,
        dpps:pd.DataFrame,
        variable_regions:pd.DataFrame
    ) -> pd.DataFrame:
    '''
    Args:
        - dpp: DataFrame with at least columns:
          - dpp_id
          - species
          - var_region_id
        - variable_regsion: DataFrame with at least columns:
          - var_region_id
          - species
          - featureAA_id
        - featureAA DataFrame with at least columns:
          - featureAAid
          - species
    Returns:
        DataFrame featureAA with updated species
    '''
    # Deduct species based on other entities
    species_map = get_featureAA_species(
        dpp = dpps[['id', 'species', 'variable_regions']].rename(columns={'variable_regions': 'var_region_id'}),
        variable_region = variable_regions[['var_region_id', 'species', 'featureAA_id']].rename(columns={'var_region_id': 'id'}),
        featureAA = featureAA[['featureAA_id', 'species']].rename(columns={'featureAA_id': 'id'})
    )
    featureAA = featureAA.drop('species', axis=1)
    featureAA = featureAA.merge(species_map, left_on = 'featureAA_id', right_on = 'id')
    return featureAA


def get_annotations(featureAA) -> dict:
    """
    Get annotations for a featureAA DataFrame

    args:
      - featureAA (DataFrame)
    returns: dict
       {
       annotated:
       failed:
       }
    """
    annotations = list()
    failed = list()
    for index, row in featureAA.iterrows():
        id = row['featureAA_id']
        seq = row['AA']
        species = row['species']
        chain_type = row['function']
        print(id)
        print(index)
        try:
            annotations.append({id:annotate_seq(
                seq=seq,
                species=get_anarci_species(species),
                chain_type=get_anarci_chain_type(chain_type)
                )})
        except Exception as e:
            print(f"failed featureAA {id}: {e}")
            failed.append(id)
    result = {
        'annotated': annotations,
        'failed': failed
    }
    return result


def annotation_to_entity(benchling, annotation):
    '''
    Transform annotation format into benchling aasequences_batch_update format.
    '''
    id =  list(annotation.keys())[0]
    annotation_metadata = json.dumps({
        'ANARCI_metadata_imgt':  annotation[id]['metadata_imgt'],
        'ANARCI_metadata_kabat': annotation[id]['metadata_kabat']
    })
    fields = annotation[id]['annotation']

    entity = {
        "id": id,
        "fields": {key: {'value':value} for key,value in fields.items()},
        "customFields": {'annotation_metadata': {'value':annotation_metadata}}, 
        "schemaId": benchling.settings.schema_id_feature_AA,
    }
    return entity


def annotate_benchling(benchling) -> pd.DataFrame:
    """
    Annotate all featureAA's on benchling which have no annotation yet.

    Args:
        benchling: instance to annotate sequences in
    Returns: DataFrame
        annotated sequences
    """
    dpps = get_dpps(benchling=benchling)
    dpps = dpps[dpps.protein_type == "Antibody"] # only focus for now
    var_region_ids = set(dpps["variable_regions"])

    # Manual exceptions due to access issues
    #var_region_ids.remove('bfi_bUI315uZ') 
    #var_region_ids.remove('bfi_j0sG7tEA') 

    variable_regions = get_variable_regions(
        benchling=benchling,
        ids = list(var_region_ids)
    )
    featureAA = get_featureAA(
        benchling=benchling,
        ids=variable_regions["featureAA_id"].unique()
    )
    featureAA = exclude_fully_annotated(featureAA)
    featureAA = determine_species(
        featureAA=featureAA,
        dpps=dpps,
        variable_regions=variable_regions
        )
    featureAA = featureAA.sort_values('featureAA_id').reset_index(drop=True)

    ##  Manual example for upload debugging
    # feature_aa_new = []
    # entity = {
    #       "id": "prtn_8zk0Jp97",
    #       "fields": {
    #           'CDR1_IMGT': {
    #              "value":"GGFFSGYY"
    #           },
    #           'CDR2_IMGT': {
    #              "value":"INHSGST"
    #           },
    #           'CDR3_IMGT': {
    #              "value":"ARDKWTWYFDL"
    #           },
    #            'FR1_IMGT': {
    #              "value":"QVQLQQWGAGLLKPSETLSLTCAVY"
    #           },
    #           'FR2_IMGT': {
    #              "value":"WSWIRQPPGKGLEWIGE"
    #           },
    #           'FR3_IMGT': {
    #              "value":"NYNPSLKSRVTISVETSKNQFSLKLSSVTAADTAVYYC"
    #           },   
    #           'FR4_IMGT': {
    #              "value":"WGRGTLVTVSS"
    #           },  
    #       },
    #         "schemaId": benchling.settings.schema_id_feature_AA
    #     }
    # feature_aa_new.append(entity);

    batch_size = 1000
    batches = len(featureAA) // batch_size + 1
    benchling_ids = pd.DataFrame()
    failed = []

    ## test query
    ## body_i = [feature_aa_new[173]]

    # Each batch takes approx 1h
    for i in range(batches):
        annotation_result = get_annotations(featureAA=featureAA[(i * batch_size) : min((i + 1) * batch_size,len(featureAA))])
        failed.append(annotation_result['failed'])
        annotations = annotation_result['annotated']
        feature_aa_new = [annotation_to_entity(benchling, a) for a in annotations]

        body_i = feature_aa_new

        result = query_loop(
            benchling,
            body = { "aaSequences": body_i },
            endpoint = "aa-sequences:bulk-update",
            sleep = 5
        )
        entities = result["response"]["aaSequences"]
        benchling_ids_batch = pd.DataFrame({
            "type": "aa-sequences",
            "id": [entity["id"] for entity in entities]
        })
        benchling_ids = pd.concat([benchling_ids, benchling_ids_batch], axis = 0)
    # TODO: report on failing sequences
    
    return(benchling_ids)
