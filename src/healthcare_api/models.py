from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Basis(Contract):
    name: str
    value: int | float
    unit: str


class Metric(Contract):
    name: str
    value: int | float | None
    unit: str
    basis: str
    denominator: Basis | None = None
    source_period: str


class Provenance(Contract):
    project: str
    project_version: str
    commit: str
    artifact_version: Literal["1"] = "1"
    source_period: str
    limitation: str


class Summary(Contract):
    provenance: Provenance
    metrics: list[Metric]


class County(Contract):
    county_fips: str = Field(pattern=r"^[0-9]{5}$")
    county: str
    baseline_selected: bool
    capacity_stable: bool
    metrics: list[Metric]


class CountyList(Contract):
    provenance: Provenance
    count: int = Field(ge=0)
    counties: list[County]


class CountyDetail(Contract):
    provenance: Provenance
    county: County


class Health(Contract):
    status: Literal["ok"]
    api_version: Literal["0.1.0"]
    artifact_version: Literal["1"]


class ErrorDetail(Contract):
    code: str
    message: str


class ErrorResponse(Contract):
    error: ErrorDetail
