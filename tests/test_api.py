import csv
import hashlib
import json
import shutil

import pytest
from fastapi.testclient import TestClient

from healthcare_api.app import app, get_store
from healthcare_api.models import CountyDetail, CountyList, ErrorResponse, Health, Summary
from healthcare_api.service import ARTIFACTS, Store


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "route,model",
    [
        ("/health", Health),
        ("/quality/summary", Summary),
        ("/spending/summary", Summary),
        ("/access/counties", CountyList),
        ("/access/counties/25011", CountyDetail),
    ],
)
def test_contract_determinism(client, route, model):
    r = client.get(route)
    assert r.status_code == 200
    model.model_validate(r.json())
    assert r.content == client.get(route).content


@pytest.mark.parametrize(
    "route,status,code",
    [
        ("/access/counties/123", 400, "malformed_request"),
        ("/access/counties/abcde", 400, "malformed_request"),
        ("/access/counties/２５０１１", 400, "malformed_request"),
        ("/access/counties/99999", 404, "resource_unavailable"),
        ("/access/counties/06001", 404, "resource_unavailable"),
        ("/access/counties?selection=bad", 422, "unsupported_value"),
        ("/access/counties?selection=", 422, "unsupported_value"),
        ("/access/counties?selection=all&selection=baseline", 400, "malformed_request"),
        ("/access/counties?metric=unknown", 422, "unsupported_parameter"),
        ("/spending/summary?year=2024", 422, "unsupported_parameter"),
        ("/quality/summary?foo=bar", 422, "unsupported_parameter"),
        ("/health?foo=bar", 422, "unsupported_parameter"),
        ("/access/counties/25011?foo=bar", 422, "unsupported_parameter"),
        ("/missing", 404, "resource_unavailable"),
    ],
)
def test_errors(client, route, status, code):
    r = client.get(route)
    assert r.status_code == status
    assert ErrorResponse.model_validate(r.json()).error.code == code


@pytest.mark.parametrize("selection,count", [("all", 14), ("baseline", 6), ("capacity_stable", 5)])
def test_filters(client, selection, count):
    rows = client.get("/access/counties", params={"selection": selection}).json()
    assert rows["count"] == count
    if selection != "all":
        assert all(
            r["baseline_selected" if selection == "baseline" else "capacity_stable"] for r in rows["counties"]
        )


def test_internal_error_no_leak(client):
    def broken():
        raise RuntimeError("SECRET /private/path traceback")

    app.dependency_overrides[get_store] = broken
    r = client.get("/quality/summary")
    assert r.status_code == 500
    assert r.json() == {"error": {"code": "internal_error", "message": "Unable to serve the request."}}


def test_method(client):
    r = client.post("/spending/summary")
    assert r.status_code == 405
    assert r.json()["error"]["code"] == "method_not_allowed"


def test_integrity(tmp_path):
    shutil.copytree(ARTIFACTS, tmp_path / "data")
    (tmp_path / "data" / "spending.json").write_text("{}")
    with pytest.raises(ValueError, match="integrity"):
        Store(tmp_path / "data")


def test_missing_artifact(tmp_path):
    shutil.copytree(ARTIFACTS, tmp_path / "data")
    (tmp_path / "data" / "spending.json").unlink()
    with pytest.raises(FileNotFoundError):
        Store(tmp_path / "data")


def test_provenance_hashes(client):
    manifest = json.loads((ARTIFACTS / "manifest.json").read_text())
    for s in manifest["sources"]:
        assert hashlib.sha256((ARTIFACTS / s["file"]).read_bytes()).hexdigest() == s["sha256"]
    for route, file in [
        ("/quality/summary", "quality.json"),
        ("/spending/summary", "spending.json"),
        ("/access/counties", "counties.csv"),
    ]:
        source = next(s for s in manifest["sources"] if s["file"] == file)
        p = client.get(route).json()["provenance"]
        assert p["commit"] == source["commit"] and p["project_version"] == source["project_version"]


def test_quality_reconciliation(client):
    source = json.loads((ARTIFACTS / "quality.json").read_text())
    got = {m["name"]: m for m in client.get("/quality/summary").json()["metrics"]}
    assert len(got) == 20
    for row in source["aggregate_metrics"]:
        for key in ("tp", "fp", "fn", "precision", "recall"):
            metric = got[f"{row['category']}.{key}"]
            assert metric["value"] == row[key]
            if key in ("precision", "recall"):
                assert metric["denominator"]["value"] == row["tp"] + row["fp" if key == "precision" else "fn"]
    assert len(source["runs"]) == 72


def test_spending_reconciliation(client):
    source = json.loads((ARTIFACTS / "spending.json").read_text())
    claims = json.loads((ARTIFACTS / "claims.json").read_text())
    got = {m["name"]: m for m in client.get("/spending/summary").json()["metrics"]}
    assert len(got) == 8
    for key in (
        "paid_cents",
        "claims",
        "members",
        "member_months",
        "paid_per_member_month",
        "claims_per_1000_member_months",
    ):
        assert got[key]["value"] == source[key]
    for key in ("incorrect_join_paid_cents", "overstatement_cents"):
        assert got[key]["value"] == claims["analytics"][key]
    assert got["paid_cents"]["value"] == 1590527
    assert got["incorrect_join_paid_cents"]["value"] == 3701102
    assert got["paid_per_member_month"]["denominator"]["value"] == 288
    assert got["paid_per_member_month"]["value"] == pytest.approx(1590527 / 100 / 288)


def test_all_county_reconciliation(client):
    with (ARTIFACTS / "counties.csv").open() as f:
        source = {r["fips"]: r for r in csv.DictReader(f)}
    rows = client.get("/access/counties").json()["counties"]
    assert [r["county_fips"] for r in rows] == sorted(source)
    for row in rows:
        s = source[row["county_fips"]]
        assert row["county"] == s["county"]
        assert row["baseline_selected"] == (s["baseline_selected"] == "True")
        assert row["capacity_stable"] == (s["capacity_stable"] == "True")
        assert len(row["metrics"]) == 8
        for m in row["metrics"]:
            assert m["value"] == float(s[m["name"]])
            if m["denominator"]:
                assert m["denominator"]["value"] == float(s[m["denominator"]["name"]])
        assert client.get("/access/counties/" + row["county_fips"]).json()["county"] == row


def test_openapi(client):
    schema = client.get("/openapi.json").json()
    assert len(schema["paths"]) == 5
    for path in schema["paths"].values():
        assert all(str(status) in path["get"]["responses"] for status in (200, 400, 404, 422, 500))
    assert client.get("/docs").status_code == 200


@pytest.mark.parametrize("route", ["/quality/summary", "/spending/summary", "/access/counties"])
def test_metric_metadata(client, route):
    data = client.get(route).json()
    metrics = data.get("metrics", []) or [m for row in data["counties"] for m in row["metrics"]]
    assert all(m["unit"] and m["basis"] and m["source_period"] for m in metrics)
    if route == "/spending/summary":
        for m in metrics:
            if m["name"].endswith("_cents"):
                assert m["unit"] == "USD cents" and isinstance(m["value"], int)
    if route == "/access/counties":
        expected = {
            "population": "people",
            "pcp_2023": "physicians",
            "pcp_per_100k": "physicians per 100,000 people",
            "poverty_pct": "percent",
            "age65_pct": "percent",
            "poverty_moe_pp": "percentage points",
            "age65_moe_pp": "percentage points",
            "selected_scenarios": "scenarios",
        }
        assert all(m["unit"] == expected[m["name"]] for m in metrics)


def test_missing_artifact_returns_internal_error(client):
    def missing():
        raise FileNotFoundError("/internal/secret/path")

    app.dependency_overrides[get_store] = missing
    response = client.get("/health")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
