# Python standard libraries
import re
from typing import List, Dict
# external libraries
from pydantic import BaseModel, Field, field_validator, model_validator
# internal modules
from logger import get_logger

logger = get_logger()

"Represents the user's input data for generating a personalized motivational sentence."

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class UserMotivationInput(BaseModel):
    name: str = Field(..., description="Mother's name")
    child_name: Optional[str] = Field(None, description="Child's name if available")
    age: int = Field(..., ge=0, description="Mother's age (must be non-negative)")
    pregnancy_status: Literal["pregnant", "postpartum", "not_pregnant"] = Field(
        ..., description="Pregnancy status of the user"
    )
    pregnancy_week: Optional[int] = Field(
        None, ge=0, le=42, description="Pregnancy week (only if pregnant)"
    )

    child_age: Optional[int] = Field(
        None, ge=0, description="Age of the child (only for mothers with children)"
    )

    current_situation: str = Field(
        ..., description="The user's current life situation"
    )
    challenges: str = Field(
        ..., description="User's main challenges or problems"
    )
    goals: str = Field(
        ..., description="What the user wants to achieve"
    )

    emotional_state: Optional[str] = Field(
        None, description="User's emotional condition"
    )

    extra_notes: Optional[str] = Field(
        None, description="Additional notes about user's health or situation"
    )

    # Validators
    @field_validator("name", "current_situation", "challenges", "goals")
    def not_empty(cls, value):
        if not value or not value.strip():
            raise ValueError("This field cannot be empty or whitespace.")
        return value

    @field_validator("pregnancy_week")
    def validate_pregnancy_week(cls, value, info):
        status = info.data.get("pregnancy_status")
        if status == "pregnant" and value is None:
            raise ValueError("pregnancy_week is required when pregnancy_status is 'pregnant'.")
        return value

    @field_validator("child_age")
    def validate_child_age(cls, value, info):
        status = info.data.get("pregnancy_status")
        if status == "postpartum" and value is None:
            raise ValueError("child_age is required when pregnancy_status is 'postpartum'.")
        return value

# output validation
class MotivationOutputValidation(BaseModel):
    motivational_sentence: str
    # converting any number into string if needed
    @field_validator("motivational_sentence")
    def convert_to_str(cls, v):
        return str(v)


def force_json_closure(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        logger.debug("JSON closure detected in text")
        return match.group()
    logger.warning("No JSON object found in text, returning empty dict")
    return "{}"


def normalize_mixed_text(text: str) -> str:
    """
    Normalize mixed text by:
    1. Replacing multiple spaces/newlines with a single space
    2. Removing leading/trailing whitespace
    3. Removing non-printable characters
    """
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    text = re.sub(r'\s+', ' ', text)
    logger.debug("Text normalized using normalize_mixed_text")
    return text.strip()