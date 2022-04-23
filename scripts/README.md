# Helper scripts

## Usage

The scripts in this directory use [Poetry](https://github.com/python-poetry/poetry) for describing dependencies and keeping a consistent lockfile. This lockfile is useful because it ensures every contributor is able to use the exact same dependencies.

To install Poetry, follow the Poetry [installation guide](https://python-poetry.org/docs/#installation).

To install from the lockfile, run `poetry update`.

To run a script, prefix it with `poetry run`. For example:

```
poetry run python update_example_schemas.py
```

Using `poetry run` ensures that you're running the python script using _this_ local environment, not your global environment.
