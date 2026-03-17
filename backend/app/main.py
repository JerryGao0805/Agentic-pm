from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import settings
from app.db import probe_mysql

app = FastAPI(title="Project Management MVP Backend")


HELLO_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PM MVP Backend</title>
    <style>
      body {
        margin: 0;
        padding: 40px 24px;
        font-family: "Segoe UI", Arial, sans-serif;
        color: #032147;
        background: #f7f8fb;
      }
      main {
        max-width: 720px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid rgba(3, 33, 71, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
      }
      h1 {
        margin-top: 0;
      }
      pre {
        margin-top: 16px;
        background: #f7f8fb;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(3, 33, 71, 0.08);
        overflow-x: auto;
      }
      code {
        color: #209dd7;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Hello from the PM MVP backend</h1>
      <p>Backend scaffold is running in Docker.</p>
      <p>Checking <code>/api/health</code>:</p>
      <pre id="health-output">Loading...</pre>
    </main>
    <script>
      const output = document.getElementById("health-output");
      fetch("/api/health")
        .then(async (response) => {
          const payload = await response.json();
          output.textContent = JSON.stringify(payload, null, 2);
        })
        .catch((error) => {
          output.textContent = `Health call failed: ${error.message}`;
        });
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def read_root() -> str:
    return HELLO_PAGE


@app.get("/api/health")
def health() -> dict:
    is_connected, error = probe_mysql()
    return {
        "status": "ok" if is_connected else "degraded",
        "service": settings.app_name,
        "database": {
            "connected": is_connected,
            "host": settings.db_host,
            "port": settings.db_port,
            "name": settings.db_name,
            "error": error,
        },
    }
