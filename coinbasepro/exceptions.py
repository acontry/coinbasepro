class CoinbaseAPIError(IOError):
    """There was an ambiguous exception that occurred."""


class BadRequest(CoinbaseAPIError, ValueError):
    """An invalid API format was used."""


class InvalidAPIKey(CoinbaseAPIError, ValueError):
    """An invalid API key was used."""


class InvalidAuthorization(CoinbaseAPIError, ValueError):
    """API key does not have sufficient authorization for an action."""


class RateLimitError(CoinbaseAPIError):
    """Too many requests were made."""
