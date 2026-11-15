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
    tmp_config.upsert_club({"login": "7900", "password": "secret-pass", "company_id": "5"})
    raw = json.loads(tmp_config.path.read_text(encoding="utf-8"))
    assert raw["clubs"][0]["login"] == "7900"
    assert raw["clubs"][0]["password"] != "secret-pass"
    again = Config(tmp_config.path)
    assert again.clubs()[0]["password"] == "secret-pass"


def test_corrupted_config_uses_backup(tmp_config):
    tmp_config.update("notify", {"telegram_chat_id": "first"})
    tmp_config.update("notify", {"telegram_chat_id": "second"})  # бэкап содержит "first"
    tmp_config.path.write_text("{broken", encoding="utf-8")
    cfg = Config(tmp_config.path)
    assert cfg.get("notify", "telegram_chat_id") == "first"
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


def test_migration_from_single_club(tmp_path):
    """Настройки версии 2 (один клуб в разделе smartshell) переносятся в список клубов."""
    p = tmp_path / "config.json"
    p.write_text(json.dumps({
        "version": 2,
        "smartshell": {"login": "7900", "password": secrets.encrypt("pw"), "company_id": "77", "club_name": "Клуб А — ул. Ленина, 1", "user_agent": ""},
        "bindings": [{"id": "b1", "host_id": 1, "host_alias": "PC1", "connector_id": "c", "device_id": "d"}],
        "virtual_hosts": [{"host_id": 5, "alias": "PS5", "token": secrets.encrypt("tok")}],
    }, ensure_ascii=False), encoding="utf-8")
    cfg = Config(p)
    clubs = cfg.clubs()
    assert len(clubs) == 1 and clubs[0]["name"] == "Клуб А" and clubs[0]["company_id"] == "77"
    assert clubs[0]["password"] == "pw"
    kid = clubs[0]["id"]
    assert cfg.bindings()[0]["club_id"] == kid
    assert cfg.virtual_hosts()[0]["club_id"] == kid and cfg.virtual_hosts()[0]["token"] == "tok"
    raw = json.loads(p.read_text(encoding="utf-8"))
    assert "smartshell" not in raw and raw["version"] == 3  # сохранено в новом формате
    assert raw["clubs"][0]["password"] != "pw"  # пароль по-прежнему зашифрован
    # повторная загрузка ничего не ломает
    again = Config(p)
    assert again.clubs()[0]["id"] == kid


def test_clubs_crud(tmp_config):
    import pytest
    from ssbridge.net import BridgeError
    a = tmp_config.upsert_club({"login": "l", "password": "p", "company_id": "1", "name": "А"})
    b = tmp_config.upsert_club({"login": "l", "password": "p", "company_id": "2"})
    assert b["name"] == "Клуб 2"
    with pytest.raises(BridgeError):
        tmp_config.upsert_club({"login": "l", "password": "p", "company_id": "1"})  # дубликат
    with pytest.raises(BridgeError):
        tmp_config.upsert_club({"login": "l", "password": "", "company_id": "3"})
    # пароль-маска не затирает сохранённый пароль
    tmp_config.upsert_club({"id": a["id"], "name": "А2", "password": MASK})
    assert tmp_config.club(a["id"])["password"] == "p" and tmp_config.club(a["id"])["name"] == "А2"
    tmp_config.add_binding({"club_id": a["id"], "host_id": 1, "connector_id": "c", "device_id": "d"})
    tmp_config.add_binding({"club_id": b["id"], "host_id": 1, "connector_id": "c", "device_id": "d"})
    assert len(tmp_config.bindings()) == 2  # одинаковый id хоста в разных клубах — разные привязки
    tmp_config.add_virtual_host(9, "PS", "t", b["id"])
    tmp_config.delete_club(b["id"])
    assert [x["club_id"] for x in tmp_config.bindings()] == [a["id"]]
    assert tmp_config.virtual_hosts() == []
