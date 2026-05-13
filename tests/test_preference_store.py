from app.tools.preference.user_preference import MySQLPreferenceStore, parse_mysql_dsn


def test_mysql_preference_store_parses_dsn():
    store = MySQLPreferenceStore("mysql+aiomysql://user:pass@localhost:3307/cockpit")

    assert store.connection_kwargs["host"] == "localhost"
    assert store.connection_kwargs["port"] == 3307
    assert store.connection_kwargs["user"] == "user"
    assert store.connection_kwargs["password"] == "pass"
    assert store.connection_kwargs["db"] == "cockpit"


def test_parse_mysql_dsn_supports_mysql_scheme():
    parsed = parse_mysql_dsn("mysql://user:pass@db/cockpit")

    assert parsed["host"] == "db"
    assert parsed["port"] == 3306
    assert parsed["db"] == "cockpit"
