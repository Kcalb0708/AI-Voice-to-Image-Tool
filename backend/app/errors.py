class ProviderConfigurationError(RuntimeError):
    """Raised when a configured provider cannot be called."""


class ProviderResponseError(RuntimeError):
    """Raised when a provider response cannot be used safely."""
