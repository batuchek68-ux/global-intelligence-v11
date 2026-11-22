"""Disabled legacy script: do not extract browser session cookies.

The former version printed authentication cookies to stdout. This replacement
intentionally performs no browser or network access. Use an official provider
OAuth/API flow and store credentials in a local secret manager instead.
"""

if __name__ == "__main__":
    raise SystemExit("Cookie extraction is disabled. Revoke any previously exposed session and use official authentication.")
