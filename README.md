# ostorlab

Work in Progress.

## Testing

Work in Progress.

### Docker-based tests

Tests marked with `docker` tag are integration test that interact with the Docker API. Make sure to disable them in
test environment where Docker API is not accessible:

```shell
pytest -v -m "not docker"
```