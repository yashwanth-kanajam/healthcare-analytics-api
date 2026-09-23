# API contracts

API release 0.1.0 uses artifact version 1. Routes are intentionally fixed and read-only. Breaking schema changes require a new API release and contract review; data replacement requires a new artifact version. No implicit latest-data download occurs.

Analytical envelopes include project name, project version, source Git commit, artifact version, source period, and an interpretation limitation. Each metric contains name, numeric value (or null for unavailable data), unit, source period, population/evaluation basis, and a denominator object when applicable. Null is never converted to zero. Financial totals remain integer cents; floating rates preserve source precision without implying measurement precision.

County identifiers are strings of exactly five ASCII digits, preserving leading zeros. A well-formed FIPS outside the packaged Massachusetts records is unavailable (404), not a malformed request. County collections return count and FIPS-sorted records; the count is the number of returned counties.

| HTTP | Error code | Meaning |
|---|---|---|
| 400 | `malformed_request` | Invalid FIPS format or repeated query key |
| 422 | `unsupported_parameter` | Query key absent from endpoint contract |
| 422 | `unsupported_value` | Selection outside the documented enum |
| 404 | `resource_unavailable` | County or route unavailable |
| 405 | `method_not_allowed` | Unsupported HTTP method |
| 500 | `internal_error` | Internal failure; no exception details returned |

Errors use `{"error":{"code":"...","message":"..."}}`. Error text never echoes raw user input, paths, or stack traces. OpenAPI includes typed success and error schemas. Duplicate query keys are rejected even when their values agree.

`/health` loads and checks artifact hashes on the first request in a process. The service assumes packaged artifacts remain immutable thereafter; restart after installing a new version. It is not a continuous filesystem monitor.

Implementation references: [FastAPI query validation](https://fastapi.tiangolo.com/tutorial/query-param-models/) and [exception handling](https://fastapi.tiangolo.com/tutorial/handling-errors/).
