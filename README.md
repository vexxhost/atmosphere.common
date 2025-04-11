# `ansible-collection-flux`

This collection allows the deployment of Flux into a Kubernetes cluster, you can
either install it manually using `ansible-galaxy`:

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
    version: 0.1.2
```

<!--
x-release-please-end
-->

You can then install it using:

```bash
ansible-galaxy collection install -r requirements.yaml
```
