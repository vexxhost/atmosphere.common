# `ansible-collection-flux`

This collection allows the deployment of Flux into a Kubernetes cluster.

## Installation

You can either install it manually using `ansible-galaxy`:

```bash
ansible-galaxy collection install vexxhost.flux
```

Alternatively, you can add it to your `requirements.yaml` file if you are managing
multiple collections:

<!--
x-release-please-start-version
-->

```yaml
dependencies:
  - name: vexxhost.flux
    version: 0.1.3
```

<!--
x-release-please-end
-->

You can then install it using:

```bash
ansible-galaxy collection install -r requirements.yaml
```

## Usage

You can either call the `ansible-playbook` command directly for this play, while
setting the `target` variable to an inventory group, a list of hosts or a single host
that has a `KUBECONFIG` pointing to the cluster you want to deploy Flux to:

```bash
ansible-playbook vexxhost.flux.site -e target=controllers
```

Alternatively, you can add this to be part of your playbooks:

```yaml
- ansible.builtin.import_playbook: vexxhost.flux.site
  vars:
    target: controllers
```
