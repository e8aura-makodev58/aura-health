"""Strict shared draft contract. No policy state can be returned."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class FindingReference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    fact_id: str
    signal: str
    direction: str
    since: str


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=600)
    fact_ids: list[str] = Field(min_length=1, max_length=24)
    findings: list[FindingReference] = Field(default_factory=list, max_length=12)
    section: Literal["changes", "context", "gaps", "routine", "review"] = "changes"


class AgentDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    claims: list[Claim] = Field(max_length=16)
    question_ids: list[str] = Field(max_length=3)
    headline: str = Field(default="", max_length=160)


OUTPUT_SCHEMA = AgentDraft.model_json_schema()
