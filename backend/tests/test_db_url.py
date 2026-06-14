"""Tests for managed-DB connection-string normalization (prod deploy)."""

import ssl

from app.core.database import db_connect_args, normalize_db_url


def test_normalize_adds_asyncpg_driver():
    assert normalize_db_url("postgresql://u:p@h:5432/db").startswith(
        "postgresql+asyncpg://"
    )
    # Already-asyncpg is idempotent.
    assert normalize_db_url("postgresql+asyncpg://u:p@h/db") == (
        "postgresql+asyncpg://u:p@h/db"
    )


def test_normalize_strips_libpq_only_params():
    out = normalize_db_url("postgresql://u:p@h:5432/db?sslmode=require")
    assert "sslmode" not in out
    assert out.startswith("postgresql+asyncpg://")
    # A DO-style URI with multiple libpq params keeps only asyncpg-safe ones.
    out2 = normalize_db_url("postgres://u:p@h:25060/defaultdb?sslmode=require&connect_timeout=10")
    assert "sslmode" not in out2 and "connect_timeout=10" in out2


def test_connect_args_ssl_verifies():
    args = db_connect_args("postgresql://u:p@h/db?sslmode=require")
    ctx = args["ssl"]
    assert isinstance(ctx, ssl.SSLContext)
    # Verification stays ON (no MITM exposure).
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_connect_args_none_for_plaintext_or_disabled():
    assert db_connect_args("postgresql://u:p@localhost/db") == {}
    assert db_connect_args("postgresql://u:p@localhost/db?sslmode=disable") == {}
