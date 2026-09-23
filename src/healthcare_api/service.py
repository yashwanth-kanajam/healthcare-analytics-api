"""Read pinned outputs; do not rerun source analytics."""

import csv
import hashlib
import json
from pathlib import Path

from .models import Basis, County, Metric, Provenance, Summary

ARTIFACTS = Path(__file__).parent / "artifacts" / "v1"


class Store:
    def __init__(self, root=ARTIFACTS):
        manifest = json.loads((root / "manifest.json").read_text())
        self.sources = {s["file"]: s for s in manifest["sources"]}
        for name, source in self.sources.items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("Artifact integrity check failed")
        self.quality = json.loads((root / "quality.json").read_text())
        self.spending = json.loads((root / "spending.json").read_text())
        self.claims = json.loads((root / "claims.json").read_text())
        with (root / "counties.csv").open(newline="") as handle:
            self.rows = list(csv.DictReader(handle))
        if len(self.rows) != 14 or len({r["fips"] for r in self.rows}) != 14:
            raise ValueError("County coverage check failed")

    def provenance(self, file):
        s = self.sources[file]
        access = file == "counties.csv"
        return Provenance(
            project=s["project"],
            project_version=s["project_version"],
            commit=s["commit"],
            source_period="ACS 2019-2023; physician counts 2023"
            if access
            else "Synthetic calendar year 2024",
            limitation="County screening indicators do not establish unmet need or an optimal clinic location."
            if access
            else "Synthetic data only; no real payer or patient data. Controlled results do not estimate real-world performance.",
        )

    def quality_summary(self):
        metrics = []
        for row in self.quality["aggregate_metrics"]:
            for key in ("tp", "fp", "fn", "precision", "recall"):
                denom = None
                if key in ("precision", "recall"):
                    denom = Basis(
                        name="predicted_positive_units" if key == "precision" else "labeled_positive_units",
                        value=row["tp"] + row["fp" if key == "precision" else "fn"],
                        unit="evaluation units",
                    )
                metrics.append(
                    Metric(
                        name=f"{row['category']}.{key}",
                        value=row[key],
                        unit="proportion" if denom else "evaluation units",
                        denominator=denom,
                        basis="Expanded evaluation: 18 scenarios x 4 seeds; category-specific labeled units, not patients or defect events.",
                        source_period="Synthetic calendar year 2024",
                    )
                )
        return Summary(provenance=self.provenance("quality.json"), metrics=metrics)

    def spending_summary(self):
        s = self.spending
        metrics = []
        for key, unit in [
            ("paid_cents", "USD cents"),
            ("claims", "claims"),
            ("members", "members"),
            ("member_months", "member-months"),
            ("paid_per_member_month", "USD per member-month"),
            ("claims_per_1000_member_months", "claims per 1,000 member-months"),
        ]:
            denom = (
                Basis(name="enrolled_member_months", value=s["member_months"], unit="member-months")
                if key in ("paid_per_member_month", "claims_per_1000_member_months")
                else None
            )
            metrics.append(
                Metric(
                    name=key,
                    value=s[key],
                    unit=unit,
                    denominator=denom,
                    basis="Validated clean baseline, seed 17; eligible claims and distinct enrolled member-months.",
                    source_period="Synthetic calendar year 2024",
                )
            )
        for key in ("incorrect_join_paid_cents", "overstatement_cents"):
            metrics.append(
                Metric(
                    name=key,
                    value=self.claims["analytics"][key],
                    unit="USD cents",
                    basis="Intentional header-line join error demonstration; not actual spending.",
                    source_period="Synthetic calendar year 2024",
                )
            )
        return Summary(provenance=self.provenance("spending.json"), metrics=metrics)

    def counties(self):
        result = []
        definitions = [
            ("population", "people", None, "ACS total population"),
            (
                "pcp_2023",
                "physicians",
                None,
                "Nonfederal primary-care patient-care MDs and DOs; excludes residents and age 75+",
            ),
            (
                "pcp_per_100k",
                "physicians per 100,000 people",
                "population",
                "Physician counts divided by ACS total population",
            ),
            (
                "poverty_pct",
                "percent",
                "poverty_population",
                "Population below poverty threshold / population with poverty status determined",
            ),
            ("age65_pct", "percent", "population", "Population age 65+ / total population"),
            (
                "poverty_moe_pp",
                "percentage points",
                None,
                "Approximate 90% poverty percentage margin of error",
            ),
            ("age65_moe_pp", "percentage points", None, "Approximate 90% age 65+ percentage margin of error"),
            (
                "selected_scenarios",
                "scenarios",
                "evaluated_scenarios",
                "Selections across eight reasonable assumptions; not a probability",
            ),
        ]
        for r in sorted(self.rows, key=lambda row: row["fips"]):
            metrics = []
            for key, unit, den, basis in definitions:
                value = float(r[key]) if r[key] else None
                denominator = (
                    Basis(
                        name=den,
                        value=float(r[den]),
                        unit="scenarios" if den == "evaluated_scenarios" else "people",
                    )
                    if den
                    else None
                )
                metrics.append(
                    Metric(
                        name=key,
                        value=value,
                        unit=unit,
                        denominator=denominator,
                        basis=basis,
                        source_period="2023"
                        if key == "pcp_2023"
                        else "ACS 2019-2023; workforce 2023 (2022 in prior-year sensitivity)"
                        if key in ("pcp_per_100k", "selected_scenarios")
                        else "ACS 2019-2023",
                    )
                )
            result.append(
                County(
                    county_fips=r["fips"],
                    county=r["county"],
                    baseline_selected=r["baseline_selected"] == "True",
                    capacity_stable=r["capacity_stable"] == "True",
                    metrics=metrics,
                )
            )
        return result
