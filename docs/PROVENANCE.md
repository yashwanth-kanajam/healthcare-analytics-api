# Dataset provenance

Version 1 packages exact bytes from committed aggregate artifacts. Source projects are not runtime dependencies and are not modified by this service. The [manifest](../src/healthcare_api/artifacts/v1/manifest.json) records each source path, project version, Git commit, and SHA-256. Hash checks detect accidental artifact changes; they are not a digital signature.

| File | Source | Version |
|---|---|---|
| claims.json | healthcare-claims-quality / reports/results.json | 0.3.0 |
| quality.json | healthcare-claims-quality / reports/expanded/expanded-results.json | 0.3.0 |
| spending.json | healthcare-claims-quality / dashboard/dashboard-reconciliation.json | 0.3.0 |
| counties.csv | ma-primary-care-access / analysis/county_comparison.csv | 0.1.0 |

Claims source commit: b84bb77e424c68683fa61d7dd7b342d092e03186.
Access source commit: 67bd860b69ac33384dd238647c83169d250f8d5b.

Claims are self-generated synthetic 2024 data. No real payer/patient records are included. The access project uses Census ACS 2019-2023 five-year tables B01001 and B17001 and HRSA AHRF 2024-2025 release workforce observations for 2023/2022. Full source-download provenance remains in that private project's data/source_register.json. This API includes only its validated county aggregates, not the national downloads or geographic geometry.

Reconciliation tests compare every returned metric and denominator to the copied source artifacts and validate their hashes. This confirms faithful serving of the fixed snapshots; it does not independently validate the original clinical assumptions or rerun either analytical pipeline.
