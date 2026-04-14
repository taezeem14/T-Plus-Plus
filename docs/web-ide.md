# T++ Web IDE

T++ includes a minimal web IDE powered by the JSON execution API.

## Start Server

```powershell
tpp api --serve --host 127.0.0.1 --port 8787
```

Open in browser:

- http://127.0.0.1:8787/

## API Endpoint

- POST /run
- Content-Type: application/json

Example body:

```json
{
  "source": "let x be 5\nsay x",
  "mode": "run"
}
```

## Response

Example response fields:

- ok
- mode
- stdout
- error
- error_category
- tests
- summary
