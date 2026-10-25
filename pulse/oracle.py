"""Protected, read-only ORDS client. Secrets/tokens remain on the Python server."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from threading import RLock
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .oracle_mapping import map_current_patient, map_latest_vitals, map_open_alert

BASE = "https://oracleapex.com/ords/maham_ali/"
CONFIG_FILE = Path(__file__).resolve().parent.parent / ".secrets" / "oracle.json"


class NoOracleRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OracleService:
    def __init__(self, config_file=None, environment=None, opener=None):
        self.config_file = Path(config_file) if config_file else CONFIG_FILE
        self.environment = environment if environment is not None else os.environ
        self.opener = opener or build_opener(NoOracleRedirect())
        self.lock = RLock()
        self._token, self._expires, self._fingerprint = None, 0, None

    def _credentials(self):
        try:
            config = json.loads(self.config_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            config = {}
        except (OSError, ValueError):
            raise ValueError("Oracle private configuration cannot be read.") from None
        if not isinstance(config, dict):
            raise ValueError("Oracle private configuration must be a JSON object.")
        identifier = self.environment.get("ORACLE_CLIENT_ID", config.get("client_id", ""))
        secret = self.environment.get("ORACLE_CLIENT_SECRET", config.get("client_secret", ""))
        if not all(isinstance(v, str) and v.strip() for v in (identifier, secret)):
            raise ValueError(
                "Oracle connection is not configured yet. The protected API credentials are required."
            )
        return identifier.strip(), secret.strip()

    def configuration(self):
        try:
            self._credentials()
            return "Configured locally"
        except ValueError:
            return "Not configured"

    def _json(self, request):
        try:
            with self.opener.open(request, timeout=15) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("Oracle response is too large.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("Oracle returned an unexpected response.")
            return result
        except HTTPError as error:
            if error.code == 401:
                self._token, self._expires = None, 0
                message = (
                    "Oracle rejected backend access. Check the protected API client and read role."
                )
            elif error.code == 403:
                message = (
                    "Oracle could not read the requested resource. "
                    "Check the API permissions and source tables/views."
                )
            elif error.code == 404:
                message = "The protected Oracle API is not published at the agreed path yet."
            else:
                message = f"Oracle API request failed (HTTP {error.code}). Retry later."
            raise ValueError(message) from None
        except (URLError, OSError, TimeoutError, UnicodeError, json.JSONDecodeError):
            raise ValueError("Oracle could not be read. Check the connection and retry.") from None

    def _authorize(self):
        identifier, secret = self._credentials()
        fingerprint = hashlib.sha256((identifier + "\0" + secret).encode()).digest()
        now = datetime.now(timezone.utc).timestamp()
        if self._token and self._fingerprint == fingerprint and self._expires > now + 30:
            return
        self._token, self._expires = None, 0
        authorization = base64.b64encode((identifier + ":" + secret).encode()).decode()
        data = self._json(
            Request(
                BASE + "oauth/token",
                method="POST",
                data=urlencode({"grant_type": "client_credentials"}).encode(),
                headers={
                    "User-Agent": "PulsePrototype/1.0",
                    "Authorization": "Basic " + authorization,
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        )
        token, expiry = data.get("access_token"), data.get("expires_in")
        if not isinstance(token, str) or not token or any(c.isspace() for c in token):
            raise ValueError("Oracle did not supply a usable access token.")
        if (
            not isinstance(expiry, (int, float))
            or isinstance(expiry, bool)
            or not 0 < expiry <= 86400
        ):
            raise ValueError("Oracle token lifetime is unavailable.")
        self._token, self._expires, self._fingerprint = token, now + expiry, fingerprint

    def _rows(self, resource):
        url = BASE + "pulse/v1/" + resource + "/"
        expected_path = urlsplit(url).path
        rows, seen = [], set()
        for _ in range(20):
            parts = urlsplit(url)
            if (
                parts.scheme != "https"
                or parts.netloc != "oracleapex.com"
                or parts.path != expected_path
                or parts.fragment
                or url in seen
            ):
                raise ValueError("Oracle returned an unsafe or repeated pagination link.")
            seen.add(url)
            result = self._json(
                Request(
                    url,
                    headers={
                        "User-Agent": "PulsePrototype/1.0",
                        "Authorization": "Bearer " + self._token,
                        "Accept": "application/json",
                    },
                )
            )
            items = result.get("items")
            if not isinstance(items, list) or not all(isinstance(row, dict) for row in items):
                raise ValueError("Oracle returned an unexpected row format.")
            rows.extend(items)
            if not result.get("hasMore", False):
                return rows
            links = result.get("links", [])
            if not isinstance(links, list) or not all(isinstance(link, dict) for link in links):
                raise ValueError("Oracle returned an unexpected pagination format.")
            url = next(
                (link.get("href") for link in links if link.get("rel") == "next"),
                None,
            )
            if not isinstance(url, str):
                raise ValueError(
                    "Oracle pagination is incomplete; partial rows were not displayed."
                )
        raise ValueError("Oracle pagination limit reached; partial rows were not displayed.")

    def snapshot(self):
        with self.lock:
            self._authorize()
            return dict(
                patients=[map_current_patient(row) for row in self._rows("patients")],
                readings=[map_latest_vitals(row) for row in self._rows("readings/latest")],
                alerts=[map_open_alert(row) for row in self._rows("alerts")],
                fetchedAt=datetime.now(timezone.utc).isoformat(),
            )
