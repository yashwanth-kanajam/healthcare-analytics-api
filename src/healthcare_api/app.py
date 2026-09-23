from functools import lru_cache
from typing import Literal

from fastapi import Depends, FastAPI, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .models import CountyDetail, CountyList, ErrorResponse, Health, Summary
from .service import Store


@lru_cache(maxsize=1)
def get_store():
    return Store()


class RequestError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def error(status, code, message):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


async def check_query(request: Request):
    allowed = {"selection"} if request.url.path == "/access/counties" else set()
    keys = list(request.query_params)
    if any(len(request.query_params.getlist(k)) > 1 for k in keys):
        raise RequestError(400, "malformed_request", "Query parameters must not be repeated.")
    if set(keys) - allowed:
        raise RequestError(
            422, "unsupported_parameter", "Unsupported query parameter. See the endpoint contract."
        )


app = FastAPI(
    title="Healthcare Analytics API",
    version="0.1.0",
    description="Read-only portfolio aggregates. Synthetic claims and public county statistics; not a production clinical system.",
    dependencies=[Depends(check_query)],
    responses={code: {"model": ErrorResponse} for code in (400, 404, 405, 422, 500)},
)


@app.exception_handler(RequestError)
async def request_error(request, exc):
    return error(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    unsupported = any(e["type"] == "literal_error" for e in exc.errors())
    return error(
        422 if unsupported else 400,
        "unsupported_value" if unsupported else "malformed_request",
        "Unsupported filter value." if unsupported else "County FIPS must contain exactly five ASCII digits.",
    )


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return error(
        exc.status_code,
        "resource_unavailable" if exc.status_code == 404 else "method_not_allowed",
        "Resource unavailable." if exc.status_code == 404 else "Method not allowed.",
    )


@app.exception_handler(Exception)
async def internal_error(request, exc):
    return error(500, "internal_error", "Unable to serve the request.")


@app.get("/health", response_model=Health)
def health(store=Depends(get_store)):
    return Health(status="ok", api_version="0.1.0", artifact_version="1")


@app.get("/quality/summary", response_model=Summary)
def quality(store=Depends(get_store)):
    return store.quality_summary()


@app.get("/spending/summary", response_model=Summary)
def spending(store=Depends(get_store)):
    return store.spending_summary()


@app.get("/access/counties", response_model=CountyList)
def counties(
    selection: Literal["all", "baseline", "capacity_stable"] | None = None, store=Depends(get_store)
):
    rows = store.counties()
    if selection in ("baseline", "capacity_stable"):
        rows = [
            r
            for r in rows
            if getattr(r, "baseline_selected" if selection == "baseline" else "capacity_stable")
        ]
    return CountyList(provenance=store.provenance("counties.csv"), count=len(rows), counties=rows)


@app.get("/access/counties/{county_fips}", response_model=CountyDetail)
def county(county_fips: str = Path(pattern=r"^[0-9]{5}$"), store=Depends(get_store)):
    for row in store.counties():
        if row.county_fips == county_fips:
            return CountyDetail(provenance=store.provenance("counties.csv"), county=row)
    raise RequestError(404, "resource_unavailable", "County is unavailable in this dataset.")
