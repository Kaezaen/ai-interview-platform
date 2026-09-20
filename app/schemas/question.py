"""Response schemas for the question endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import QuestionCategory, QuestionDifficulty


class QuestionRead(BaseModel):
    """A generated question as the API exposes it.

    ``prompt_version`` and ``model_name`` are deliberately absent. They exist so
    a stored row can be explained after the prompt is rewritten or the model is
    swapped; they carry nothing for the caller, and naming the model would leak
    a vendor detail into the contract.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ordinal: int
    content: str
    category: QuestionCategory
    skill: str
    difficulty: QuestionDifficulty
    created_at: datetime
