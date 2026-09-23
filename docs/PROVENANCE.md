# Dataset provenance

Version 1 packages exact bytes from committed aggregate artifacts. Source projects are not runtime dependencies and are not modified by this service. The [manifest](../src/healthcare_api/artifacts/v1/manifest.json) records each source path, project version, source revision identifier, and SHA-256. Hash checks detect accidental artifact changes; they are not a digital signature.

The two source projects are published at [healthcare-claims-quality](https://github.com/yashwanth-kanajam/healthcare-claims-quality) and [ma-primary-care-access](https://github.com/yashwanth-kanajam/ma-primary-care-access). Those repositories are the review path for the analyses themselves.

| File | Source | Version |
|---|---|---|
| claims.json | healthcare-claims-quality / reports/results.json | 0.3.0 |
| quality.json | healthcare-claims-quality / reports/expanded/expanded-results.json | 0.3.0 |
| spending.json | healthcare-claims-quality / dashboard/dashboard-reconciliation.json | 0.3.0 |
| counties.csv | ma-primary-care-access / analysis/county_comparison.csv | 0.1.0 |

Each artifact carries the source revision identifier recorded when it was generated — `b84bb77e424c68683fa61d7dd7b342d092e03186` for the claims files, `67bd860b69ac33384dd238647c83169d250f8d5b` for the county file. These are build records that tie a served number to the analysis run that produced it. They are not references to resolve against the published repositories; verify the artifacts by their SHA-256 against the source files instead.

Claims are self-generated synthetic 2024 data. No real payer/patient records are included. The access project uses Census ACS 2019-2023 five-year tables B01001 and B17001 and HRSA AHRF 2024-2025 release workforce observations for 2023/2022. Full source-download provenance is recorded in that project's [`data/source_register.json`](https://github.com/yashwanth-kanajam/ma-primary-care-access/blob/main/data/source_register.json). This API includes only its validated county aggregates, not the national downloads or geographic geometry.

Reconciliation tests compare every returned metric and denominator to the copied source artifacts and validate their hashes. This confirms faithful serving of the fixed snapshots; it does not independently validate the original clinical assumptions or rerun either analytical pipeline.
