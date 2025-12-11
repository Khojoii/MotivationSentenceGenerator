from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

"""" This class is used by 2 input classes in pydantic_validation.py"""

class BaseMotivationInput(BaseModel):
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
    current_situation: str = Field(..., description="The user's current life situation")
    challenges: str = Field(..., description="User's main challenges or problems")
    goals: str = Field(..., description="What the user wants to achieve")
    extra_notes: Optional[str] = Field(None, description="Additional notes")

    # Empty-string validator
    @field_validator("name", "current_situation", "challenges", "goals")
    def not_empty(cls, value):
        if not value or not value.strip():
            raise ValueError("This field cannot be empty or whitespace.")
        return value

    # Pregnancy week ONLY if pregnant
    @field_validator("pregnancy_week")
    def validate_pregnancy_week(cls, value, info):
        status = info.data.get("pregnancy_status")
        if status == "pregnant" and value is None:
            raise ValueError("pregnancy_week is required when pregnancy_status is 'pregnant'.")
        return value

    # Child age ONLY if postpartum
    @field_validator("child_age")
    def validate_child_age(cls, value, info):
        status = info.data.get("pregnancy_status")
        if status == "postpartum" and value is None:
            raise ValueError("child_age is required when pregnancy_status is 'postpartum'.")
        return value

    # Custom validator for pregnancy_status (optional)
    @field_validator("pregnancy_status")
    def validate_pregnancy_status(cls, value):
        allowed = {"pregnant", "postpartum", "not_pregnant"}
        if value not in allowed:
            raise ValueError(
                "pregnancy_status must be one of: pregnant, postpartum, not_pregnant"
            )
        return value