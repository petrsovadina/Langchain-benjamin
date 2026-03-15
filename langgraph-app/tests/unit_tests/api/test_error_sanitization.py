"""Tests for error response sanitization (US1).

Verifies that:
- Production mode sends generic error messages to clients
- Development mode sends raw error details for debugging
- Server-side logging includes full error details regardless of mode
"""

from unittest.mock import AsyncMock, MagicMock, patch

from api.config import Settings


class TestSSEErrorSanitization:
    """Test SSE stream error sanitization in routes.py."""

    async def _collect_error_events(
        self, environment: str, cors_origins: list[str]
    ) -> list[str]:
        """Helper: run consult_stream_generator with a forced error and collect events."""
        test_settings = Settings(
            environment=environment,
            cors_origins=cors_origins,
        )

        # Force an exception by making the MCP client import fail
        with (
            patch("api.routes.settings", test_settings),
            patch(
                "api.routes.graph",
            ) as mock_graph,
        ):
            # Make astream_events raise inside the async for loop
            async def failing_astream(*args, **kwargs):
                raise RuntimeError("DB connection pool exhausted")
                yield  # noqa: unreachable — makes this an async generator

            mock_graph.astream_events = failing_astream

            from api.routes import consult_stream_generator

            events = []
            async for event in consult_stream_generator(
                query="test", mode="quick", user_id=None
            ):
                events.append(event)

        return events

    async def test_production_mode_hides_error_details(self):
        """SSE error events MUST NOT contain raw exception text in production."""
        events = await self._collect_error_events(
            environment="production",
            cors_origins=["https://app.example.com"],
        )

        error_data = [e for e in events if '"internal_error"' in e]
        assert len(error_data) > 0, "Expected at least one error event"

        for event in error_data:
            assert "An unexpected error occurred" in event
            assert "DB connection pool exhausted" not in event

    async def test_development_mode_shows_error_details(self):
        """Development mode includes raw error details for debugging."""
        events = await self._collect_error_events(
            environment="development",
            cors_origins=[],
        )

        error_data = [e for e in events if '"internal_error"' in e]
        assert len(error_data) > 0, "Expected at least one error event"

        # Development mode should include the raw error message
        combined = "".join(error_data)
        assert "DB connection pool exhausted" in combined

    async def test_error_logged_server_side_in_production(self):
        """Full error MUST be logged server-side even in production."""
        prod_settings = Settings(
            environment="production",
            cors_origins=["https://app.example.com"],
        )

        async def failing_astream(*args, **kwargs):
            raise RuntimeError("Secret internal error")
            yield  # noqa: unreachable

        with (
            patch("api.routes.settings", prod_settings),
            patch("api.routes.logger") as mock_logger,
            patch("api.routes.graph") as mock_graph,
        ):
            mock_graph.astream_events = failing_astream

            from api.routes import consult_stream_generator

            events = []
            async for event in consult_stream_generator(
                query="test", mode="quick", user_id=None
            ):
                events.append(event)

        # Logger must have been called with error details
        mock_logger.error.assert_called()
        # Verify exc_info=True in the call
        call_kwargs = mock_logger.error.call_args
        assert call_kwargs[1].get("exc_info") is True
        # Client should NOT see the raw error
        assert "Secret internal error" not in "".join(events)


class TestHealthEndpointSanitization:
    """Test health endpoint error sanitization."""

    async def test_health_production_hides_sukl_error(self):
        """Health endpoint MUST NOT expose raw SUKL errors in production."""
        prod_settings = Settings(
            environment="production",
            cors_origins=["https://app.example.com"],
        )

        with (
            patch("api.routes.settings", prod_settings),
            patch.dict(
                "sys.modules",
                {"agent.graph": MagicMock(_sukl_client=None, _biomcp_client=None)},
            ),
            patch("api.routes.get_pool", new_callable=AsyncMock) as mock_pool,
        ):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            mock_pool.return_value.acquire.return_value.__aenter__ = AsyncMock(
                return_value=mock_conn
            )
            mock_pool.return_value.acquire.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

            from api.routes import health_check

            response = await health_check()

        for _key, value in response.mcp_servers.items():
            if "error" in str(value):
                assert value == "error", (
                    f"Expected 'error' but got '{value}' — raw error leaked"
                )

    async def test_health_production_hides_db_error(self):
        """Health endpoint MUST NOT expose raw DB errors in production."""
        prod_settings = Settings(
            environment="production",
            cors_origins=["https://app.example.com"],
        )

        with (
            patch("api.routes.settings", prod_settings),
            patch.dict(
                "sys.modules",
                {"agent.graph": MagicMock(_sukl_client=None, _biomcp_client=None)},
            ),
            patch("api.routes.get_pool", side_effect=OSError("Connection refused")),
        ):
            from api.routes import health_check

            response = await health_check()

        assert response.database == "error", (
            f"Expected 'error' but got '{response.database}' — raw DB error leaked"
        )

    async def test_health_development_shows_error_details(self):
        """Development mode includes error details in health response."""
        dev_settings = Settings(
            environment="development",
            cors_origins=[],
        )

        with (
            patch("api.routes.settings", dev_settings),
            patch.dict(
                "sys.modules",
                {"agent.graph": MagicMock(_sukl_client=None, _biomcp_client=None)},
            ),
            patch("api.routes.get_pool", side_effect=OSError("Connection refused")),
        ):
            from api.routes import health_check

            response = await health_check()

        # In dev mode, raw error details should be present
        assert response.database is not None
        assert "Connection refused" in response.database
