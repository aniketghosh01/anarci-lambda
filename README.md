# Biologics-research-helix-wrapper-api

## Dependencies

Installation from source requires the private packages `ts-ids-core` and `ts-ids-components`. The `ts-pypi-external` package repository has already been added in `pyproject.toml`. For future reference:

```
poetry source add --priority=supplemental ts-pypi-external https://tetrascience.jfrog.io/artifactory/api/pypi/ts-pypi-external/simple/
```

In order to fetch packages from the `ts-pypi-external` repository, a reference token still needs to be added locally with:

```
poetry config http-basic.ts-pypi-external "" "<reference_token>"
```

If needed, new packages from `ts-pypi-external` can be added as dependencies using:

```
poetry add <package-name> --source ts-pypi-external
```

## Create tetrascience IDS

New tetrascience IDS artifacts are created using the `ts-cli` interface:

```
ts-cli publish . --type ids --config cfg.json --interactive
```

where `cfg.json` contains the following info (bayer-dev environment):

```
{
    "api_url": "https://api.bayer-dev.tetrascience.com/v1",
    "auth_token": "<api token>",
    "org": "bayer-br-dev",
    "ignore_ssl": false
}
```