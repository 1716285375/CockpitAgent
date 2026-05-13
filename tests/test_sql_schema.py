from pathlib import Path


def test_mysql_init_schema_contains_required_tables():
    schema = Path("docker/mysql/init.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS user_preferences" in schema
    assert "CREATE TABLE IF NOT EXISTS audit_events" in schema
    assert "UNIQUE KEY uq_user_preference" in schema
