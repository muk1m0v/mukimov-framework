# Releases

For substantial library changes, prepare and publish a PyPI release as part of the task. For small changes, such as a typo fix or a minor documentation edit, finish and verify the change first, then ask the maintainer whether to publish it now or include it in a later release. Wait for their answer before pushing a release tag, unless they already explicitly asked to publish that change.

When publishing, bump the package version, verify the release, and use the GitHub Actions Trusted Publishing workflow. Verify the release and its file attestations on PyPI before reporting publication complete. Do not reuse an existing PyPI version.
