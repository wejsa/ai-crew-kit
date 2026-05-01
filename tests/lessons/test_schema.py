"""Schema validation regression tests for lessons-learned.json.

Phase 7 Step 2 — covers Step 1 D1 schema (lessons-learned.schema.json) regression.
"""
from __future__ import annotations

import pytest

from .conftest import mutate, schema_errors


def test_valid_document_passes(valid_document, schema):
    assert schema_errors(valid_document, schema) == []


@pytest.mark.parametrize(
    "field, bad_value, expected_token",
    [
        ("id", "BAD-ID", "L-"),
        ("id", "L-1", "L-"),  # Below 3 digits — pattern requires \d{3,}
        ("category", "foobar", "enum"),
        ("impact", "ultra", "enum"),
        ("appliedCount", 0, "minimum"),
        ("appliedCount", -1, "minimum"),
        ("title", "", "minLength"),
    ],
)
def test_invalid_field_value_fails(valid_document, schema, field, bad_value, expected_token):
    doc = mutate(valid_document, **{field: bad_value})
    errors = schema_errors(doc, schema)
    assert errors, f"expected schema error for {field}={bad_value!r}"
    assert any(expected_token in err for err in errors), errors


def test_missing_required_field_fails(valid_document, schema):
    doc = mutate(valid_document)
    del doc["lessons"][0]["createdAt"]
    errors = schema_errors(doc, schema)
    assert errors and any("createdAt" in err for err in errors)


def test_additional_property_fails(valid_document, schema):
    doc = mutate(valid_document, unknownField="not allowed")
    errors = schema_errors(doc, schema)
    assert errors and any("Additional properties" in err for err in errors)


def test_metadata_required_fields(valid_document, schema):
    doc = {"metadata": {}, "lessons": []}
    errors = schema_errors(doc, schema)
    assert errors and any("version" in err for err in errors)


def test_tags_must_be_unique(valid_document, schema):
    doc = mutate(valid_document, tags=["dup", "dup"])
    errors = schema_errors(doc, schema)
    assert errors and any("unique" in err.lower() for err in errors)
