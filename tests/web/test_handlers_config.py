from __future__ import annotations


def test_get_config_returns_expected_keys(client):
    data = client.get_json("/api/config")
    for key in ("library_root", "rclone_remote", "web_host", "web_port"):
        assert key in data


def test_get_auth_status_no_pin(client):
    data = client.get_json("/api/auth/status")
    assert data == {"pin_configured": False}


def test_post_config_updates_library_root(client, tmp_path):
    new_root = str(tmp_path / "new_library")
    resp = client.post_json("/api/config", {"library.library_root": new_root})
    assert resp["saved"] == ["library.library_root"]

    data = client.get_json("/api/config")
    assert data["library_root"] == new_root


def test_post_config_rejects_unknown_fields(client):
    resp = client.post_json("/api/config", {"not_a_real_field": "x"})
    assert "error" in resp
