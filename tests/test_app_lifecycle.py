from app.main import create_app


def test_create_app_without_nacos_watcher():
    app = create_app()

    assert app.title == "Cockpit Agent"
