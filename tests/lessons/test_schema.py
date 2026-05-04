"""Schema validation regression tests for lessons-learned.json.

Phase 7 Step 2 — covers Step 1 D1 schema (lessons-learned.schema.json) regression.

PR #44 리뷰 CRITICAL #1: jsonschema 메시지 문자열 의존 제거 →
ValidationError.validator 속성(안정적 공개 API) 기반으로 전환.
"""
from __future__ import annotations

import pytest

from .conftest import mutate, schema_errors


def test_valid_document_passes(valid_document, schema):
    assert schema_errors(valid_document, schema) == []


@pytest.mark.parametrize(
    "field, bad_value, expected_keyword",
    [
        ("id", "BAD-ID", "pattern"),
        ("id", "L-1", "pattern"),  # below 3 digits
        ("category", "foobar", "enum"),
        ("impact", "ultra", "enum"),
        ("appliedCount", 0, "minimum"),
        ("appliedCount", -1, "minimum"),
        ("title", "", "minLength"),
    ],
)
def test_invalid_field_value_fails(valid_document, schema, field, bad_value, expected_keyword):
    doc = mutate(valid_document, **{field: bad_value})
    errors = schema_errors(doc, schema)
    assert errors, f"expected schema error for {field}={bad_value!r}"
    assert any(kw == expected_keyword for _, kw in errors), errors


def test_missing_required_field_fails(valid_document, schema):
    doc = mutate(valid_document)
    del doc["lessons"][0]["createdAt"]
    errors = schema_errors(doc, schema)
    assert any(kw == "required" for _, kw in errors), errors


def test_additional_property_fails(valid_document, schema):
    doc = mutate(valid_document, unknownField="not allowed")
    errors = schema_errors(doc, schema)
    assert any(kw == "additionalProperties" for _, kw in errors), errors


def test_metadata_required_fields(schema):
    doc = {"metadata": {}, "lessons": []}
    errors = schema_errors(doc, schema)
    assert any(kw == "required" and "metadata" in path for path, kw in errors), errors


def test_tags_must_be_unique(valid_document, schema):
    doc = mutate(valid_document, tags=["dup", "dup"])
    errors = schema_errors(doc, schema)
    assert any(kw == "uniqueItems" for _, kw in errors), errors
