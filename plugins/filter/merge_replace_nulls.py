# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

def merge_replace_nulls(base, fallback):
    """
    Recursively merges two dictionaries:
    - Any `None` values in `base` will be replaced by values from `fallback` (if present).
    - Other values in `base` are preserved.
    """
    if not isinstance(base, dict) or not isinstance(fallback, dict):
        return fallback if base is None else base

    result = {}
    all_keys = set(base.keys()) | set(fallback.keys())

    for key in all_keys:
        base_val = base.get(key)
        fallback_val = fallback.get(key)

        if isinstance(base_val, dict) and isinstance(fallback_val, dict):
            result[key] = merge_replace_nulls(base_val, fallback_val)
        elif base_val is None and fallback_val is not None:
            result[key] = fallback_val
        else:
            result[key] = base_val

    return result


class FilterModule(object):
    def filters(self):
        return {
            'merge_replace_nulls': merge_replace_nulls
        }
