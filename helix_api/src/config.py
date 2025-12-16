import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    client_id: str = os.getenv("BENCHLING_CLIENT_ID", "")
    client_secret: str = os.getenv("BENCHLING_CLIENT_SECRET", "") 

class DEVSettings(Settings):
    base_url: str = "https://bayer-dev.benchling.com" 
    registry_id: str = "src_dlAQySkQ"   # Bayer registry
    plasmid_not_available: str = ""   # only available in PROD
    schema_id_individual_clones: str = "assaysch_I2ANgdCQ"  # NGS Pipeline Output (Incl. Results) v0.1
    schema_id_clone_pool: str = "assaysch_lKdA5G3j"  # [ONE][NGS] Repertoire Run
    schema_id_mutation_analysis: str = "assaysch_IK763bgT"  # [NGS] Mutation Analysis Run
    schema_id_mutation_assay_results: str = "assaysch_wI28nj9K"  # [NGS] Variant Library Design
    schema_id_pcr_pool: str = "ts_LcoWdHGI"  # [ONE][NGS] PCR Pool
    schema_id_feature_AA: str = "ts_RcJul02H"   # [ONE] Feature AA
    schema_id_variable_region: str = "ts_hFEAmeKW"   # [ONE] Variable Region
    schema_id_chain_AA: str = "ts_gVkqINsV"   # [ONE] Chain AA
    schema_id_protein_complex_design: str = "ts_FvvZltqA"    # [ONE] Protein Complex Design
    schema_id_dpp: str = "ts_PTZi0VEq"   # [ONE] Desired Product Protein
    schema_id_ppb: str = "ts_XGzIqcDR"   # [ONE] Protein Purified Batch
    schema_id_peb: str = "ts_KkezXR6i"   # [ONE] [PP] Protein Expression Batch
    schema_id_expression_run: str = "ts_5OXBYJnK"   # [ONE] [PP] Expression Run
    schema_id_bdp_entity: str = "ts_Xh70lONQ"   # [ONE] BDP Entity
    schema_id_plasmid: str = "ts_wrlxkNkz"   # [ONE] Plasmid
    schema_id_project: str = "ts_PxUImI2w"   # [ONE] Project
    schema_id_bdp_project: str = ""   # BDP Project
    schema_id_plasmid_batch: str = "ts_qnjxCbqk"  # [ONE] Plasmid Batch
    schema_id_pharmaceutical_target: str = ""  # Pharmaceutical Target
    schema_id_chain_design: str = "" # Chain Design
    schema_id_cell_line: str = ""  # Cell Line
    schema_id_downstream_processing_run: str = ""   # Downstream Processing Run
    schema_id_unit_operation: str = ""   # Unit Operation
    dropdown_id_functions: str = "sfs_vjpSRJrF"
    dropdown_id_species: str = "sfs_6Rljxe7b"
    dropdown_id_chain_type: str = "sfs_vjpSRJrF"
    dropdown_id_protein_type: str = "sfs_p8PisEIM"
    dropdown_id_antibody_format: str = "sfs_AafdMl6Z"
    dropdown_id_antibody_isotype: str = "sfs_xnJRuQ0i"
    dropdown_id_modification: str = "sfs_RGN7I4YK"
    dropdown_id_provider: str = "sfs_IeLfpW6i"
    dropdown_id_batch_status: str = "sfs_Wl7eNDng" 
    dropdown_id_expression_status: str = "sfs_ERLvDT0k"
    dropdown_id_plasmid_category: str = "sfs_uqPoNhuj"
    dropdown_id_plasmid_batch_type: str = "sfs_UFXksk74"
    dropdown_id_expression_batch_type: str = "sfs_JrOMtxAk"
    dropdown_id_expression_product_type: str = "sfs_VUxsyNjF"
    dropdown_id_growth_medium: str = ""
    dropdown_id_expression_product_type: str = ""
    dropdown_id_confidentiality_status: str = ""

class QASettings(Settings):
    base_url: str = "https://bayer-qa.benchling.com" 
    registry_id: str = "src_YfjrZwrO"   # Bayer registry
    plasmid_not_available: str = ""     # only available in PROD  
    schema_id_individual_clones: str = "assaysch_42WJh3RS"  
    schema_id_clone_pool: str = "assaysch_WN8XXnuy"
    schema_id_mutation_analysis: str = "assaysch_JObzYf0i"
    schema_id_mutation_assay_results: str = "assaysch_uVahzca0"
    schema_id_pcr_pool: str = "ts_h9JpwO47"
    schema_id_feature_AA: str = "ts_7PBsIdck"  # [ONE] Feature AA
    schema_id_variable_region: str = "ts_MvhZgIRm"  # [ONE] Variable Region
    schema_id_chain_AA: str = "ts_kTvD5Obc"   # [ONE] Chain AA
    schema_id_protein_complex_design: str = "ts_d1NKWkTj"    # [ONE] Protein Complex Design
    schema_id_dpp: str = "ts_JUBl1tZg"  # [ONE] Desired Product Protein
    schema_id_ppb: str = "ts_128Z5cMy"   # [ONE] Protein Purified Batch
    schema_id_peb: str = "ts_msh1SUkO"   # [ONE] [PP] Protein Expression Batch
    schema_id_expression_run: str = "ts_q9m64KYe"   # [ONE] [PP] Expression Run
    schema_id_bdp_entity: str = "ts_GZJvxEE5"   # [ONE] BDP Entity
    schema_id_bdp_project: str = "ts_SCBEzGSG"   # BDP Project
    schema_id_plasmid: str = "ts_WedCb47n"   # [ONE] Plasmid
    schema_id_project: str = "ts_Cy1WJYj6"   # [ONE] Project
    schema_id_plasmid_batch: str = "ts_C0glNPD5"  # [ONE] Plasmid Batch
    schema_id_pharmaceutical_target: str = "ts_QqUHErtf"  # Pharmaceutical Target
    schema_id_chain_design: str = "ts_ttiaGQOf" # Chain Design
    schema_id_cell_line: str = "ts_edlpYhNC"  # Cell Line
    schema_id_downstream_processing_run: str = "ts_qG23EPrG"   # Downstream Processing Run
    schema_id_unit_operation: str = "ts_dkbU5pml"   # Unit Operation
    dropdown_id_functions: str = "sfs_WnYPYii8"
    dropdown_id_species: str = "sfs_SSNCkcQB"
    dropdown_id_chain_type: str = ""
    dropdown_id_protein_type: str = "sfs_e5L88Dgy"
    dropdown_id_antibody_format: str = ""
    dropdown_id_antibody_isotype: str = ""
    dropdown_id_modification: str = "sfs_gmy7tSU9"
    dropdown_id_provider: str = "sfs_bIYdsNUg"
    dropdown_id_batch_status: str = "sfs_032jQisF" 
    dropdown_id_expression_batch_type: str = "sfs_sCxb2A2z"
    dropdown_id_expression_status: str = "sfs_9T4bYlk6"
    dropdown_id_plasmid_category: str = "sfs_lpFcwaRz"
    dropdown_id_plasmid_batch_type: str = ""
    dropdown_id_expression_product_type: str = ""
    dropdown_id_growth_medium: str = "sfs_VNtuswWE"
    dropdown_id_expression_product_type: str = "sfs_SIC4tVZY"
    dropdown_id_confidentiality_status: str = ""

class PRODSettings(Settings):
    base_url: str = "https://bayer.benchling.com" 
    registry_id: str = "src_Jee4nbYF"  # Bayer registry
    plasmid_not_available: str = "seq_0IHSQ10H"
    schema_id_individual_clones: str = "assaysch_ZjKRXUPD"
    schema_id_clone_pool: str = "assaysch_qSE5kLw0"
    schema_id_mutation_analysis: str = "assaysch_QB1DG9dZ"  
    schema_id_mutation_assay_results: str = "assaysch_yF8DzQKV"
    schema_id_pcr_pool: str = "ts_8kULMlEm"
    schema_id_feature_AA: str = "ts_EjbKfQga"  # [ONE] Feature AA
    schema_id_variable_region: str = "ts_yDFl7j9n"  # [ONE] Variable Region
    schema_id_chain_AA: str = "ts_b5TxHMOy"   # [ONE] Chain AA
    schema_id_protein_complex_design: str = "ts_t1U09xBV"    # [ONE] Protein Complex Design
    schema_id_dpp: str = "ts_8E6iR2Kk"  # [ONE] Desired Product Protein
    schema_id_ppb: str = "ts_peKE94pF"   # [ONE] Protein Purified Batch
    schema_id_peb: str = "ts_dvf0ahpH"   # [ONE] [PP] Protein Expression Batch
    schema_id_expression_run: str = "ts_k2kjl91U"   # [ONE] [PP] Expression Run
    schema_id_bdp_entity: str = "ts_zXthphVb"   # [ONE] BDP Entity
    schema_id_plasmid: str = "ts_VMCSiuO8"   # [ONE] Plasmid
    schema_id_project: str = "ts_QHhYSP9W"   # [ONE] Project
    schema_id_bdp_project: str = "ts_bH0NzXTx"   # BDP Project
    schema_id_plasmid_batch: str = "ts_mKxBu1tK"  # [ONE] Plasmid Batch
    schema_id_pharmaceutical_target: str = "ts_V3urOinr"  # Pharmaceutical Target
    schema_id_chain_design: str = "ts_5SlQW0BX" # Chain Design
    schema_id_cell_line: str = "ts_YEaEbfUC"  # Cell Line
    schema_id_downstream_processing_run: str = "ts_KIL7c67w"   # Downstream Processing Run
    schema_id_unit_operation: str = "ts_eQbWWjtO"   # Unit Operation
    dropdown_id_functions: str = "sfs_k4tEiwp4"
    dropdown_id_species: str = "sfs_0yntNk72"
    dropdown_id_chain_type: str = ""
    dropdown_id_protein_type: str = "sfs_Mze6G0cT"
    dropdown_id_antibody_format: str = ""
    dropdown_id_antibody_isotype: str = ""
    dropdown_id_modification: str = "sfs_20FD8JjZ"
    dropdown_id_provider: str = "sfs_S00rJaXQ"
    dropdown_id_batch_status: str = "sfs_resbPCby" 
    dropdown_id_expression_batch_type: str = "sfs_eGyZYsvB"
    dropdown_id_expression_status: str = "sfs_tm9zIJvx"
    dropdown_id_plasmid_category: str = "sfs_lAKyK3d9"
    dropdown_id_plasmid_batch_type: str = ""
    dropdown_id_expression_product_type: str = ""
    dropdown_id_growth_medium: str = "sfs_IZYQC97U"
    dropdown_id_expression_product_type: str = "sfs_HQ96PHGK"
    dropdown_id_confidentiality_status: str = "sfs_HeAvTw2o"


class tdpSettings(BaseSettings):
    jwt_token: str = os.getenv("TDP_TOKEN", "") 

class tdpPRODSettings(tdpSettings):
    base_url: str = "https://bayer.tetrascience.com" 
    org_slug: str = "bayer-br-prod"
    api_url: str = "https://api.bayer.tetrascience.com/v1"
    
class tdpQASettings(tdpSettings):
    base_url: str = "https://bayer-qa.tetrascience.com" 
    org_slug: str = "bayer-br-qa"
    api_url: str = "https://api.bayer-qa.tetrascience.com/v1"
    
class tdpDEVSettings(tdpSettings):
    base_url: str = "https://bayer-dev.tetrascience.com"
    org_slug: str = "bayer-br-dev" 
    api_url: str = "https://api.bayer-dev.tetrascience.com/v1"
    
def get_settings() -> (PRODSettings | QASettings | DEVSettings):
    benchling_environment = os.getenv("BENCHLING_ENV", "dev")  # defaults to "dev" 
    if benchling_environment == "prod":
        settings = PRODSettings()
    elif benchling_environment == "qa":
        settings = QASettings()
    else:
        settings = DEVSettings()
    return settings

def get_tdp_settings() -> (tdpPRODSettings | tdpQASettings | tdpDEVSettings):
    tdp_environment = os.getenv("TDP_ENV", "dev")  # defaults to "dev" 
    if tdp_environment == "prod":
        settings = tdpPRODSettings()
    elif tdp_environment == "qa":
        settings = tdpQASettings()
    else:
        settings = tdpDEVSettings()
    return settings
