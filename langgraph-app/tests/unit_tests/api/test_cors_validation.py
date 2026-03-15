"""Tests for CORS production safety (US2).

Verifies that:
- Production fails fast with empty CORS origins
- Production fails fast with wildcard origins
- Development allows wildcard origins
"""

import pytest
from pydantic import ValidationError

from api.config import Settings


class TestCORSValidation:
    """Test CORS startup validation in config.py."""

    def test_production_rejects_empty_cors_origins(self):
        """Production MUST fail fast when cors_origins is empty."""
        with pytest.raises(ValidationError):
            Settings(
                environment="production",
                cors_origins=[],
            )

    def test_production_rejects_wildcard_cors(self):
        """Production MUST reject wildcard '*' in cors_origins."""
        with pytest.raises(ValidationError):
            Settings(
                environment="production",
                cors_origins=["*"],
            )

    def test_production_rejects_wildcard_mixed(self):
        """Production MUST reject if wildcard is mixed with real origins."""
        with pytest.raises(ValidationError):
            Settings(
                environment="production",
                cors_origins=["https://app.example.com", "*"],
            )

    def test_production_accepts_valid_origins(self):
        """Production accepts explicit, non-wildcard origins."""
        s = Settings(
            environment="production",
            cors_origins=["https://app.example.com", "https://admin.example.com"],
        )
        assert s.cors_origins == [
            "https://app.example.com",
            "https://admin.example.com",
        ]

    def test_development_allows_empty_cors(self):
        """Development MAY use empty cors_origins (defaults to wildcard)."""
        s = Settings(
            environment="development",
            cors_origins=[],
        )
        assert s.cors_origins == []

    def test_development_allows_wildcard(self):
        """Development MAY use wildcard origins."""
        s = Settings(
            environment="development",
            cors_origins=["*"],
        )
        assert s.cors_origins == ["*"]
