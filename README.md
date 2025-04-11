# `atmosphere.common`

This collections contains a set of common Ansible roles and playbooks that can
be used to deploy and manage various components on a Kubernetes cluster.  They
can be used individually or however their primary purpose is to be used as part
of the [Atmosphere](https://github.com/vexxhost/atmosphere) project.

## Installation

You can either install this collection manually using the `ansible-galaxy` command:

```bash
ansible-galaxy collection install atmosphere.common
```

Alternatively, you can add it to your `requirements.yaml` file if you are managing
multiple collections:

<!--
x-release-please-start-version
-->

```yaml
dependencies:
  - name: atmosphere.common
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

Each role contains a `README.md` file that describes how to use it.  There are some
pre-composed playbooks that allow you to deploy some components quickly.  The playbooks
are located in the `playbooks` directory.  You can use them as they are or import
them in your own playbooks.

All of the playbooks will have a `target` variable that you can set to specify the
target hosts to run the playbook on.  In general, this should be set to a group
of hosts in your inventory that have a `KUBECONFIG` pointing to the cluster you
want to deploy the component to.  The playbooks will use the `KUBECONFIG` variable
to determine the context to use when deploying the component.

### Example

To deploy the `flux` playbook to the `controllers` group, you can run the following
command:

```bash
ansible-playbook atmosphere.common.flux -e target=controllers
```

Alternatively, you can add this to be part of your playbooks:

```yaml
- ansible.builtin.import_playbook: atmosphere.common.flux
  vars:
    target: controllers
```
