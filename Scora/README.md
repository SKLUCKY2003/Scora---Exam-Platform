# SCORA Examiner Insights — VS Code local project

This project serves the corrected HTML page and provides the two API endpoints the page expects.

## Important data note

The supplied `data.db` was included for reference. It does not contain populated exam records, and the table names/schema do not establish how real exam data should be queried. Therefore, the server defaults to **DEMO mode** and returns clearly synthetic example values so you can run and test the UI. It does **not** claim these are actual examiner results. Connecting genuine exam data requires the real application's database schema or backend queries.

## Requirements

- Python 3.9+ (no extra Python packages needed)
- Visual Studio Code (optional but recommended)

## Run it

1. Extract this folder if you downloaded the ZIP.
2. Open the `scora_examiner_vscode` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Run:

   ```bash
   python server.py
   ```

   On some Windows installations, use `py server.py` instead.

5. Open `http://127.0.0.1:8000/` to view the original interactive demo page.
6. To test the new API integration view, open this URL:

   `http://127.0.0.1:8000/?live=1&test_id=demo-test&section_id=demo-section&question_id=demo-question`

7. Check server/database status at `http://127.0.0.1:8000/api/health`.

Do not open the HTML by double-clicking it or using `file://`; the API calls need to be served from the same local server.

## Optional: disable demo responses

The app defaults to demo responses. To disable them, set `SCORA_DEMO_MODE=0` before starting the server.

**Windows PowerShell**

```powershell
$env:SCORA_DEMO_MODE="0"
python server.py
```

**macOS/Linux**

```bash
SCORA_DEMO_MODE=0 python3 server.py
```

In this mode, the API deliberately returns HTTP 501 for insights until a real database schema/backend implementation is provided. The server does not infer exam tables from the supplied database.

## Files

- `server.py` — local HTTP server and API routes
- `public/index.html` — corrected SCORA Examiner Insights HTML
- `data.db` — the database file supplied with the assignment
