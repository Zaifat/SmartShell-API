"""Движок синхронизации SmartShell → умный дом.

Отказоустойчивость:
* каждый цикл изолирован, любые исключения логируются и не роняют программу;
* если SmartShell недоступен — устройства НЕ переключаются (состояние удерживается);
* «предохранитель» для каждой системы умного дома: при сбоях опрос
  откладывается с нарастающей паузой (15 с → 5 мин), остальные системы работают;
* повтор команд с ограничением попыток, контроль, что устройство действительно
  переключилось (режим «поддерживать состояние»);
* сторожевой поток перезапускает зависший цикл;
* ограничение частоты запросов к SmartShell (не более 20/мин по документации);
* несколько клубов SmartShell: у каждого своё подключение и свой лимит запросов,
  сбой одного клуба не влияет на привязки других.
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


class ClubState:
    """Состояние одного клуба (аккаунта) SmartShell."""

    def __init__(self, kid: str, on_problem):
        self.id = kid
        self.name = ""
        self.company_id = ""
        self.ss: SmartShell | None = None
        self.sig = ""
        self.hosts: dict[int, Host] = {}
        self.groups: list[dict] = []
        self.hosts_ts = 0.0
        self.ok: bool | None = None
        self.message = "ещё не проверялось"
        self.problem = journal.Problem("SmartShell", "smartshell", on_problem)
        self.keepalive_ts: dict[int, float] = {}
        self.vh_problem: dict[int, journal.Problem] = {}

    @property
    def active(self) -> int:
        return sum(1 for h in self.hosts.values() if h.active)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "company_id": self.company_id, "ok": self.ok,
                "message": self.message, "hosts": len(self.hosts), "active": self.active,
                "rpm_used": self.ss.limiter.used() if self.ss else 0}


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
        self.clubs: dict[str, ClubState] = {}
        self.conns: dict[str, connectors.Connector] = {}
        self._conn_sig: dict[str, str] = {}
        self.cstate: dict[str, ConnectorState] = {}
        self.bstate: dict[str, BindingState] = {}
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
        gen = self.config.get("general")
        rpm = int(gen.get("max_billing_rpm") or 15)
        clubs = {c["id"]: c for c in self.config.clubs() if c.get("enabled", True)}
        for kid in list(self.clubs):
            if kid not in clubs:
                self.clubs.pop(kid)
        for kid, c in clubs.items():
            st = self.clubs.get(kid)
            if st is None:
                st = self.clubs[kid] = ClubState(kid, self._on_problem)
            st.name = c.get("name") or f"Клуб {c.get('company_id', '')}"
            st.company_id = str(c.get("company_id", ""))
            st.problem.key = "SmartShell" if len(clubs) == 1 else f"SmartShell «{st.name}»"
            sig = json.dumps([c.get("login"), c.get("password"), c.get("company_id"), c.get("user_agent")])
            if sig != st.sig:
                st.sig = sig
                st.ss = self._ss_factory(c.get("login", ""), c.get("password", ""), c.get("company_id", ""),
                                         c.get("user_agent", ""), rpm)
                st.hosts, st.groups, st.hosts_ts = {}, [], 0.0
            elif st.ss is not None:
                st.ss.limiter.set_limit(min(19, rpm))

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

    def club(self, kid: str | None = None) -> ClubState:
        """Клуб по id (без id — единственный/первый клуб)."""
        self._sync_config()
        if kid:
            st = self.clubs.get(kid)
            if st is None:
                raise BridgeError("клуб не найден или отключён")
            return st
        if not self.clubs:
            raise AuthError("SmartShell не настроен — добавьте клуб")
        return next(iter(self.clubs.values()))

    def smartshell(self, kid: str | None = None) -> SmartShell:
        return self.club(kid).ss

    def club_for(self, b: dict) -> ClubState | None:
        kid = b.get("club_id")
        if kid:
            return self.clubs.get(kid)
        return next(iter(self.clubs.values())) if len(self.clubs) == 1 else None

    @property
    def hosts(self) -> dict[int, Host]:
        """Все хосты всех клубов (для статистики)."""
        out: dict[int, Host] = {}
        for st in self.clubs.values():
            out.update(st.hosts)
        return out

    # ------------------------------------------------------------------ cycle
    def refresh_club(self, st: ClubState) -> None:
        if not st.ss or not st.ss.configured:
            st.ok = None
            st.message = "не настроено"
            raise AuthError("SmartShell не настроен")
        hosts, groups = st.ss.hosts()
        st.hosts = {h.id: h for h in hosts}
        st.groups = groups
        st.hosts_ts = time.time()

    def refresh_hosts(self, kid: str | None = None) -> None:
        """Обновить хосты одного клуба (или всех)."""
        if kid:
            self.refresh_club(self.club(kid))
            return
        self._sync_config()
        if not self.clubs:
            raise AuthError("SmartShell не настроен — добавьте клуб")
        for st in self.clubs.values():
            self.refresh_club(st)

    def _check_club(self, st: ClubState) -> bool:
        try:
            self.refresh_club(st)
            st.ok = True
            st.message = f"OK, хостов: {len(st.hosts)}, активных сеансов: {st.active}"
            st.problem.ok(f"{st.problem.key}: связь восстановлена")
            return True
        except AuthError as e:
            st.ok = False if st.ss and st.ss.configured else None
            st.message = describe(e)
            if st.ok is False:
                st.problem.fail(f"{st.problem.key}: {describe(e)}")
        except Exception as e:
            st.ok = False
            st.message = describe(e)
            st.problem.fail(f"{st.problem.key} недоступен: {describe(e)}. Устройства этого клуба не переключаются до восстановления связи")
        return False

    def run_cycle(self) -> None:
        if not self._cycle_lock.acquire(timeout=1):
            return
        t0 = time.time()
        try:
            self._sync_config()
            bindings = [b for b in self.config.bindings() if b.get("enabled", True)]

            all_ids = {b["id"] for b in self.config.bindings()}

            # 1. SmartShell — каждый клуб отдельно; если клуб недоступен,
            #    его устройства не переключаются (состояние удерживается)
            ok_clubs = set()
            for st in list(self.clubs.values()):
                if self._check_club(st):
                    ok_clubs.add(st.id)
                    # 2. Виртуальные хосты (приставки без шелла)
                    self._keepalive(st)
            held = [b for b in bindings if (self.club_for(b) is not None and self.club_for(b).id not in ok_clubs)]
            for b in held:
                bs = self.bstate.setdefault(b["id"], BindingState())
                bs.error = ""  # причина видна в статусе клуба
            bindings = [b for b in bindings if (c := self.club_for(b)) is None or c.id in ok_clubs]
            if not bindings:
                for bid in list(self.bstate):
                    if bid not in all_ids:
                        self.bstate.pop(bid, None)
                return

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
                if bid not in all_ids:
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
        st = self.club_for(b)
        if st is None:
            return None
        h = st.hosts.get(int(b.get("host_id") or 0)) if str(b.get("host_id") or "").isdigit() else None
        if h:
            return h
        alias = (b.get("host_alias") or "").strip().lower()
        return next((x for x in st.hosts.values() if x.alias.strip().lower() == alias), None) if alias else None

    def _apply(self, b: dict, states: dict | None) -> None:
        bs = self.bstate.setdefault(b["id"], BindingState())
        label = f"{b.get('host_alias') or b.get('host_id')} → {b.get('device_name') or b.get('device_id')}"
        if bs.problem is None:
            bs.problem = journal.Problem(label, "devices", self._on_problem)
        host = self._resolve_host(b)
        if host is None:
            if self.club_for(b) is None:
                bs.error = "клуб SmartShell удалён или отключён"
                bs.problem.fail(f"{label}: клуб SmartShell этой привязки удалён или отключён", "WARNING")
            else:
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

    def _keepalive(self, st: ClubState) -> None:
        single = len(self.clubs) == 1
        vhs = [v for v in self.config.virtual_hosts() if v.get("club_id") == st.id or (not v.get("club_id") and single)]
        if not vhs or not st.ss:
            return
        interval = max(15, int(self.config.get("general", "keepalive_interval", 30) or 30))
        now = time.time()
        for vh in vhs:
            hid = vh.get("host_id")
            if now - st.keepalive_ts.get(hid, 0) < interval:
                continue
            st.keepalive_ts[hid] = now
            prob = st.vh_problem.setdefault(hid, journal.Problem(f"Хост {vh.get('alias')}", "smartshell", self._on_problem))
            if hid not in st.hosts:
                prob.fail(f"Виртуальный хост «{vh.get('alias')}» удалён с карты клуба. Удалите его в разделе «SmartShell» → «Хосты для приставок» или создайте заново", "WARNING")
                continue
            try:
                st.ss.host_keepalive(vh.get("token", ""))
                prob.ok(f"Виртуальный хост «{vh.get('alias')}» снова в сети")
            except Exception as e:
                prob.fail(f"Виртуальный хост «{vh.get('alias')}»: {describe(e)}", "WARNING")

    # ------------------------------------------------------------------ status
    def overall(self) -> tuple[str, str]:
        """(уровень, текст) для трея и шапки: ok | warn | error | paused | setup."""
        if self.paused:
            return "paused", "Синхронизация на паузе"
        if not self.config.clubs() or not self.config.connectors():
            return "setup", "Требуется настройка"
        bad_clubs = [st for st in self.clubs.values() if st.ok is False]
        if bad_clubs:
            if len(self.clubs) == 1:
                return "error", f"SmartShell: {bad_clubs[0].message}"
            if len(bad_clubs) == 1:
                return "error", f"SmartShell «{bad_clubs[0].name}»: {bad_clubs[0].message}"
            return "error", "SmartShell недоступен: " + ", ".join(st.name for st in bad_clubs)
        bad = [self.config.connector(cid) for cid, s in self.cstate.items() if s.ok is False and cid in self.conns]
        if bad:
            return "error", "Нет связи: " + ", ".join((c or {}).get("name", "?") for c in bad)
        errs = [b for b in self.bstate.values() if b.error]
        if errs:
            return "warn", f"Проблемы с устройствами: {len(errs)}"
        if not self.clubs or any(st.ok is None for st in self.clubs.values()):
            return "warn", "Запуск..."
        return "ok", "Всё работает"

    def status(self) -> dict:
        level, text = self.overall()
        bindings = []
        for b in self.config.bindings():
            host = self._resolve_host(b)
            bs = self.bstate.get(b["id"])
            cs = self.cstate.get(b.get("connector_id", ""))
            club = self.club_for(b)
            bindings.append({**b, "host": host.to_dict() if host else None, "state": bs.to_dict() if bs else None,
                             "connector_ok": cs.ok if cs else None, "club_name": club.name if club else "",
                             "club_ok": club.ok if club else False})
        clubs = [st.to_dict() for st in self.clubs.values()]
        oks = [c["ok"] for c in clubs]
        ss_ok = None if not clubs else (False if False in oks else (True if all(oks) else None))
        if len(clubs) == 1:
            ss_msg = clubs[0]["message"]
        elif clubs:
            ss_msg = f"клубов: {len(clubs)}, на связи: {sum(1 for o in oks if o)}"
        else:
            ss_msg = "клуб не добавлен"
        return {
            "level": level, "text": text, "paused": self.paused,
            "dry_run": bool(self.config.get("general", "dry_run", False)),
            "uptime": int(time.time() - self.started), "cycles": self.cycles,
            "last_cycle": self.last_cycle, "last_cycle_ms": self.last_cycle_ms,
            "smartshell": {"ok": ss_ok, "message": ss_msg,
                           "club": ", ".join(c["name"] for c in clubs),
                           "rpm_used": max([c["rpm_used"] for c in clubs] or [0]),
                           "hosts": sum(c["hosts"] for c in clubs), "active": sum(c["active"] for c in clubs)},
            "clubs": clubs,
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

        self._sync_config()
        if not self.clubs:
            def no_club():
                raise BridgeError("не добавлен ни один клуб — откройте раздел «SmartShell»")
            run("SmartShell: клуб", no_club)
        for st in list(self.clubs.values()):
            prefix = "SmartShell" if len(self.clubs) == 1 else f"SmartShell «{st.name}»"

            def ss_login(st=st):
                if not st.ss or not st.ss.configured:
                    raise BridgeError("не заполнены логин, пароль или ID клуба")
                st.ss.invalidate()
                st.ss.ensure_token()
                return "вход выполнен"

            def ss_hosts(st=st):
                self.refresh_club(st)
                return f"хостов: {len(st.hosts)}, групп: {len(st.groups)}, активных сеансов: {st.active}"

            run(f"{prefix}: авторизация", ss_login)
            run(f"{prefix}: список хостов", ss_hosts)

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
                if self.club_for(b) is None:
                    raise BridgeError("клуб SmartShell этой привязки удалён или отключён")
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
