# `glance_image`

This role uploads an image into OpenStack Glance and keeps it in sync with the
declared source.

## Sources

HTTP remains the default:

```yaml
glance_image_url: https://images.example/image.qcow2
```

An image can instead be extracted from a public or authenticated OCI image.
The manifest and payload must both be immutable:

```yaml
glance_image_oci_reference: registry.example/image@sha256:<manifest-digest>
glance_image_oci_path: /images/image.qcow2
glance_image_oci_sha512: <qcow2-sha512>
# glance_image_oci_authfile: /run/secrets/registry-auth.json
```

The role installs `skopeo`, selects the declared Linux architecture, converts
layers to gzip during the copy, streams the requested regular file from gzip
or uncompressed layers, and verifies SHA512 before upload. An OCI reference
without a manifest digest is rejected.

## Change Detection

For an HTTP source, the role sends a `HEAD` request to `glance_image_url` to
check for changes. For OCI, the digest-pinned reference, artifact path, and
required SHA512 form the source identity. Download and upload are skipped when
that identity is already recorded on the Glance image.

If the server returns an `ETag` header, the role captures it and compares it
against the `atmosphere:image:etag` property stored on any existing image with
the same name. A re-upload is triggered when:

- no image with that name exists yet, or
- the `atmosphere:image:url` property differs from the selected source
  identity, or
- an `ETag` is available and it differs from the stored
  `atmosphere:image:etag`.

If the server does not return an `ETag` header, the role falls back to URL-only
change detection. As long as `glance_image_url` stays the same the role is
idempotent; when the URL changes a re-upload occurs.

## Upload Sequence

To ensure a service image is always available under the expected name, the role
uploads the new image first and only renames the previous image as obsolete
once the upload has succeeded. If the upload fails, the old image remains
available under the original name.

The outdated image is renamed to `<name>-<short-etag>` or to
`<name>-<short-id>` when the existing image carries no stored `ETag`. Its tags
are replaced with `atmosphere:image:obsolete`.

## Properties Stamped On Uploaded Images

- `atmosphere:image:url` - the HTTP URL or immutable
  `oci://<reference>#<path>` source identity.
- `atmosphere:image:etag` - the HTTP `ETag`, when available, or the required
  OCI payload SHA512.

Images uploaded by earlier versions of Atmosphere lack these properties and are
treated as outdated on the next run, which causes a one-time re-upload.
