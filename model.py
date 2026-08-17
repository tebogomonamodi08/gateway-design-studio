from pydantic import BaseModel
from typing import List, Optional


class LiteLLMParams(BaseModel):
    model: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None

class ModelItem(BaseModel):
    model_name: str
    litellm_params: LiteLLMParams
    
class GatewayConfig(BaseModel):
    model_list : List[ModelItem]