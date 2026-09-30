# Healthcare Analytics API

This project exposes selected outputs from the claims-quality and primary-care-access analyses through a read-only FastAPI interface. Responses are typed, inputs are validated, errors are predictable, and every returned metric reconciles to the source artifact it came from.

## What the API exposes

| GET endpoint | Returns |
|---|---|
| `/health` | Service responds and packaged artifacts load with matching hashes |
| `/quality/summary` | Defect-evaluation results by category from the synthetic claims analysis |
| `/spending/summary` | Baseline spending and utilization, with the join-error comparison |
| `/access/counties` | All 14 Massachusetts counties, sorted by FIPS |
| `/access/counties/{county_fips}` | One county |

Analytical responses carry units, source period, basis and the relevant denominator. Money stays in integer USD cents except the explicitly labeled per-member-month rate, and a `null` means unavailable rather than zero.

## How a request is served

![Data flow: packaged artifacts are hash-verified by the artifact store, then served through the FastAPI application, which validates input and returns either a typed JSON response or a structured error. Every returned metric is reconciled against the artifact it came from.](docs/img/api_flow.svg)

The values come from four immutable files copied byte-for-byte out of the claims-quality and primary-care-access projects. The API never recomputes an analytical result; it serves a fixed snapshot, so there is no database. A new dataset means a new artifact version and a fresh reconciliation.

## Contracts and validation

Responses are typed models; unknown extra fields and non-finite numbers are rejected.

Only the county collection accepts a query parameter: `selection=all`, `baseline` or `capacity_stable` (omitted means all). Unknown or repeated parameters are rejected.

| Status | Code | When |
|---|---|---|
| 400 | `malformed_request` | County FIPS is not exactly five ASCII digits, or a query parameter is repeated |
| 422 | `unsupported_parameter` | Query parameter that the endpoint does not accept |
| 422 | `unsupported_value` | `selection` value outside the allowed set, including empty |
| 404 | `resource_unavailable` | Well-formed county not in the dataset, or unknown route |
| 405 | `method_not_allowed` | Unsupported method on a valid route |
| 500 | `internal_error` | Fixed, safe message — no stack trace, path, or echoed input |

A 400 means the identifier could not be parsed; a 404 means it parsed but no such record exists.

Every error uses the same envelope with a stable machine-readable code. OpenAPI describes both success and error schemas, and Swagger documentation is generated locally at `/docs`.

## Example

```sh
curl http://127.0.0.1:8000/access/counties/25011
```

```json
{
  "provenance": {
    "project": "ma-primary-care-access",
    "project_version": "0.1.0",
    "commit": "67bd860b69ac33384dd238647c83169d250f8d5b",
    "artifact_version": "1",
    "source_period": "ACS 2019-2023; physician counts 2023",
    "limitation": "County screening indicators do not establish unmet need or an optimal clinic location."
  },
  "county": {
    "county_fips": "25011",
    "county": "Franklin",
    "baseline_selected": true,
    "capacity_stable": true,
    "metrics": [
      {
        "name": "population",
        "value": 70922.0,
        "unit": "people",
        "basis": "ACS total population",
        "denominator": null,
        "source_period": "ACS 2019-2023"
      }
    ]
  }
}
```

A well-formed county that is not in the dataset returns `404`:

```sh
curl http://127.0.0.1:8000/access/counties/99999
```

```json
{ "error": { "code": "resource_unavailable", "message": "County is unavailable in this dataset." } }
```

One metric is shown above; the live response returns the full list. The complete set of recorded requests and responses is in [`docs/examples.json`](docs/examples.json).

The `commit` field records the build of the source analysis that produced the artifact. It is an internal build record; the analyses themselves are reviewed through the public repositories linked below.

## Reconciliation and testing

Returned metrics and denominators are reconciled against the packaged source artifacts, and artifact hashes are checked against the manifest when the service loads. Automated tests also cover API contracts, input validation, error behavior and deterministic responses.

Details in [validation](docs/VERIFICATION.md) and [provenance](docs/PROVENANCE.md).

### Where the data comes from

The API packages validated analytical artifacts from two published case studies:

- **[Healthcare Claims Quality & Financial Reconciliation](https://github.com/yashwanth-kanajam/healthcare-claims-quality)** — source of `claims.json`, `quality.json` and `spending.json`
- **[Massachusetts Primary Care Access Planning](https://github.com/yashwanth-kanajam/ma-primary-care-access)** — source of `counties.csv`

The packaged artifacts were hash-checked against the corresponding files in those repositories before release.

## Run locally

Requires Python 3.11+.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m uvicorn healthcare_api.app:app --host 127.0.0.1 --port 8000
```

Then open [Swagger UI](http://127.0.0.1:8000/docs) or the [OpenAPI JSON](http://127.0.0.1:8000/openapi.json). The service has no authentication, so it is bound to localhost.

```sh
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/quality/summary
curl http://127.0.0.1:8000/spending/summary
curl 'http://127.0.0.1:8000/access/counties?selection=baseline'
.venv/bin/python -m pytest -q
```

After editing application code, reinstall with `pip install --no-deps .` before testing; the tests run against the installed package.

Further reading: [contracts and errors](docs/CONTRACTS.md), [metric definitions](docs/METRICS.md).

## Limitations

The API serves fixed outputs from the two underlying analytical projects; it is not a live healthcare system. The claims data are synthetic, and the county-access data are historical public aggregates. The service is intended as a local demonstration rather than a production deployment.

Analytical limitations remain those documented in the source projects.
