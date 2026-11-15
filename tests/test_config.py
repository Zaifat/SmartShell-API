import json

from ssbridge import secrets
from ssbridge.config import MASK, Config, mask_tree, unmask_tree


def test_secret_roundtrip():
    enc = secrets.encrypt("пароль-123")
    assert enc != "пароль-123"
    assert secrets.is_encrypted(enc)
    assert secrets.decrypt(enc) == "пароль-123"
    assert secrets.decrypt("plain") == "plain"
    assert secrets.encrypt("") == ""


def test_config_encrypts_on_disk(tmp_config):
    tmp_config.update("smartshell", {"login": "7900", "password": "secret-pass"})
    raw = json.loads(tmp_config.path.read_text(encoding="utf-8"))
    assert raw["smartshell"]["login"] == "7900"
    assert raw["smartshell"]["password"] != "secret-pass"
    again = Config(tmp_config.path)
    assert again.get("smartshell", "password") == "secret-pass"


def test_corrupted_config_uses_backup(tmp_config):
    tmp_config.update("smartshell", {"login": "first"})
    tmp_config.update("smartshell", {"login": "second"})  # бэкап содержит "first"
    tmp_config.path.write_text("{broken", encoding="utf-8")
    cfg = Config(tmp_config.path)
    assert cfg.get("smartshell", "login") == "first"
    assert cfg.load_error


def test_mask_unmask():
    old = {"token": "abc", "url": "http://x", "devices": [{"name": "a", "password": "p"}]}
    masked = mask_tree(old)
    assert masked["token"] == MASK and masked["url"] == "http://x"
    assert masked["devices"][0]["password"] == MASK
    masked["url"] = "http://y"
    restored = unmask_tree(masked, old)
    assert restored == {"token": "abc", "url": "http://y", "devices": [{"name": "a", "password": "p"}]}


def test_connector_upsert_keeps_secret(tmp_config):
    c = tmp_config.upsert_connector({"type": "yandex", "name": "Я", "settings": {"token": "t1"}})
    tmp_config.upsert_connector({"id": c["id"], "type": "yandex", "name": "Я2", "settings": {"token": MASK}})
    assert tmp_config.connector(c["id"])["settings"]["token"] == "t1"
    assert tmp_config.connector(c["id"])["name"] == "Я2"
    tmp_config.set_bindings([{"connector_id": c["id"], "device_id": "d", "host_id": 1}])
    tmp_config.delete_connector(c["id"])
    assert tmp_config.bindings() == []
