# external libraries
from pydantic import BaseModel, Field, field_validator
from typing import Optional
# internal modules
from validations.pydantic_base_class import BaseMotivationInput
from logger import get_logger

logger = get_logger()

"Represents the user's input/output data for generating a personalized motivational sentence."

class DailyMotivationInput(BaseMotivationInput):
    pass


class UserMotivationInput(BaseMotivationInput):
    
    emotional_state: Optional[str] = Field(
        None, description="User's emotional condition")

# output validation
class MotivationOutputValidation(BaseModel):
    motivational_sentence: str
    # converting any number into string if needed
    @field_validator("motivational_sentence")
    def convert_to_str(cls, v):
        return str(v)


class UserMotivationInputWrapper(BaseModel):
    user_info: UserMotivationInput

class DailyMotivationInputWrapper(BaseModel):
    user_info: DailyMotivationInput