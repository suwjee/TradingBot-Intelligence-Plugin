"""Strict, shared decoding for integrity-sensitive Plugin input."""
from __future__ import annotations

import json


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(token):
    raise ValueError(f"Invalid JSON constant: {token}")


def strict_json_loads(value):
    """Reject duplicate object keys at every depth and non-JSON constants."""
    return json.loads(value, object_pairs_hook=_unique_pairs,
                      parse_constant=_invalid_constant)


def strict_json_decoder():
    """Apply the same object and constant rules to incremental decoding."""
    return json.JSONDecoder(object_pairs_hook=_unique_pairs,
                            parse_constant=_invalid_constant)


def metadata_json(value):
    """Compare JSON types exactly, including boolean versus integer values."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))
