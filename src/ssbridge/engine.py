"""Движок синхронизации SmartShell → умный дом.

Отказоустойчивость:
* каждый цикл изолирован, любые исключения логируются и не роняют программу;
* если SmartShell недоступен — устройства НЕ переключаются (состояние удерживается);
* «предохранитель» для каждой системы умного дома: при сбоях опрос
  откладывается с нарастающей паузой (15 с → 5 мин), остальные системы работают;
* повтор команд с ограничением попыток, контроль, что устройство действительно
  переключилось (режим «поддерживать состояние»);
* сторожевой поток перезапускает зависший цикл;
* ограничение частоты запросов к SmartShell (не более 20/мин по документации).
"""
from __future__ import annotations

import json
import socket
import threading
import time
from typing import Callable

from . import connectors, journal
from .config import Config
from .net import AuthError, BridgeError, describe
from .smartshell import Host, SmartShell


class ConnectorState:
    def __init__(self, cid: str):
        self.cid = cid
        self.ok: bool | None = None
        self.message = "ещё не проверялось"
        self.fail_count = 0
        self.retry_at = 0.0
        self.last_ok = 0.0
        self.problem = journal.Problem(cid, "devices")

    def to_dict(self) -> dict:
        return {"ok": self.ok, "message": self.message, "fail_count": self.fail_count,
                "retry_in": max(0, int(self.retry_at - time.time())), "last_ok": self.last_ok}


class BindingState:
    def __init__(self):
        self.desired: bool | None = None
        self.actual: bool | None = None
        self.raw: bool | None = None
        self.off_since: float | None = None
        self.last_cmd: bool | None = None
        self.last_cmd_ts = 0.0
        self.attempts = 0
        self.hold_until = 0.0
        self.error = ""
        self.last_action = ""
        self.last_action_ts = 0.0
        self.problem: journal.Problem | None = None

    def to_dict(self) -> dict:
        return {
            "desired": self.desired, "actual": self.actual, "session": self.raw,
            "off_since": self.off_since,
            "error": self.error, "last_action": self.last_action, "last_action_ts": self.last_action_ts,
            "hold_in": max(0, int(self.hold_until - time.time())),
        }


class Engine:
    def __init__(self, config: Config, notifier=None,
                 smartshell_factory: Callable[..., SmartShell] | None = None,
                 connector_factory: Callable[[dict], connectors.Connector] | None = None):
        self.config = config
        self.notifier = notifier
        self._ss_factory = smartshell_factory or SmartShell
        self._conn_factory = connector_factory or connectors.create
        self.ss: SmartShell | None = None
        self._ss_sig = ""
        self.conns: dict[str, connectors.Connector] = {}
        self._conn_sig: dict[str, str] = {}
        self.cstate: dict[str, ConnectorState] = {}
        self.bstate: dict[str, BindingState] = {}
        self.hosts: dict[int, Host] = {}
        self.groups: list[dict] = []
        self.hosts_ts = 0.0
        self.ss_ok: bool | None = None
        self.ss_message = "ещё не проверялось"
        self.ss_problem = journal.Problem("SmartShell", "smartshell", self._on_problem)
        self.paused = False
        self.started = time.time()
        self.cycles = 0
        self.last_cycle = 0.0
        self.last_cycle_ms = 0
        self.heartbeat = time.time()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._gen = 0
        self._cycle_lock = threading.Lock()
        self._keepalive_ts: dict[int, float] = {}
        self._vh_problem: dict[int, journal.Problem] = {}
        self._first = True
        self._listeners: list[Callable[[], None]] = []

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> None:
        self._spawn_loop()
        threading.Thread(target=self._watchdog, name="watchdog", daemon=True).start()
        journal.info("Синхронизация запущена", "engine")

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        for c in self.conns.values():
            c.close()

    def _spawn_loop(self) -> None:
        self._gen += 1
        threading.Thread(target=self._loop, args=(self._gen,), name=f"engine-{self._gen}", daemon=True).start()

    def _loop(self, gen: int) -> None:
        while not self._stop.is_set() and gen == self._gen:
            self.heartbeat = time.time()
            if not self.paused:
                try:
                    self.run_cycle()
                except Exception as e:  # последняя линия обороны
                    journal.error(f"Непредвиденная ошибка цикла: {describe(e)}", "engine", exc=True)
            interval = max(5, int(self.config.get("general", "poll_interval", 10) or 10))
            self._wake.wait(interval)
            self._wake.clear()

    def _watchdog(self) -> None:
        while not self._stop.is_set():
            time.sleep(15)
            interval = max(5, int(self.config.get("general", "poll_interval", 10) or 10))
            limit = max(180, interval * 6)
            if time.time() - self.heartbeat > limit:
                journal.error(f"Цикл синхронизации не отвечает более {limit} с — перезапуск", "engine")
                self.heartbeat = time.time()
                self._spawn_loop()

    def run_now(self) -> None:
        self._wake.set()

    def set_paused(self, paused: bool) -> None:
        self.paused = paused
        journal.warning("Синхронизация приостановлена" if paused else "Синхронизация возобновлена", "engine")
        self._notify_listeners()
        if not paused:
            self.run_now()

    def add_listener(self, fn: Callable[[], None]) -> None:
        self._listeners.append(fn)

    def _notify_listeners(self) -> None:
        for fn in self._listeners:
            try:
                fn()
            except Exception:
                pass

    def _on_problem(self, key: str, active: bool, message: str) -> None:
        if not self.notifier:
            return
        if active:
            self.notifier.error(message, key)
        else:
            self.notifier.recovered(f"{key}: работа восстановлена")

    # ------------------------------------------------------------------ config sync
    def _sync_config(self) -> None:
        ss_conf = self.config.get("smartshell")
        gen = self.config.get("general")
        sig = json.dumps([ss_conf.get("login"), ss_conf.get("password"), ss_conf.get("company_id"), ss_conf.get("user_agent")])
        if sig != self._ss_sig:
            self._ss_sig = sig
            self.ss = self._ss_factory(ss_conf.get("login", ""), ss_conf.get("password", ""), ss_conf.get("company_id", ""),
                                       ss_conf.get("user_agent", ""), int(gen.get("max_billing_rpm") or 15))
            self.hosts = {}
        elif self.ss is not None:
            self.ss.limiter.set_limit(min(19, int(gen.get("max_billing_rpm") or 15)))

        wanted = {c["id"]: c for c in self.config.connectors() if c.get("enabled", True)}
        for cid in list(self.conns):
            if cid not in wanted:
                self.conns.pop(cid).close()
                self._conn_sig.pop(cid, None)
        for cid, conf in wanted.items():
            sig = json.dumps(conf, sort_keys=True, ensure_ascii=False)
            if self._conn_sig.get(cid) != sig:
                if cid in self.conns:
                    self.conns[cid].close()
                try:
                    self.conns[cid] = self._conn_factory(conf)
                    self._conn_sig[cid] = sig
                    st = self.cstate.setdefault(cid, ConnectorState(cid))
                    st.problem.key = conf.get("name") or cid
                    st.problem.on_change = self._on_problem
                    st.retry_at = 0
                except Exception as e:
                    journal.error(f"Не удалось создать подключение «{conf.get('name')}»: {describe(e)}", "devices")

    def connector(self, cid: str) -> connectors.Connector:
        self._sync_config()
        conn = self.conns.get(cid)
        if conn is None:
            conf = self.config.connector(cid)
            if not conf:
                raise BridgeError("система умного дома не найдена")
            conn = self._conn_factory(conf)  # выключенная — создаём временно для теста
        return conn

    def smartshell(self) -> SmartShell:
        self._sync_config()
        return self.ss

    # ------------------------------------------------------------------ cycle
    def refresh_hosts(self) -> None:
        if not self.ss or not self.ss.configured:
            self.ss_ok = None
            self.ss_message = "не настроено"
            raise AuthError("SmartShell не настроен")
        hosts, groups = self.ss.hosts()
        self.hosts = {h.id: h for h in hosts}
        self.groups = groups
        self.hosts_ts = time.time()

    def run_cycle(self) -> None:
        if not self._cycle_lock.acquire(timeout=1):
            return
        t0 = time.time()
        try:
            self._sync_config()
            bindings = [b for b in self.config.bindings() if b.get("enabled", True)]

            # 1. SmartShell
            try:
                self.refresh_hosts()
                self.ss_ok = True
                self.ss_message = f"OK, хостов: {len(self.hosts)}, активных сеансов: {sum(1 for h in self.hosts.values() if h.active)}"
                self.ss_problem.ok("SmartShell: связь восстановлена")
            except AuthError as e:
                self.ss_ok = False if self.ss and self.ss.configured else None
                self.ss_message = describe(e)
                if self.ss_ok is False:
                    self.ss_problem.fail(f"SmartShell: {describe(e)}")
                return
            except Exception as e:
                self.ss_ok = False
                self.ss_message = describe(e)
                self.ss_problem.fail(f"SmartShell недоступен: {describe(e)}. Устройства не переключаются до восстановления связи")
                return

            # 2. Виртуальные хосты (приставки без шелла)
            self._keepalive()

            # 3. Состояния устройств
            by_conn: dict[str, list[dict]] = {}
            for b in bindings:
                by_conn.setdefault(b.get("connector_id", ""), []).append(b)
            states: dict[str, dict[str, bool | None]] = {}
            for cid, items in by_conn.items():
                states[cid] = self._poll_connector(cid, [b.get("device_id", "") for b in items])

            # 4. Применение
            seen = set()
            for b in bindings:
                seen.add(b["id"])
                try:
                    self._apply(b, states.get(b.get("connector_id", "")))
                except Exception as e:
                    journal.error(f"Ошибка обработки привязки {b.get('host_alias')}: {describe(e)}", "engine", exc=True)
            for bid in list(self.bstate):
                if bid not in seen:
                    self.bstate.pop(bid, None)
            self._first = False
        finally:
            self.cycles += 1
            self.last_cycle = time.time()
            self.last_cycle_ms = int((time.time() - t0) * 1000)
            self._cycle_lock.release()
            self._notify_listeners()

    def _poll_connector(self, cid: str, device_ids: list[str]) -> dict[str, bool | None] | None:
        conn = self.conns.get(cid)
        st = self.cstate.setdefault(cid, ConnectorState(cid))
        if conn is None:
            st.ok = False
            st.message = "система отключена или не найдена"
            return None
        if time.time() < st.retry_at:
            return None
        try:
            with conn.lock:
                res = conn.get_states(device_ids)
            st.ok = True
            st.message = "OK"
            st.fail_count = 0
            st.last_ok = time.time()
            st.problem.ok(f"{conn.name}: связь восстановлена")
            return res
        except Exception as e:
            st.ok = False
            st.fail_count += 1
            delay = min(300, 15 * (2 ** min(st.fail_count - 1, 5)))
            st.retry_at = time.time() + delay
            st.message = describe(e)
            st.problem.fail(f"{conn.name}: {describe(e)} (повтор через {delay} с)")
            return None

    def _resolve_host(self, b: dict) -> Host | None:
        h = self.hosts.get(int(b.get("host_id") or 0)) if str(b.get("host_id") or "").isdigit() else None
        if h:
            return h
        alias = (b.get("host_alias") or "").strip().lower()
        return next((x for x in self.hosts.values() if x.alias.strip().lower() == alias), None) if alias else None

    def _apply(self, b: dict, states: dict | None) -> None:
        bs = self.bstate.setdefault(b["id"], BindingState())
        label = f"{b.get('host_alias') or b.get('host_id')} → {b.get('device_name') or b.get('device_id')}"
        if bs.problem is None:
            bs.problem = journal.Problem(label, "devices", self._on_problem)
        host = self._resolve_host(b)
        if host is None:
            bs.error = "хост не найден в SmartShell"
            bs.problem.fail(f"{label}: хост «{b.get('host_alias')}» не найден на карте клуба", "WARNING")
            return

        now = time.time()
        raw = host.active or (bool(b.get("on_in_service")) and host.in_service)
        if b.get("invert"):
            raw = not raw
        bs.raw = host.active

        # задержка выключения
        delay = int(b.get("off_delay") or 0)
        if raw:
            bs.off_since = None
            desired = True
        elif delay > 0 and bs.desired and not self._first:
            if bs.off_since is None:
                bs.off_since = now
                journal.info(f"{label}: сеанс завершён, выключение через {delay} с", "devices")
            desired = now - bs.off_since < delay
            if not desired:
                bs.off_since = None
        else:
            bs.off_since = None
            desired = False

        changed = desired != bs.desired
        bs.desired = desired
        actual = states.get(b.get("device_id")) if states is not None else None
        bs.actual = actual

        if states is None:
            bs.error = "система умного дома недоступна"
            return
        if now < bs.hold_until:
            bs.error = ""
            return

        enforce = bool(self.config.get("general", "enforce_state", True))
        need = False
        if changed or bs.last_cmd is None:
            need = actual is None or actual != desired
            if actual is None and not changed and bs.last_cmd == desired:
                need = False
            if changed:
                bs.attempts = 0
        elif actual is not None and actual != desired and enforce:
            # устройство в другом состоянии: даём время на отклик после команды
            backoff = min(300, 20 * (2 ** min(bs.attempts, 4)))
            need = now - bs.last_cmd_ts >= backoff
        elif actual is None and bs.last_cmd != desired:
            need = True

        if not need:
            if actual == desired:
                if bs.last_cmd is None:
                    bs.last_cmd = desired
                bs.attempts = 0
                bs.error = ""
                bs.problem.ok(f"{label}: устройство в нужном состоянии")
            return

        word = "включение" if desired else "выключение"
        reason = "начался сеанс" if desired and host.active else ("сервисный режим" if desired else "сеанс завершён")
        if not changed and bs.last_cmd is not None:
            reason = "устройство было переключено вручную или не выполнило команду"
        if self.config.get("general", "dry_run", False):
            if changed or bs.last_cmd != desired:
                journal.info(f"[тестовый режим] {label}: {word} ({reason}) — команда не отправлена", "devices")
            bs.last_cmd, bs.last_cmd_ts = desired, now
            return
        self.command(b, desired, reason=reason, label=label)

    def command(self, b: dict, on: bool, reason: str = "", label: str | None = None, manual: bool = False) -> None:
        bs = self.bstate.setdefault(b["id"], BindingState())
        label = label or f"{b.get('host_alias')} → {b.get('device_name') or b.get('device_id')}"
        if bs.problem is None:
            bs.problem = journal.Problem(label, "devices", self._on_problem)
        conn = self.connector(b.get("connector_id", ""))
        word = "включено" if on else "выключено"
        bs.last_cmd, bs.last_cmd_ts = on, time.time()
        bs.attempts += 1
        last_exc = None
        for attempt in range(2):
            try:
                with conn.lock:
                    conn.set_state(b.get("device_id", ""), on)
                bs.error = ""
                bs.last_action = f"{word}{' вручную' if manual else ''}"
                bs.last_action_ts = time.time()
                journal.success(f"{label}: {word}{(' — ' + reason) if reason else ''}", "devices")
                if self.notifier and not manual:
                    self.notifier.switched(f"{label}: {word} ({reason})")
                if manual:
                    bs.hold_until = time.time() + 300
                bs.problem.ok()
                return
            except Exception as e:
                last_exc = e
                if attempt == 0:
                    time.sleep(1.5)
        bs.error = describe(last_exc)
        bs.problem.fail(f"{label}: не удалось — {describe(last_exc)} (попытка {bs.attempts})")
        if manual:
            raise BridgeError(describe(last_exc))

    def _keepalive(self) -> None:
        vhs = self.config.virtual_hosts()
        if not vhs or not self.ss:
            return
        interval = max(15, int(self.config.get("general", "keepalive_interval", 30) or 30))
        now = time.time()
        for vh in vhs:
            hid = vh.get("host_id")
            if now - self._keepalive_ts.get(hid, 0) < interval:
                continue
            self._keepalive_ts[hid] = now
            prob = self._vh_problem.setdefault(hid, journal.Problem(f"Хост {vh.get('alias')}", "smartshell", self._on_problem))
            if hid not in self.hosts:
                prob.fail(f"Виртуальный хост «{vh.get('alias')}» удалён с карты клуба. Удалите его в разделе «SmartShell» → «Хосты для приставок» или создайте заново", "WARNING")
                continue
            try:
                self.ss.host_keepalive(vh.get("token", ""))
                prob.ok(f"Виртуальный хост «{vh.get('alias')}» снова в сети")
            except Exception as e:
                prob.fail(f"Виртуальный хост «{vh.get('alias')}»: {describe(e)}", "WARNING")

    # ------------------------------------------------------------------ status
    def overall(self) -> tuple[str, str]:
        """(уровень, текст) для трея и шапки: ok | warn | error | paused | setup."""
        if self.paused:
            return "paused", "Синхронизация на паузе"
        if not self.config.get("smartshell", "login") or not self.config.connectors():
            return "setup", "Требуется настройка"
        if self.ss_ok is False:
            return "error", f"SmartShell: {self.ss_message}"
        bad = [self.config.connector(cid) for cid, s in self.cstate.items() if s.ok is False and cid in self.conns]
        if bad:
            return "error", "Нет связи: " + ", ".join((c or {}).get("name", "?") for c in bad)
        errs = [b for b in self.bstate.values() if b.error]
        if errs:
            return "warn", f"Проблемы с устройствами: {len(errs)}"
        if self.ss_ok is None:
            return "warn", "Запуск..."
        return "ok", "Всё работает"

    def status(self) -> dict:
        level, text = self.overall()
        bindings = []
        for b in self.config.bindings():
            host = self._resolve_host(b)
            bs = self.bstate.get(b["id"])
            cs = self.cstate.get(b.get("connector_id", ""))
            bindings.append({**b, "host": host.to_dict() if host else None, "state": bs.to_dict() if bs else None,
                             "connector_ok": cs.ok if cs else None})
        return {
            "level": level, "text": text, "paused": self.paused,
            "dry_run": bool(self.config.get("general", "dry_run", False)),
            "uptime": int(time.time() - self.started), "cycles": self.cycles,
            "last_cycle": self.last_cycle, "last_cycle_ms": self.last_cycle_ms,
            "smartshell": {"ok": self.ss_ok, "message": self.ss_message,
                           "club": self.config.get("smartshell", "club_name", ""),
                           "rpm_used": self.ss.limiter.used() if self.ss else 0,
                           "hosts": len(self.hosts), "active": sum(1 for h in self.hosts.values() if h.active)},
            "connectors": {cid: s.to_dict() for cid, s in self.cstate.items()},
            "bindings": bindings,
        }

    # ------------------------------------------------------------------ diagnostics
    def self_test(self) -> list[dict]:
        checks: list[dict] = []

        def run(name: str, fn):
            t = time.time()
            try:
                msg = fn() or "OK"
                checks.append({"name": name, "ok": True, "message": msg, "ms": int((time.time() - t) * 1000)})
            except Exception as e:
                checks.append({"name": name, "ok": False, "message": describe(e), "ms": int((time.time() - t) * 1000)})

        def internet():
            socket.create_connection(("billing.smartshell.gg", 443), timeout=5).close()
            return "billing.smartshell.gg доступен"

        def data_dir():
            from . import paths
            p = paths.data_dir() / ".write_test"
            p.write_text("ok")
            p.unlink()
            return str(paths.data_dir())

        run("Интернет и DNS", internet)
        run("Папка данных доступна для записи", data_dir)

        def ss_login():
            ss = self.smartshell()
            if not ss or not ss.configured:
                raise BridgeError("не заполнены логин, пароль или ID клуба")
            ss.invalidate()
            ss.ensure_token()
            return "вход выполнен"

        run("SmartShell: авторизация", ss_login)

        def ss_hosts():
            self.refresh_hosts()
            return f"хостов: {len(self.hosts)}, групп: {len(self.groups)}, активных сеансов: {sum(1 for h in self.hosts.values() if h.active)}"

        run("SmartShell: список хостов", ss_hosts)

        device_cache: dict[str, dict[str, str]] = {}
        for conf in self.config.connectors():
            def ctest(conf=conf):
                conn = self.connector(conf["id"])
                with conn.lock:
                    msg = conn.test()
                    try:
                        device_cache[conf["id"]] = {d.id: d.name for d in conn.list_devices()}
                    except Exception:
                        pass
                return msg
            run(f"{conf.get('name')}{'' if conf.get('enabled', True) else ' (отключено)'}", ctest)

        for b in self.config.bindings():
            def btest(b=b):
                if not self._resolve_host(b):
                    raise BridgeError(f"хост «{b.get('host_alias')}» не найден в SmartShell")
                devs = device_cache.get(b.get("connector_id"))
                if devs is None:
                    raise BridgeError("система умного дома недоступна")
                if b.get("device_id") not in devs:
                    raise BridgeError("устройство не найдено в системе умного дома")
                return "хост и устройство найдены" + ("" if b.get("enabled", True) else " (привязка отключена)")
            run(f"Привязка: {b.get('host_alias')} → {b.get('device_name') or b.get('device_id')}", btest)

        ok = sum(1 for c in checks if c["ok"])
        level = journal.success if ok == len(checks) else journal.warning
        level(f"Диагностика: пройдено {ok} из {len(checks)} проверок", "diag")
        for c in checks:
            if not c["ok"]:
                journal.warning(f"Диагностика — {c['name']}: {c['message']}", "diag")
        return checks
