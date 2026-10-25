"""Server-only Garmin Personal API access check. Never logs or returns credentials."""

from datetime import datetime, timezone
import base64
import binascii
import json
import math
import os
import hashlib
from pathlib import Path
from threading import RLock
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .garmin_mapping import map_readings

TOKEN_URL = (
    "https://personal.connectapi.garmin.com/"
    "personalapitoken-service/personal-api/personal-api-key/token"
)
KEY_FILE = Path(__file__).resolve().parent.parent / ".secrets" / "garmin-personal-api-key"


class NoCredentialRedirect(HTTPRedirectHandler):
    """Do not forward a credential-bearing request to a redirect destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GarminAccess:
    def __init__(self, key_file=None, environment=None, opener=None):
        self.key_file = Path(key_file) if key_file is not None else KEY_FILE
        self.environment = environment if environment is not None else os.environ
        self.opener = opener or build_opener(NoCredentialRedirect())
        self._lock = RLock()
        self._bearer = None
        self._expires = 0
        self._fingerprint = None
        self._cooldown_until = 0

    def _key(self):
        value = self.environment.get("GARMIN_PERSONAL_API_KEY")
        if value is None:
            try:
                value = self.key_file.read_text(encoding="utf-8").strip()
            except FileNotFoundError:
                return ""
            except OSError:
                raise ValueError(
                    "Garmin key file cannot be read. Check the local file permissions."
                ) from None
        value = value.strip()
        if not value:
            return ""
        if len(value) > 4096 or any(
            ord(character) < 33 or ord(character) > 126 for character in value
        ):
            raise ValueError("Garmin key format is invalid. Use the new key on a single line.")
        return value

    def configuration(self):
        try:
            return "Configured locally" if self._key() else "Not configured"
        except ValueError:
            return "Local configuration error"

    def _obtain_token(self):
        key = self._key()
        if not key:
            raise ValueError("Garmin is not configured. Follow the local setup instructions below.")
        request = Request(
            TOKEN_URL,
            data=b"",
            method="POST",
            headers={
                "Authorization": f"ApiKey {key}",
                "Accept": "text/plain, application/json",
            },
        )
        try:
            with self.opener.open(request, timeout=8) as response:
                raw = response.read(16385)
            if not raw or len(raw) > 16384:
                raise ValueError(
                    "Garmin returned an unexpected token response. No access was verified."
                )
            # Garmin's official Python client documents a plain-text bearer response.
            # Some gateways use a JSON access_token envelope; neither value leaves this method.
            token = raw.decode("utf-8").strip()
            if token.startswith("{"):
                token = json.loads(token).get("access_token", "")
            if (
                not isinstance(token, str)
                or len(token.split(".")) != 3
                or any(character.isspace() for character in token)
            ):
                raise ValueError(
                    "Garmin returned an unexpected token response. No access was verified."
                )
            try:
                payload = token.split(".")[1]
                expiry = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))[
                    "exp"
                ]
                if (
                    not isinstance(expiry, (int, float))
                    or isinstance(expiry, bool)
                    or not math.isfinite(expiry)
                    or not (expiry > datetime.now(timezone.utc).timestamp())
                ):
                    raise ValueError("Invalid expiry")
            except (ValueError, KeyError, TypeError, binascii.Error):
                raise ValueError(
                    "Garmin returned an invalid or expired token. No access was verified."
                ) from None
        except HTTPError as error:
            if error.code in {401, 403}:
                message = (
                    "Garmin rejected access. The key may be expired, revoked or not permitted."
                )
            elif error.code == 429:
                message = "Garmin's request limit was reached. Wait before trying again."
            else:
                message = (
                    "Garmin access check failed. Retry later; no watch connection was confirmed."
                )
            raise ValueError(message) from None
        except (URLError, OSError, TimeoutError):
            raise ValueError(
                "Garmin could not be reached. Check the internet connection and retry."
            ) from None
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError(
                "Garmin returned an unreadable response. No access was verified."
            ) from None
        return token, expiry

    def check(self):
        self._obtain_token()
        return dict(
            state="API access verified",
            checkedAt=datetime.now(timezone.utc).isoformat(),
            message="Garmin accepted the server-side credential exchange. No health data was requested. "
            "This does not confirm a live watch connection or available readings.",
        )

    def clear(self):
        with self._lock:
            self._bearer, self._expires, self._fingerprint = None, 0, None

    def readings(self, day):
        from datetime import date

        try:
            selected = date.fromisoformat(day)
        except (ValueError, TypeError):
            raise ValueError("Choose a valid Garmin calendar date.") from None
        if selected > datetime.now(timezone.utc).date():
            raise ValueError("Choose today or an earlier date.")
        with self._lock:
            if datetime.now(timezone.utc).timestamp() < self._cooldown_until:
                raise ValueError("Garmin rate-limited requests. Refresh is paused; retry later.")
            key = self._key()
            if not key:
                self.clear()
                raise ValueError(
                    "Garmin is not configured. Save the key in the private local file first."
                )
            fingerprint = hashlib.sha256(key.encode()).digest()
            if (
                fingerprint != self._fingerprint
                or self._expires <= datetime.now(timezone.utc).timestamp() + 60
            ):
                self.clear()
                self._bearer, self._expires = self._obtain_token()
                self._fingerprint = fingerprint
            payloads, errors = [], []
            for name, path in (
                (
                    "Heart rate",
                    f"/wellness-service/wellness/dailyHeartRate?date={selected.isoformat()}",
                ),
            ):
                request = Request(
                    "https://personal.connectapi.garmin.com" + path,
                    headers={
                        "Authorization": f"Bearer {self._bearer}",
                        "Accept": "application/json",
                    },
                )
                try:
                    with self.opener.open(request, timeout=8) as response:
                        raw = response.read(2_000_001)
                    if len(raw) > 2_000_000:
                        raise ValueError("Response too large")
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        raise ValueError("Unexpected schema")
                    payloads.append(payload)
                except HTTPError as error:
                    if error.code == 429:
                        try:
                            delay = min(
                                3600, max(30, int((error.headers or {}).get("Retry-After", "60")))
                            )
                        except ValueError:
                            delay = 60
                        self._cooldown_until = datetime.now(timezone.utc).timestamp() + delay
                        raise ValueError(
                            "Garmin rate-limited requests. Refresh is paused; retry later."
                        ) from None
                    if error.code == 401:
                        self.clear()
                        raise ValueError(
                            "Garmin authorisation expired or was revoked. Check the owner's key and retry."
                        ) from None
                    errors.append(
                        f"{name}: Garmin returned HTTP {error.code}; no new measurement available."
                    )
                    payloads.append(None)
                except (ValueError, UnicodeError, URLError, OSError, TimeoutError):
                    errors.append(
                        f"{name}: data could not be retrieved. Retry after checking Garmin sync and internet access."
                    )
                    payloads.append(None)
            result = map_readings(payloads[0], day=selected.isoformat())
            result["errors"] = errors
            return result
