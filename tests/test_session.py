import pytest
from unittest.mock import patch, MagicMock
from app.session import SessionConfig, get_db


@patch("os.environ", {"DB_USERNAME": "user", "DB_PASSWORD": "pass", "DB_HOST": "localhost", "DB_NAME": "testdb"})
def test_session_config_url_with_env_vars():
    """Test that SessionConfig generates the correct URL when env vars are set."""
    config = SessionConfig()
    assert config.url() == "postgresql://user:pass@localhost:5432/testdb"


@patch("os.environ", {})
def test_session_config_url_fallback_to_sqlite():
    """Test that SessionConfig falls back to SQLite when env vars are missing."""
    config = SessionConfig()
    assert config.url() == "sqlite:///./test.db"


@patch("app.session.SessionLocal")
def test_get_db(mock_session_local):
    """Test that get_db creates and closes a session."""
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    generator = get_db()
    db = next(generator)  # Get the session
    assert db == mock_session

    # Close the session
    with pytest.raises(StopIteration):
        next(generator)

    mock_session.close.assert_called_once()
