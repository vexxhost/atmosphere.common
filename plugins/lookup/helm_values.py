# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from ansible.plugins.lookup import LookupBase
from ansible.plugins.filter.core import combine, to_nice_yaml
from ansible.errors import AnsibleLookupError

DOCUMENTATION = """
name: helm_values
short_description: Lookup and merge helm values for a component
description:
  - Looks up base and override helm values for a single component
  - Merges them using combine(recursive=True) and formats as YAML
  - Expects variables named _<component>_helm_values and <component>_helm_values
options:
  _terms:
    description: Component name to lookup helm values for
    required: true
    type: str
"""

EXAMPLES = """
- ansible.builtin.debug:
    msg: "{{ lookup('atmosphere.common.helm_values', 'metrics_server') }}"
"""

RETURN = """
_value:
  description: Merged helm values as YAML string
  type: str
"""


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        """
        Look up and merge helm values for a single component

        Args:
            terms: List containing single component name
            variables: Template variables context

        Returns:
            List with single merged YAML string (Ansible lookup convention)
        """
        if variables is None:
            variables = {}

        if len(terms) != 1:
            raise AnsibleLookupError(
                "helm_values lookup expects exactly one component name"
            )

        component_name = terms[0]

        try:
            # Look up base values: _<component_name>_helm_values
            base_var_name = f"_{component_name}_helm_values"
            base_values_raw = variables.get(base_var_name)

            if base_values_raw is None:
                raise AnsibleLookupError(
                    f"Base values variable '{base_var_name}' not found for "
                    f"component '{component_name}'"
                )

            # Template the base values
            base_values = self._templar.template(base_values_raw)

            # Look up override values: <component_name>_helm_values (optional)
            override_var_name = f"{component_name}_helm_values"
            overrides_raw = variables.get(override_var_name, {})

            # Template the override values
            overrides = self._templar.template(overrides_raw)

            # Merge using built-in combine filter
            merged = combine(base_values, overrides, recursive=True)

            # Format as YAML using built-in to_nice_yaml filter
            yaml_output = to_nice_yaml(merged, indent=2)

            # Return as single-item list (Ansible lookup convention)
            return [yaml_output]

        except Exception as e:
            raise AnsibleLookupError(
                f"Failed to lookup helm values for component '{component_name}': {str(e)}"
            )
