# Validation

What the automated checks cover, and what they do not establish.

## Coverage

Automated checks cover API contracts, input validation, error behaviour, deterministic responses, and reconciliation against the validated analytical artifacts. Specifically:

- All five routes return their declared response models.
- Typed schemas reject unknown extra fields and non-finite numbers.
- Malformed county identifiers, unavailable counties, unsupported query parameters, unsupported filter values, and repeated parameters each return their documented status and error code.
- Internal failures return a fixed, safe message with no stack trace, path, or echoed input.
- Packaged artifact integrity is checked against the manifest hashes when the store loads.
- Responses are deterministic across repeated calls.

## Reconciliation

Every exposed metric and denominator is compared against the source artifact it is served from, and the artifact hashes are verified against the manifest. This confirms the interface serves the analyses faithfully, so it does not become a second, divergent source of truth.

It does **not** independently validate the original analyses, and it does not rerun either pipeline.

## Installation

Verified from a clean clone into a fresh virtual environment using `requirements-lock.txt` and a non-editable package install. The checks exercise the installed package rather than the working tree.

A real localhost HTTP server was run against all five routes, along with the OpenAPI and Swagger documentation endpoints and the saved response examples. No source project, dashboard application, database, or network download is required.

## What this does not establish

This is a small read-only interface over fixed artifacts. It makes no claim to production availability, authentication, authorisation, or operational hardening, and it carries every limitation of the analyses behind it.
