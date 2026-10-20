# envcensus

Audit environment variables referenced in source code against `.env` and `.env.example` files. `envcensus` reports variables used in code but missing from your example file, variables declared but never used, and drift between `.env` and `.env.example`.

## Features

- Scans Python, JavaScript, TypeScript, shell, YAML, TOML, and JSON files.
- Detects common access patterns such as `os.getenv`, `os.environ`, and `process.env`.
- Compares discovered references with `.env` and `.env.example`.
- Supports text and JSON output.
- Can fail CI when code references variables missing from the example file.
- Uses only the Python standard library.

## Install

```bash
pip install .
```

Or run directly:

```bash
python envcensus.py .
```

## Usage

Audit the current project:

```bash
envcensus .
```

Use custom env file names:

```bash
envcensus . --env-file .env.local --example-file .env.example
```

Emit JSON:

```bash
envcensus . --format json
```

Fail in CI when referenced variables are missing from the example file:

```bash
envcensus . --fail-on-missing
```

## Example output

```text
envcensus report for /path/to/project
referenced variables: 3
variables in env file: 2
variables in example file: 2

Missing from example file:
  - API_TOKEN

Declared in example but unused:
  (none)

Only in env file:
  (none)

Missing from env file:
  (none)
```

## License

MIT
