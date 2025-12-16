from typing import Any, List, Optional, Union, cast
from benchling_api_client.v2.stable.models.custom_entity import CustomEntity
from benchling_api_client.v2.stable.models.field import Field

def to_string_list(val: Any) -> list[str]:
    if type(val) is list and all(isinstance(s, str) for s in val):
        return val
    else:
        return []
    
def to_string(val: Any) -> str:
    return val if type(val) is str else ''

def get_field_id_from_custom_entity(custom_entity, key: str) -> Optional[str]:
    if not type(custom_entity) is CustomEntity or type(custom_entity.fields[key]) is not Field:
        return None
    id = custom_entity.fields[key].value
    return id if type(id) is str else None