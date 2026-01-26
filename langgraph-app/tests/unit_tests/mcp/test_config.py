"""Unit tests for MCPConfig.

Tests environment-based configuration loading for MCP infrastructure.
Following TDD - tests written BEFORE implementation.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from agent.mcp.config import MCPConfig


class TestMCPConfigDefaults:
    """Tests for MCPConfig default values."""

    def test_default_sukl_url(self):
        """Test default SÚKL MCP URL."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            assert config.sukl_url == "http://localhost:3000"

    def test_default_sukl_timeout(self):
        """Test default SÚKL timeout."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            assert config.sukl_timeout == 30.0

    def test_default_biomcp_url(self):
        """Test default BioMCP URL."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            assert config.biomcp_url == "http://localhost:8080"

    def test_default_biomcp_timeout(self):
        """Test default BioMCP timeout."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            assert config.biomcp_timeout == 60.0

    def test_default_biomcp_max_results(self):
        """Test default BioMCP max results."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            assert config.biomcp_max_results == 10

    def test_default_retry_config(self):
        """Test default retry configuration."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            assert config.max_retries == 3
            assert config.retry_base_delay == 1.0
            assert config.retry_max_delay == 30.0
            assert config.retry_jitter is True


class TestMCPConfigFromEnv:
    """Tests for loading config from environment variables."""

    def test_loads_sukl_url_from_env(self):
        """Test loading SÚKL URL from environment."""
        with patch.dict(os.environ, {"SUKL_MCP_URL": "http://custom:3001"}):
            config = MCPConfig.from_env()
            assert config.sukl_url == "http://custom:3001"

    def test_loads_sukl_timeout_from_env(self):
        """Test loading SÚKL timeout from environment."""
        with patch.dict(os.environ, {"SUKL_MCP_TIMEOUT": "45"}):
            config = MCPConfig.from_env()
            assert config.sukl_timeout == 45.0

    def test_loads_biomcp_url_from_env(self):
        """Test loading BioMCP URL from environment."""
        with patch.dict(os.environ, {"BIOMCP_URL": "http://biomcp-prod:8080"}):
            config = MCPConfig.from_env()
            assert config.biomcp_url == "http://biomcp-prod:8080"

    def test_loads_biomcp_timeout_from_env(self):
        """Test loading BioMCP timeout from environment."""
        with patch.dict(os.environ, {"BIOMCP_TIMEOUT": "120"}):
            config = MCPConfig.from_env()
            assert config.biomcp_timeout == 120.0

    def test_loads_biomcp_max_results_from_env(self):
        """Test loading BioMCP max results from environment."""
        with patch.dict(os.environ, {"BIOMCP_MAX_RESULTS": "25"}):
            config = MCPConfig.from_env()
            assert config.biomcp_max_results == 25

    def test_loads_retry_max_retries_from_env(self):
        """Test loading max retries from environment."""
        with patch.dict(os.environ, {"MCP_MAX_RETRIES": "5"}):
            config = MCPConfig.from_env()
            assert config.max_retries == 5

    def test_loads_retry_base_delay_from_env(self):
        """Test loading retry base delay from environment."""
        with patch.dict(os.environ, {"MCP_RETRY_BASE_DELAY": "2.5"}):
            config = MCPConfig.from_env()
            assert config.retry_base_delay == 2.5

    def test_loads_retry_max_delay_from_env(self):
        """Test loading retry max delay from environment."""
        with patch.dict(os.environ, {"MCP_RETRY_MAX_DELAY": "60"}):
            config = MCPConfig.from_env()
            assert config.retry_max_delay == 60.0

    def test_loads_retry_jitter_true_from_env(self):
        """Test loading retry jitter=true from environment."""
        with patch.dict(os.environ, {"MCP_RETRY_JITTER": "true"}):
            config = MCPConfig.from_env()
            assert config.retry_jitter is True

    def test_loads_retry_jitter_false_from_env(self):
        """Test loading retry jitter=false from environment."""
        with patch.dict(os.environ, {"MCP_RETRY_JITTER": "false"}):
            config = MCPConfig.from_env()
            assert config.retry_jitter is False


class TestMCPConfigRetryConfigIntegration:
    """Tests for RetryConfig creation from MCPConfig."""

    def test_creates_retry_config(self):
        """Test creating RetryConfig from MCPConfig."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()
            retry_config = config.to_retry_config()

            from agent.mcp.domain.entities import RetryConfig

            assert isinstance(retry_config, RetryConfig)
            assert retry_config.max_retries == config.max_retries
            assert retry_config.base_delay == config.retry_base_delay
            assert retry_config.max_delay == config.retry_max_delay
            assert retry_config.jitter == config.retry_jitter


class TestMCPConfigImmutability:
    """Tests for MCPConfig immutability."""

    def test_config_is_frozen(self):
        """Test that MCPConfig is immutable (frozen dataclass)."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig.from_env()

            with pytest.raises(AttributeError):
                config.sukl_url = "http://modified:3000"
