from app.tools.preference.user_preference import MySQLPreferenceStore


def test_mysql_preference_store_parses_dsn():
    store = MySQLPreferenceStore("mysql+aiomysql://user:pass@localhost:3307/cockpit")

    assert store.connection_kwargs["host"] == "localhost"
    assert store.connection_kwargs["port"] == 3307
    assert store.connection_kwargs["user"] == "user"
    assert store.connection_kwargs["password"] == "pass"
    assert store.connection_kwargs["db"] == "cockpit"
