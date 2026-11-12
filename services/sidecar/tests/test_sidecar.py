from cip_sidecar.main import PORTS, build_apps, configure_environment


def test_environment_points_every_service_at_the_shared_data_dir():
    environment = configure_environment({"CIP_DATA_DIR": "/data", "CIP_EXPORTS_DIR": "/docs/Asistente"})

    assert environment["CIP_LIBRARY_DATA_DIR"] == "/data/library"
    assert environment["CIP_GATEWAY_DATA_DIR"] == "/data/gateway"
    assert environment["CIP_GATEWAY_EXPORTS_DIR"] == "/docs/Asistente"
    assert environment["CIP_AGENTS_LIBRARY_URL"] == f"http://127.0.0.1:{PORTS['library']}"


def test_explicit_settings_win_over_defaults():
    environment = configure_environment({"CIP_DATA_DIR": "/data", "CIP_LIBRARY_DATA_DIR": "/custom"})

    assert environment["CIP_LIBRARY_DATA_DIR"] == "/custom"


def test_all_services_can_be_built_in_one_process(tmp_path, monkeypatch):
    for key, value in configure_environment({"CIP_DATA_DIR": str(tmp_path)}).items():
        monkeypatch.setenv(key, value)

    apps = build_apps()

    assert set(apps) == set(PORTS)
