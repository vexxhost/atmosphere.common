# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from ansible.plugins.lookup import LookupBase
from ansible.plugins.filter.core import to_nice_yaml
from ansible.errors import AnsibleLookupError

DOCUMENTATION = """
name: helm_values
short_description: Lookup and merge helm values for a component
description:
  - Looks up and merges helm values from multiple sources
  - Handles nullification of missing values during updates
  - Replaces null values with defaults
  - Expects variables named _<component>_helm_values and <component>_helm_values
options:
  _terms:
    description: |
      List of arguments:
      1. Component name to lookup helm values for
      2. Current values from existing Helm release (optional)
    required: true
    type: list
"""

EXAMPLES = """
# Basic usage for initial deployment
- debug:
    msg: "{{ lookup('atmosphere.common.helm_values', 'metrics_server') }}"

# Usage during update with current values
- debug:
    msg: "{{ lookup('atmosphere.common.helm_values', 'metrics_server', helm_info.values) }}"
"""

RETURN = """
_value:
  description: Merged helm values as YAML string
  type: str
"""


class LookupModule(LookupBase):
    def _nullify_missing_values(self, base, updated):
        """
        Recursively marks missing values as None when they exist in base but not in updated
        """
        if not isinstance(base, dict) or not isinstance(updated, dict):
            return updated

        result = {}
        # First handle all keys from base
        for key in base:
            if key not in updated:
                result[key] = None
            else:
                if isinstance(base[key], dict):
                    if key in updated and isinstance(updated[key], dict):
                        # Recursively handle nested dictionaries
                        result[key] = self._nullify_missing_values(base[key], updated[key])
                    else:
                        # If the structure changed (dict -> non-dict), keep the update
                        result[key] = updated[key]
                else:
                    result[key] = updated[key]

        # Then add any new keys from updated that weren't in base
        for key in updated:
            if key not in base:
                result[key] = updated[key]

        return result

    def _merge_replace_nulls(self, base, fallback):
        """
        Recursively replaces None values in base with values from fallback
        """
        if not isinstance(base, dict) or not isinstance(fallback, dict):
            return fallback if base is None else base

        result = {}
        all_keys = set(base.keys()) | set(fallback.keys())

        for key in all_keys:
            base_val = base.get(key)
            fallback_val = fallback.get(key)

            if isinstance(base_val, dict) and isinstance(fallback_val, dict):
                result[key] = self._merge_replace_nulls(base_val, fallback_val)
            elif base_val is None and fallback_val is not None:
                result[key] = fallback_val
            else:
                result[key] = base_val

        return result

    def run(self, terms, variables=None, **kwargs):
        """
        Look up and merge helm values for a component

        Args:
            terms: List containing component name and optionally current values
            variables: Template variables context
            **kwargs: Additional arguments

        Returns:
            List with single merged YAML string (Ansible lookup convention)
        """
        if variables is None:
            variables = {}

        if not terms or len(terms) > 2:
            raise AnsibleLookupError(
                "helm_values lookup expects one or two arguments: component_name, [current_values]"
            )

        component_name = terms[0]
        current_values = terms[1] if len(terms) > 1 else {}

        try:
            # Get base defaults (_metrics_server_helm_values)
            base_var_name = f"_{component_name}_helm_values"
            base_values_raw = variables.get(base_var_name)
            if base_values_raw is None:
                raise AnsibleLookupError(f"Base values variable '{base_var_name}' not found")
            base_defaults = self._templar.template(base_values_raw)

            # Get user overrides (metrics_server_helm_values)
            override_var_name = f"{component_name}_helm_values"
            user_overrides = self._templar.template(
                variables.get(override_var_name, {})
            )

            if current_values:
                # First, nullify keys that exist in current_values but not in user_overrides
                nullified_current = self._nullify_missing_values(current_values, user_overrides)
                
                # Then, nullify keys that exist in base_defaults but not in user_overrides
                nullified_from_base = self._nullify_missing_values(base_defaults, user_overrides)
                
                # Merge the two nullified sets
                merged_nullified = self._merge_replace_nulls(nullified_current, nullified_from_base)
                
                # Finally, replace remaining nulls with base defaults
                result = self._merge_replace_nulls(merged_nullified, base_defaults)
            else:
                # For initial deployment, compare against base_defaults and merge
                nullified_overrides = self._nullify_missing_values(base_defaults, user_overrides)
                result = self._merge_replace_nulls(nullified_overrides, base_defaults)

            # Format as YAML
            yaml_output = to_nice_yaml(result, indent=2)
            return [yaml_output]

        except Exception as e:
            raise AnsibleLookupError(
                f"Failed to lookup helm values for component '{component_name}': {str(e)}"
            )
