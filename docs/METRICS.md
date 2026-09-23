# Metric definitions

## Quality

The expanded evaluation contains 18 scenarios across seeds 17, 101, 202, and 303: 72 runs. It is separate from the earlier scenario suite in claims.json. Each category exposes TP, FP, FN as evaluation-unit counts. Precision = TP/(TP+FP); recall = TP/(TP+FN). Denominators are returned explicitly. Units are category-specific record/check labels, not patients or independent defect events. Aggregate TP values are 32 exact duplicates, 236 foreign-key failures, 28 invalid date sequences, and 28 financial reconciliations; FP and FN are zero in this controlled suite only.

## Spending

Synthetic 2024 baseline, seed 17: 101 claims, 24 members, 288 enrolled member-months, paid 1,590,527 USD cents. A claim is one header, not a visit. Member-months count distinct enrolled member/calendar-month combinations. Eligible services must fit within one enrollment span. Paid per member-month is USD paid divided by 288; utilization is claims x 1,000 / 288.

The incorrect header-line join reports 3,701,102 cents and an overstatement of 2,110,575 cents. These are intentionally erroneous demonstration amounts, clearly separated by name and basis from actual baseline paid. November/December have no generated services, despite full-year enrollment; no real seasonality inference is valid.

## Access

- Population: ACS 2019-2023 total county population estimate.
- PCP 2023: HRSA AHRF nonfederal MD/DO primary-care patient-care physicians; excludes residents and age 75+. Not FTEs or appointment capacity.
- PCP per 100,000: 2023 count / ACS total population x 100,000.
- Poverty percent: ACS below-poverty population / population for whom poverty status is determined x 100. This denominator differs from total population.
- Age 65+ percent: ACS age 65+ population / total population x 100.
- MOE fields: approximate ACS 90% margins of error in percentage points, copied from validated outputs.
- Selected scenarios: number of selections / evaluated scenarios (eight here), not a probability.

Baseline selection means physician rate below the county median (78.82678906708841) and either poverty at least the state weighted 9.98217416202257% or age 65+ at least 17.4668193086918%. Capacity-stable selection persists across baseline, 40th/60th percentile cutoffs, and prior-year workforce assumptions. These flags are copied, not recomputed by the API.

Source comparison data retain the denominators and scenario counts used for reconciliation. County averages can hide local barriers. Nonselection is not proof of adequate access.
