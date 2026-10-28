"""Build the static frontend and configure the same-origin API proxy."""
import os
from pathlib import Path
from urllib.parse import urlsplit
import build_vercel  # Copies only the public HTML and video assets.

url = os.environ.get('BACKEND_URL', '').strip()
parts = urlsplit(url)
if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
        or parts.path not in ('', '/') or parts.query or parts.fragment
        or any(c.isspace() for c in url)):
    raise SystemExit('BACKEND_URL must be the HTTPS origin of the deployed Python API, without a path or credentials.')
try:
    parts.port  # Reject invalid ports.
except ValueError:
    raise SystemExit('BACKEND_URL has an invalid port.')
Path('public/_redirects').write_text(f'/api/* {url.rstrip("/")}/api/:splat 200\n', encoding='utf-8')
