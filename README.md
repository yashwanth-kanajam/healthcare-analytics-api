# Healthcare Analytics API

**Validated analytical results should be usable by more than notebooks and dashboards.** This is a small read-only FastAPI interface that exposes selected quality, spending and access metrics through typed contracts, with input validation, predictable errors, and reconciliation back to the source analytical artifacts.

This is a read-only interface over fixed analytical artifacts, not a healthcare or clinical system. Claims data is synthetic, with no real payer or patient data, and county indicators do not establish unmet need or identify an optimal clinic location.

## What the API exposes

| GET endpoint | Returns |
|---|---|
| `/health` | Service responds and packaged artifacts load with matching hashes |
| `/quality/summary` | Defect-evaluation results by category from the synthetic claims analysis |
| `/spending/summary` | Baseline spending and utilization, with the join-error comparison |
| `/access/counties` | All 14 Massachusetts counties, sorted by FIPS |
| `/access/counties/{county_fips}` | One county |

Analytical responses carry units, source period, basis and the relevant denominator, so no number arrives without the context needed to read it. Money stays in integer USD cents except the explicitly labeled per-member-month rate, and a `null` means unavailable rather than zero.

## How a request is served

![Data flow: packaged artifacts are hash-verified by the artifact store, then served through the FastAPI application, which validates input and returns either a typed JSON response or a structured error. Every returned metric is reconciled against the artifact it came from.](docs/img/api_flow.svg)

The values come from four immutable files copied byte-for-byte out of the claims-quality and primary-care-access projects. The API never recomputes an analytical result — it serves a reviewed snapshot. There is no database, because the dataset is small, fixed, and only changes through a deliberate artifact-version bump.

## Contracts and validation

Responses are typed models rather than loose dictionaries, and unknown extra fields and non-finite numbers are rejected outright.

Ambiguous requests are refused instead of guessed. Only the county collection accepts a query parameter — `selection=all`, `baseline` or `capacity_stable`, where omission means all. Unknown parameters are rejected rather than silently ignored.

| Status | Code | When |
|---|---|---|
| 400 | `malformed_request` | County FIPS is not exactly five ASCII digits, or a query parameter is repeated |
| 422 | `unsupported_parameter` | Query parameter that the endpoint does not accept |
| 422 | `unsupported_value` | `selection` value outside the allowed set, including empty |
| 404 | `resource_unavailable` | Well-formed county not in the dataset, or unknown route |
| 405 | `method_not_allowed` | Unsupported method on a valid route |
| 500 | `internal_error` | Fixed, safe message — no stack trace, path, or echoed input |

The 400-versus-404 split is deliberate: **400 means the identifier could not be parsed, 404 means it parsed and no such record exists.**

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

Each artifact retains the source revision identifier recorded when it was generated, so a consumer can tell which version of the analysis produced a number. That identifier is an internal build record, not a reference a reviewer resolves — the published repositories linked below are the review path for the analyses.

## Reconciliation and testing

Every metric and denominator the API returns is compared against the source artifact it is served from, and artifact hashes are verified against the manifest when the store loads. **This is what stops the interface becoming a second, divergent source of truth.**

Automated checks cover API contracts, input validation, error behavior, deterministic responses, and that reconciliation. They confirm the interface serves the analyses faithfully — they are not new validation of the analyses themselves.

Details in [validation](docs/VERIFICATION.md) and [provenance](docs/PROVENANCE.md).

### Where the data comes from

The API packages validated analytical artifacts from two published case studies:

- **[Healthcare Claims Quality & Financial Reconciliation](https://github.com/yashwanth-kanajam/healthcare-claims-quality)** — source of `claims.json`, `quality.json` and `spending.json`
- **[Massachusetts Primary Care Access Planning](https://github.com/yashwanth-kanajam/ma-primary-care-access)** — source of `counties.csv`

The bundled artifacts were hash-verified and independently checked against the corresponding files in those public repositories before release. Treat the repositories linked above as the source of truth for reviewing the analyses themselves.

## Run it locally

Requires Python 3.11 or newer.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-deps .
.venv/bin/python -m uvicorn healthcare_api.app:app --host 127.0.0.1 --port 8000
```

Then open [Swagger UI](http://127.0.0.1:8000/docs) or the [OpenAPI JSON](http://127.0.0.1:8000/openapi.json). Swagger's own JavaScript and CSS load from a CDN; the JSON contract and the API itself do not. Keep this unauthenticated service bound to localhost.

```sh
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/quality/summary
curl http://127.0.0.1:8000/spending/summary
curl 'http://127.0.0.1:8000/access/counties?selection=baseline'
.venv/bin/python -m pytest -q
```

After editing application code, reinstall with `pip install --no-deps .` before testing — the tests exercise the installed package, not an implicit source-directory import.

Further reading: [contracts and errors](docs/CONTRACTS.md), [metric definitions](docs/METRICS.md).

## Limitations

The data are fixed snapshots, not current claims or appointment availability. Defect-detection results cover controlled synthetic scenarios and do not estimate real-world accuracy. County workforce counts exclude NPs and PAs and do not measure appointment availability, travel time, insurance acceptance, or within-county variation. Selection counts across parameter settings are not probabilities.

There is no authentication, hosting, live ingestion, or production availability, and none is claimed. A new dataset requires a reviewed artifact version and renewed reconciliation.

This service inherits every limitation of the analyses behind it. Serving them faithfully is not the same as validating them.
