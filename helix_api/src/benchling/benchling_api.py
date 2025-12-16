from typing import Dict, Any, Optional

import pandas as pd
from backend import BenchlingBackend
from benchling.schemas import BaseEntityGet, BaseEntityPost, SequenceAAPost, SequenceDNAPost

class BenchlingAPIBackend(BenchlingBackend):

    def get_query(self, endpoint: str, additional_headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any] | None:
        """get_query 
        Execute Benchling GET query

        :param endpoint: Benchling API endpoint, e.g. `custom-entities` or `custom-enties/<custom_entity_id>`
        :type endpoint: str
        :param additional_headers: additional named query parameters, e.g. `{"nameIncludes": "NGS_RUN001"} 
        :type additional_headers: Dict[str, Any] | None
        :return: Response object with attributes `.status_code` and `.parsed` (content parsed as dict)
        :rtype: benchling_api_client.v2.types.Response
        
        """        
        response =  self.benchling.api.get_response(
            url=f"api/v2/{endpoint}",
            additional_headers=additional_headers,
        )
        return response.parsed

    def post_query(self, endpoint: str, body: BaseEntityPost):
        """post_query
        Execute Benchling POST query with modeled response

        :param endpoint: Benchling API endpoint, e.g. `custom-entities` 
        :type endpoint: str
        :param body: query body, must inherit from dataclass BaseEntityPost
        :type body: BaseEntityPost
        :param **kwargs: named arguments passed as fields to the body of the request 
        :return: Modeled response object
        :rtype: BaseEntityGet
        
        """

        response = self.benchling.api.post_modeled(
            url=f"api/v2/{endpoint}",
            target_type=BaseEntityGet,
            body=body
        )
        return response
    
    def get_dropdown_id(self, type: str, name: Optional[str] = None):
        id = getattr(self.settings, f"dropdown_id_{type}")
        response = self.get_query(f"dropdowns/{id}")
        if response is not None:
            options = pd.DataFrame(response["options"])
            if name is not None:
                return options[options["name"] == name]["id"].item()
            else:
                return options
        else:
            return None

    def register_featureAA(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_feature_AA
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "REPLACE_NAMES_FROM_PARTS"
        body = SequenceAAPost.from_dict(kwargs)
        result = self.post_query(endpoint="aa-sequences", body=body)
        return result
    
    def bulk_update_featureAA(self, **kwargs):
        body = SequenceAAPost.from_dict(kwargs)
        result = self.post_query(endpoint="aa-sequences:bulk_update", body=body)
        return result

    def register_variableRegion(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_variable_region
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "DELETE_NAMES"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

    def register_chainAA(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_chain_AA
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "NEW_IDS"
        body = SequenceAAPost.from_dict(kwargs)
        result = self.post_query(endpoint="aa-sequences", body=body)
        return result

    def register_proteinComplexDesign(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_protein_complex_design
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "DELETE_NAMES"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

    def register_desiredProductProtein(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_dpp
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "DELETE_NAMES"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

    def register_proteinPurifiedBatch(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_ppb
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "REPLACE_NAMES_FROM_PARTS"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

    def register_expressionRun(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_expression_run
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "DELETE_NAMES"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

    def register_plasmid(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_plasmid
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "NEW_IDS"
        body = SequenceDNAPost.from_dict(kwargs)
        result = self.post_query(endpoint="dna-sequences", body=body)
        return result

    def register_plasmidBatch(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_plasmid_batch
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "REPLACE_NAMES_FROM_PARTS"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

    def register_proteinExpressionBatch(self, **kwargs):
        kwargs["schemaId"] = self.settings.schema_id_peb
        kwargs["registryId"] = self.settings.registry_id
        kwargs["namingStrategy"] = "REPLACE_NAMES_FROM_PARTS"
        body = BaseEntityPost.from_dict(kwargs)
        result = self.post_query(endpoint="custom-entities", body=body)
        return result

