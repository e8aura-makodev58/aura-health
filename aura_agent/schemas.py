"""Strict shared draft contract. No policy state can be returned."""

from pydantic import BaseModel, ConfigDict, Field


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=600)
    fact_ids: list[str] = Field(min_length=1, max_length=24)


class AgentDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    claims: list[Claim] = Field(max_length=16)
    question_ids: list[str] = Field(max_length=3)


OUTPUT_SCHEMA = AgentDraft.model_json_schema()
