# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

def nullify_missing_values(base, updated):
    """
    Recursively returns a merged dictionary where keys present in `base`
    but missing in `updated` are set to None.
    """
    if not isinstance(base, dict) or not isinstance(updated, dict):
        return updated

    result = {}
    for key in base:
        if key not in updated:
            result[key] = None
        else:
            if isinstance(base[key], dict) and isinstance(updated[key], dict):
                result[key] = nullify_missing_values(base[key], updated[key])
            else:
                result[key] = updated[key]

    # Add any extra keys that are only in updated (optional behavior)
    for key in updated:
        if key not in result:
            result[key] = updated[key]

    return result


class FilterModule(object):
    def filters(self):
        return {
            'nullify_missing_values': nullify_missing_values
        }
