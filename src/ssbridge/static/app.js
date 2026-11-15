/* SmartShell Bridge — панель управления (без фреймворков, работает офлайн) */
"use strict";

// ---------------------------------------------------------------- icons
const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
  home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  monitor: '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  power: '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/>',
  play: '<path d="m6 4 14 8-14 8z"/>',
  pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.4L21 8"/><path d="M21 3v5h-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  wand: '<path d="m15 4 5 5L9 20H4v-5z"/><path d="M14 5l5 5"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  download: '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
  alert: '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
  bolt: '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
  send: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  eyeoff: '<path d="M17.9 17.9A10 10 0 0 1 12 19C5.5 19 2 12 2 12a18 18 0 0 1 4.1-5.1M9.9 5.2A9 9 0 0 1 12 5c6.5 0 10 7 10 7a18 18 0 0 1-2.2 3.2M14.1 14.1a3 3 0 1 1-4.2-4.2M2 2l20 20"/>',
  gamepad: '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 11v3M5.5 12.5h3M15 12h.01M18 13h.01"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
};
function icon(n) { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[n] || ""}</svg>`; }
function hydrateIcons(root = document) {
  root.querySelectorAll("i[data-i]").forEach(el => { el.innerHTML = icon(el.dataset.i); });
  // Секретные поля: символы скрыты через CSS, а не через type="password",
  // поэтому браузер не предлагает «сохранить пароль». Кнопка-глаз показывает текст.
  root.querySelectorAll("input[data-secret]:not([data-wrapped])").forEach(inp => {
    inp.dataset.wrapped = "1";
    const wrap = document.createElement("span");
    wrap.className = "secret-wrap";
    inp.parentNode.insertBefore(wrap, inp);
    wrap.appendChild(inp);
    const b = document.createElement("button");
    b.type = "button"; b.className = "reveal"; b.title = "Показать / скрыть"; b.tabIndex = -1;
    b.innerHTML = icon("eye");
    b.onclick = () => { inp.classList.toggle("shown"); b.innerHTML = icon(inp.classList.contains("shown") ? "eyeoff" : "eye"); };
    wrap.appendChild(b);
  });
}

const SYS_COLORS = { yandex: "#fc3f1d", homeassistant: "#18bcf2", tuya: "#ff4800", smartthings: "#15bfff", shelly: "#4a90d9", tasmota: "#1fa3ec",
  sonoff: "#2db8a8", mqtt: "#660066", openhab: "#e64a19", domoticz: "#3d7ab8", iobroker: "#3399cc", webhook: "#64748b" };
const SYS_LETTERS = { yandex: "Я", homeassistant: "HA", tuya: "T", smartthings: "ST", shelly: "S", tasmota: "Ta", sonoff: "So", mqtt: "MQ",
  openhab: "oH", domoticz: "Dz", iobroker: "io", webhook: "</>" };
const CATEGORIES = { cloud: "Облачные сервисы", local: "Устройства в локальной сети", universal: "Шлюзы и универсальные способы" };

// ---------------------------------------------------------------- helpers
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const S = { state: null, config: null, types: [], hosts: null, groups: [], devices: {}, logs: [], logAfter: 0, page: "dashboard",
  unseenErrors: 0, bindingsDraft: null, dirty: false, fails: 0, quitting: false };

async function api(path, body, method) {
  const opt = { method: method || (body !== undefined ? "POST" : "GET"), headers: { "X-SSB": "1" } };
  if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  let r;
  try { r = await fetch(path, opt); }
  catch (e) { throw new Error("Нет связи с программой. Убедитесь, что SmartShell Bridge запущен."); }
  const data = await r.json().catch(() => ({}));
  if (r.status === 401 && data.need_pin) { await askPin(); return api(path, body, method); }
  if (!r.ok) throw new Error(data.error || `Ошибка ${r.status}`);
  return data;
}

function toast(msg, kind = "") {
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.textContent = msg;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), kind === "err" ? 7000 : 3500);
}

async function busy(btn, fn) {
  if (btn) btn.classList.add("loading");
  try { return await fn(); }
  catch (e) { toast(e.message, "err"); throw e; }
  finally { if (btn) btn.classList.remove("loading"); }
}

function fmtTime(ts) { return ts ? new Date(ts * 1000).toLocaleTimeString("ru-RU") : "—"; }
function fmtDateTime(ts) { const d = new Date(ts * 1000); return d.toLocaleDateString("ru-RU") + " " + d.toLocaleTimeString("ru-RU"); }
function fmtDur(s) {
  s = Math.max(0, Math.floor(s));
  const d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
  if (d) return `${d} д ${h} ч`;
  if (h) return `${h} ч ${m} мин`;
  if (m) return `${m} мин ${s % 60} с`;
  return `${s} с`;
}
function mmss(s) { s = Math.max(0, Math.round(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; }
function sysIcon(type, size = 42) {
  return `<div class="sys-icon" style="background:${SYS_COLORS[type] || "#64748b"};width:${size}px;height:${size}px;font-size:${size > 36 ? 15 : 12}px">${esc(SYS_LETTERS[type] || "?")}</div>`;
}
function typeInfo(t) { return S.types.find(x => x.type === t) || { title: t, fields: [] }; }
function connName(cid) { return (S.config?.connectors || []).find(c => c.id === cid)?.name || "—"; }
function sw(id, checked, label, attrs = "") {
  return `<label class="switch"><input type="checkbox" ${id ? `id="${id}"` : ""} ${checked ? "checked" : ""} ${attrs}><span class="sl"></span>${label ? `<span>${label}</span>` : ""}</label>`;
}

// ---------------------------------------------------------------- modal
function modal({ title, body, foot = "", narrow = false, onClose }) {
  const root = $("#modal-root");
  const bg = document.createElement("div");
  bg.className = "modal-bg";
  bg.innerHTML = `<div class="modal ${narrow ? "narrow" : ""}"><div class="modal-head"><h2>${title}</h2><button class="btn ghost sm" data-close>${icon("x")}</button></div>
    <div class="modal-body">${body}</div>${foot ? `<div class="modal-foot">${foot}</div>` : ""}</div>`;
  root.appendChild(bg);
  const close = () => { bg.remove(); onClose && onClose(); };
  bg.addEventListener("mousedown", e => { if (e.target === bg) close(); });
  $("[data-close]", bg).onclick = close;
  hydrateIcons(bg);
  return { el: bg, close };
}

function confirmBox(text, okLabel = "Удалить") {
  return new Promise(res => {
    const m = modal({ title: "Подтверждение", narrow: true, body: `<p>${text}</p>`,
      foot: `<button class="btn" data-no>Отмена</button><button class="btn primary" data-yes>${okLabel}</button>`, onClose: () => res(false) });
    $("[data-no]", m.el).onclick = () => { m.el.remove(); res(false); };
    $("[data-yes]", m.el).onclick = () => { m.el.remove(); res(true); };
  });
}

let pinPromise = null;
function askPin() {
  if (pinPromise) return pinPromise;
  pinPromise = new Promise(res => {
    const m = modal({ title: "Вход в панель", narrow: true, body: `<p class="muted">Для доступа по сети введите PIN-код, заданный в настройках программы.</p>
      <label class="f"><span>PIN-код</span><input type="text" data-secret autocomplete="off" spellcheck="false" id="pin-in" autofocus></label><div id="pin-err"></div>`,
      foot: `<button class="btn primary" id="pin-ok">Войти</button>` });
    const go = async () => {
      const r = await fetch("/api/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pin: $("#pin-in").value }) });
      if (r.ok) { m.el.remove(); pinPromise = null; res(); }
      else $("#pin-err").innerHTML = `<div class="result err">Неверный PIN-код</div>`;
    };
    $("#pin-ok").onclick = go;
    $("#pin-in").onkeydown = e => { if (e.key === "Enter") go(); };
  });
  return pinPromise;
}

// ---------------------------------------------------------------- navigation
const PAGES = {};
function go(page) {
  if (S.page === "bindings" && page !== "bindings" && S.dirty && !confirm("Есть несохранённые изменения привязок. Уйти без сохранения?")) return;
  if (page !== "bindings") { S.dirty = false; S.bindingsDraft = null; }
  S.page = page;
  history.replaceState(null, "", "#" + page);  // без новых записей истории — окно можно закрыть из скрипта
  $$("#nav a").forEach(a => a.classList.toggle("active", a.dataset.page === page));
  render();
}
async function render() {
  const fn = PAGES[S.page] || PAGES.dashboard;
  const el = $("#page");
  try { await fn(el); } catch (e) { el.innerHTML = `<div class="card"><div class="result err">${esc(e.message)}</div></div>`; }
  hydrateIcons(el);
}

// ---------------------------------------------------------------- polling
async function pollState() {
  try {
    S.state = await api("/api/state");
    const st = S.state;
    $("#status-pill .dot").className = "dot " + st.level;
    $("#status-text").textContent = st.text;
    $("#version").textContent = "версия " + st.version;
    const b = $("#banner");
    if (st.config_warning) { b.hidden = false; b.className = "banner"; b.textContent = st.config_warning; }
    else if (st.dry_run) { b.hidden = false; b.className = "banner info"; b.innerHTML = "Включён <b>тестовый режим</b>: программа показывает, что сделала бы, но не переключает устройства. Отключить — в «Настройках»."; }
    else b.hidden = true;
    if (S.page === "dashboard") renderDashboardLive();
    if (!st.wizard_done && !S.wizardShown) { S.wizardShown = true; wizard(); }
    S.fails = 0;
    $("#closed").hidden = true;
  } catch (e) {
    $("#status-pill .dot").className = "dot error";
    $("#status-text").textContent = "Нет связи с программой";
    if (++S.fails >= 3 || S.quitting) showClosed();
  }
}

async function pollLogs() {
  try {
    const r = await api(`/api/logs?after=${S.logAfter}`);
    if (r.items.length) {
      S.logAfter = r.items[r.items.length - 1].id;
      S.logs.push(...r.items);
      if (S.logs.length > 3000) S.logs.splice(0, S.logs.length - 3000);
      if (S.page !== "logs") {
        S.unseenErrors += r.items.filter(i => i.level === "ERROR").length;
      } else appendLogs(r.items);
      const badge = $("#log-badge");
      badge.hidden = !S.unseenErrors;
      badge.textContent = S.unseenErrors > 99 ? "99+" : S.unseenErrors;
    }
  } catch (e) { /* ignore */ }
}

async function loadConfig() {
  S.config = await api("/api/config");
  return S.config;
}

// ================================================================= DASHBOARD
PAGES.dashboard = async el => {
  if (!S.config) await loadConfig();
  el.innerHTML = `<div class="head"><div><h1>Обзор</h1><p class="sub">Состояние синхронизации SmartShell и умного дома в реальном времени</p></div></div>
    <div id="dash-live"></div>`;
  renderDashboardLive();
};

const LEVEL_ICON = { ok: "check", warn: "alert", error: "alert", paused: "pause", setup: "gear" };

function renderDashboardLive() {
  const box = $("#dash-live");
  const st = S.state;
  if (!box || !st) return;
  const conns = S.config?.connectors || [];
  const cOk = conns.filter(c => st.connectors[c.id]?.ok).length;
  const now = Date.now() / 1000;
  const tiles = st.bindings.map(b => {
    const s = b.state || {};
    const on = s.actual === true, unk = s.actual === null || s.actual === undefined;
    const host = b.host;
    let sess = host ? (host.active ? '<span class="tag ok">Сеанс идёт</span>' : host.in_service ? '<span class="tag warn">Сервис</span>' : '<span class="tag">Свободен</span>')
      : '<span class="tag err">Хост не найден</span>';
    let extra = "";
    if (s.off_since && b.off_delay) extra += `<span class="tag warn">Выкл. через ${mmss(b.off_delay - (now - s.off_since))}</span>`;
    if (s.hold_in) extra += `<span class="tag info">Ручной режим ${mmss(s.hold_in)}</span>`;
    if (!b.enabled) extra += '<span class="tag">Отключено</span>';
    const err = s.error ? `<div class="err-text">${esc(s.error)}</div>` : "";
    return `<div class="tile ${on ? "on" : ""} ${s.error ? "err" : ""}">
      <div class="tile-top"><div class="power ${on ? "on" : unk ? "unk" : ""}" title="${on ? "Включено" : unk ? "Состояние неизвестно" : "Выключено"}">${icon("power")}</div>
        <div class="grow" style="min-width:0"><div class="tile-name">${esc(b.host_alias || "—")}</div><div class="tile-dev">${esc(b.device_name || b.device_id)} · ${esc(connName(b.connector_id))}${(st.clubs || []).length > 1 && b.club_name ? ` · ${esc(b.club_name)}` : ""}</div></div></div>
      <div class="row">${sess}${extra}</div>${err}
      <div class="row small muted"><span class="grow">${s.last_action ? `${esc(s.last_action)} в ${fmtTime(s.last_action_ts)}` : "&nbsp;"}</span>
        ${s.hold_in ? `<button class="btn sm" data-release="${b.id}" title="Вернуть автоматическое управление">Авто</button>` : ""}
        <button class="btn sm" data-man="${b.id}" data-on="1">Вкл</button><button class="btn sm" data-man="${b.id}" data-on="0">Выкл</button></div></div>`;
  }).join("");

  box.innerHTML = `
    <div class="card hero ${st.level}"><div class="big-dot">${icon(LEVEL_ICON[st.level] || "check")}</div>
      <div class="grow"><div class="hero-title">${esc(st.text)}</div>
      <div class="muted small">Работает ${fmtDur(st.uptime)} · последняя проверка ${fmtTime(st.last_cycle)} (${st.last_cycle_ms} мс) · циклов: ${st.cycles}</div></div>
      <div class="row"><button class="btn" id="d-run">${icon("refresh")}Проверить сейчас</button>
      <button class="btn ${st.paused ? "primary" : ""}" id="d-pause">${icon(st.paused ? "play" : "pause")}${st.paused ? "Продолжить" : "Пауза"}</button></div></div>
    <div class="grid g4" style="margin-bottom:22px">
      <div class="card stat"><div class="label">${icon("monitor").replace("<svg", '<svg width="14"')} SmartShell</div>
        <div class="value">${st.smartshell.active}<span class="muted" style="font-size:16px"> / ${st.smartshell.hosts}</span></div>
        <div class="hint">${st.smartshell.ok === false && (st.clubs || []).length < 2 ? `<span style="color:var(--err)">${esc(st.smartshell.message)}</span>`
          : "активных сеансов" + ((st.clubs || []).length > 1 ? ` · клубов: ${st.clubs.length}` : st.smartshell.club ? " · " + esc(st.smartshell.club) : "")}</div></div>
      <div class="card stat"><div class="label">${icon("home").replace("<svg", '<svg width="14"')} Умный дом</div>
        <div class="value">${cOk}<span class="muted" style="font-size:16px"> / ${conns.length}</span></div><div class="hint">систем на связи</div></div>
      <div class="card stat"><div class="label">${icon("link").replace("<svg", '<svg width="14"')} Привязки</div>
        <div class="value">${st.bindings.filter(b => b.state?.actual).length}<span class="muted" style="font-size:16px"> / ${st.bindings.length}</span></div><div class="hint">устройств включено</div></div>
      <div class="card stat"><div class="label">${icon("shield").replace("<svg", '<svg width="14"')} Запросы к SmartShell</div>
        <div class="value">${st.smartshell.rpm_used}<span class="muted" style="font-size:16px"> / 20</span></div><div class="hint">за последнюю минуту (лимит API)</div></div>
    </div>
    ${(st.clubs || []).length > 1 ? `<div class="club-strip">${st.clubs.map(c => `<div class="club-chip ${c.ok === false ? "err" : ""}" title="${esc(c.message)}">
        <span class="dot ${c.ok ? "ok" : c.ok === false ? "error" : ""}"></span><b>${esc(c.name)}</b>
        <span class="muted">${c.ok === false ? "нет связи" : `${c.active} / ${c.hosts}`}</span></div>`).join("")}</div>` : ""}
    ${st.bindings.length ? `<div class="grid g3">${tiles}</div>` :
      `<div class="card empty">${icon("link")}<h2>Пока нет привязок</h2><p>Укажите, какое устройство включать на каждом хосте SmartShell.</p>
       <div class="row" style="justify-content:center"><button class="btn primary" onclick="wizard()">Мастер настройки</button><button class="btn" onclick="go('bindings')">Привязать устройства</button></div></div>`}`;
  $("#d-run").onclick = e => busy(e.currentTarget, async () => { await api("/api/engine", { action: "run" }); toast("Проверка запущена"); setTimeout(pollState, 1500); });
  $("#d-pause").onclick = e => busy(e.currentTarget, async () => { await api("/api/engine", { action: st.paused ? "resume" : "pause" }); await pollState(); });
  $$("[data-man]", box).forEach(b => b.onclick = e => busy(e.currentTarget, async () => {
    await api("/api/devices/set", { binding_id: b.dataset.man, on: b.dataset.on === "1" });
    toast("Команда выполнена. Автоуправление этим устройством приостановлено на 5 минут", "ok");
    setTimeout(pollState, 800);
  }));
  $$("[data-release]", box).forEach(b => b.onclick = async () => { await api("/api/bindings/release", { binding_id: b.dataset.release }); toast("Автоматическое управление восстановлено"); setTimeout(pollState, 1200); });
}

// ================================================================= HOSTS (привязки)
async function ensureHosts(refresh = false) {
  const r = await api("/api/hosts" + (refresh ? "?refresh=1" : ""));
  S.clubsHosts = r.clubs;
  selectClub(hostsView.club);
}
function selectClub(id) {
  const list = S.clubsHosts || [];
  const c = list.find(x => x.id === id) || list[0];
  hostsView.club = c ? c.id : "";
  S.hosts = c ? c.hosts : [];
  S.groups = c ? c.groups : [];
  S.hostsError = c ? c.error : "";
}
async function ensureDevices(cid, refresh = false) {
  if (!cid) return [];
  if (S.devices[cid] && !refresh) return S.devices[cid];
  try { S.devices[cid] = (await api("/api/connectors/devices", { id: cid })).devices; }
  catch (e) { S.devices[cid] = []; S.devices[cid].error = e.message; }
  return S.devices[cid];
}
async function loadAllDevices(refresh = false) {
  S.allDevices = (await api("/api/devices/all" + (refresh ? "?refresh=1" : ""))).systems;
  return S.allDevices;
}

// то же, что _norm на сервере: регистр, пробелы/дефисы, похожие латинские и русские буквы
const LAT2CYR = { a: "а", b: "в", e: "е", k: "к", m: "м", h: "н", o: "о", p: "р", c: "с", t: "т", y: "у", x: "х" };
function norm(s) {
  return String(s || "").trim().toLowerCase().replace(/ё/g, "е").replace(/[abekmhopctyx]/g, ch => LAT2CYR[ch]).replace(/[\s_\-.]+/g, "");
}
function flatDevices() {
  const out = [];
  (S.allDevices || []).forEach(sys => sys.devices.forEach(d => out.push({ ...d, connector_id: sys.id, sys })));
  return out;
}
function inClub(b) { return !b.club_id || !hostsView.club || b.club_id === hostsView.club; }
function bindingsOf(hostId) { return (S.config?.bindings || []).filter(b => String(b.host_id) === String(hostId) && inClub(b)); }
function bindingOfDevice(cid, did) { return (S.config?.bindings || []).find(b => b.connector_id === cid && b.device_id === did); }
function liveDeviceState(b) {
  const st = (S.state?.bindings || []).find(x => x.id === b.id);
  return st?.state?.actual;
}
function suggestions() {
  if (!S.hosts || !S.allDevices) return [];
  const devs = flatDevices().filter(d => !bindingOfDevice(d.connector_id, d.id));
  const out = [];
  S.hosts.forEach(h => {
    if (bindingsOf(h.id).length) return;
    const d = devs.find(x => norm(x.name) === norm(h.alias) && !out.some(o => o.device_id === x.id && o.connector_id === x.connector_id));
    if (d) out.push({ club_id: hostsView.club, host_id: h.id, host_alias: h.alias, connector_id: d.connector_id, device_id: d.id, device_name: d.name });
  });
  return out;
}
const hostsView = { q: "", mode: "all", club: "" };

PAGES.bindings = async el => {
  el.innerHTML = `<div class="head"><div><h1>Хосты и устройства</h1><p class="sub">Устройство включается, когда на хосте идёт сеанс, и выключается, когда сеанс заканчивается</p></div>
    <div class="row"><button class="btn" id="h-refresh">${icon("refresh")}Обновить</button><button class="btn primary" id="h-console">${icon("gamepad")}Добавить приставку</button></div></div>
    <div id="h-body"><div class="card empty">Загружаем хосты из SmartShell…</div></div>`;
  hydrateIcons(el);
  $("#h-refresh").onclick = e => busy(e.currentTarget, async () => { await reloadHostsPage(true); toast("Списки обновлены"); }).catch(() => {});
  $("#h-console").onclick = () => consoleDialog();
  await reloadHostsPage(false);
};

async function reloadHostsPage(refresh) {
  await loadConfig();
  S.hostsError = "";
  const hostsP = ensureHosts(refresh).catch(e => { S.hostsError = e.message; S.hosts = S.hosts || []; S.clubsHosts = S.clubsHosts || []; });
  const devP = loadAllDevices(refresh).catch(e => { S.allDevices = []; S.devicesError = e.message; });
  await hostsP;
  drawHosts();
  await devP;
  drawHosts();
}

function drawHosts() {
  const box = $("#h-body");
  if (!box) return;
  const conns = S.config.connectors;
  const hosts = S.hosts || [];
  const clubsH = S.clubsHosts || [];
  if (!(S.config.clubs || []).length) {
    box.innerHTML = `<div class="card empty">${icon("monitor")}<h2>Клуб SmartShell не подключён</h2><p>Добавьте клуб — и здесь появятся его хосты.</p>
      <button class="btn primary" onclick="addClubDialog(() => go('bindings'))">${icon("plus")}Добавить клуб</button></div>`;
    hydrateIcons(box); return;
  }
  const tabs = clubsH.length > 1 ? `<div class="seg club-seg">${clubsH.map(c => `<button data-club="${c.id}" class="${c.id === hostsView.club ? "on" : ""}">
      ${esc(c.name)} <span class="cnt">${c.hosts.length}</span>${c.error ? ' <span class="dev-dot err" title="нет связи"></span>' : ""}</button>`).join("")}</div>` : "";
  if (S.hostsError && !hosts.length) {
    box.innerHTML = `${tabs}<div class="card empty">${icon("monitor")}<h2>Нет связи со SmartShell${clubsH.length > 1 ? ` («${esc(clubName(hostsView.club))}»)` : ""}</h2><p>${esc(S.hostsError)}</p>
      <button class="btn primary" onclick="go('smartshell')">Настроить SmartShell</button></div>`;
    hydrateIcons(box); bindClubTabs(box); return;
  }
  const sugg = suggestions();
  const q = norm(hostsView.q);
  const known = new Set(hosts.map(h => String(h.id)));
  const orphans = S.hostsError ? [] : S.config.bindings.filter(b => (b.club_id || hostsView.club) === hostsView.club && !known.has(String(b.host_id)));
  const filtered = hosts.filter(h => {
    const bound = bindingsOf(h.id).length > 0;
    if (hostsView.mode === "bound" && !bound) return false;
    if (hostsView.mode === "free" && bound) return false;
    if (!q) return true;
    return norm(h.alias).includes(q) || bindingsOf(h.id).some(b => norm(b.device_name).includes(q));
  });
  const groups = {};
  filtered.forEach(h => (groups[h.group || "Без группы"] = groups[h.group || "Без группы"] || []).push(h));
  const boundCount = hosts.filter(h => bindingsOf(h.id).length).length;

  const chip = b => {
    const st = liveDeviceState(b);
    const sys = conns.find(c => c.id === b.connector_id);
    const dot = st === true ? "ok" : st === false ? "" : "unk";
    return `<div class="dev-chip ${b.enabled === false ? "off" : ""}" title="${esc(sys?.name || "")}">
      ${sysIcon(sys?.type, 22)}<span class="dev-dot ${dot}" title="${st === true ? "включено" : st === false ? "выключено" : "состояние неизвестно"}"></span>
      <span class="dev-name">${esc(b.device_name || b.device_id)}</span>
      ${b.off_delay ? `<span class="tag" title="Задержка выключения">${fmtDelay(b.off_delay)}</span>` : ""}
      ${b.on_in_service ? '<span class="tag" title="Включать в сервисном режиме">сервис</span>' : ""}
      ${b.invert ? '<span class="tag" title="Инверсия">инверсия</span>' : ""}
      ${b.enabled === false ? '<span class="tag">отключено</span>' : ""}
      <button class="icon-btn" data-bset="${b.id}" title="Настройки">${icon("gear")}</button>
      <button class="icon-btn danger" data-bdel="${b.id}" title="Отвязать">${icon("x")}</button></div>`;
  };
  const hostRow = h => {
    const bs = bindingsOf(h.id);
    const status = h.active ? '<span class="tag ok">идёт сеанс</span>' : h.in_service ? '<span class="tag warn">сервис</span>' : '<span class="tag">свободен</span>';
    return `<div class="host-row ${bs.length ? "bound" : ""}">
      <div class="host-main"><div class="host-ic ${h.virtual ? "console" : ""}">${icon(h.virtual ? "gamepad" : "monitor")}</div>
        <div style="min-width:0"><div class="host-name">${esc(h.alias)}</div><div class="row" style="gap:6px">${status}${h.virtual ? '<span class="tag info">приставка</span>' : ""}</div></div></div>
      <div class="host-devs">${bs.map(chip).join("") || '<span class="muted small">устройство не привязано</span>'}</div>
      <div class="host-act"><button class="btn sm ${bs.length ? "ghost" : "primary"}" data-pick="${h.id}">${icon("plus")}${bs.length ? "Ещё" : "Привязать устройство"}</button></div></div>`;
  };

  box.innerHTML = `${tabs}
    ${!conns.length ? `<div class="banner info">Сначала добавьте систему умного дома, в которой находятся ваши розетки. <a href="#systems" onclick="go('systems');return false">Добавить систему →</a></div>` : ""}
    ${(S.allDevices || []).filter(s => !s.ok).map(s => `<div class="banner">«${esc(s.name)}» недоступна: ${esc(s.error)}</div>`).join("")}
    ${S.hostsError ? `<div class="banner">SmartShell: ${esc(S.hostsError)}</div>` : ""}
    ${sugg.length ? `<div class="card suggest"><div class="row"><div class="sys-icon" style="background:linear-gradient(135deg,var(--accent),var(--accent2))">${icon("wand")}</div>
      <div class="grow"><b>Нашли совпадения по названиям: ${sugg.length}</b><div class="small muted">${sugg.slice(0, 6).map(s => `${esc(s.host_alias)} → ${esc(s.device_name)}`).join(" · ")}${sugg.length > 6 ? " …" : ""}</div></div>
      <button class="btn primary" id="h-sugg">${icon("link")}Привязать все</button></div></div>` : ""}
    <div class="row" style="margin:6px 0 14px"><span class="search">${icon("search")}<input id="h-q" placeholder="Поиск хоста или устройства" value="${esc(hostsView.q)}"></span>
      <div class="seg">${[["all", `Все (${hosts.length})`], ["bound", `С устройством (${boundCount})`], ["free", `Без устройства (${hosts.length - boundCount})`]]
        .map(([k, l]) => `<button data-mode="${k}" class="${hostsView.mode === k ? "on" : ""}">${l}</button>`).join("")}</div></div>
    ${hosts.length ? "" : `<div class="card empty">${icon("monitor")}<h2>На карте клуба нет хостов</h2><p>Для приставок без шелла нажмите «Добавить приставку».</p></div>`}
    ${Object.entries(groups).map(([g, hs]) => `<div class="section-title">${esc(g)} · ${hs.length}</div><div class="card host-list">${hs.map(hostRow).join("")}</div>`).join("")}
    ${hosts.length && !filtered.length ? `<div class="card empty">Ничего не найдено</div>` : ""}
    ${orphans.length ? `<div class="section-title">Хост не найден в SmartShell</div><div class="card host-list">${orphans.map(b => `<div class="host-row">
      <div class="host-main"><div class="host-ic">${icon("alert")}</div><div><div class="host-name">${esc(b.host_alias || "#" + b.host_id)}</div><span class="tag err">удалён или переименован</span></div></div>
      <div class="host-devs">${chip(b)}</div><div class="host-act"></div></div>`).join("")}</div>` : ""}`;
  hydrateIcons(box);
  bindClubTabs(box);

  const qi = $("#h-q");
  qi.oninput = () => { hostsView.q = qi.value; const pos = qi.selectionStart; drawHosts(); const n = $("#h-q"); n.focus(); n.setSelectionRange(pos, pos); };
  $$("[data-mode]", box).forEach(b => b.onclick = () => { hostsView.mode = b.dataset.mode; drawHosts(); });
  const sb = $("#h-sugg");
  if (sb) sb.onclick = e => busy(e.currentTarget, async () => {
    const r = await api("/api/bindings/add-many", { items: sugg });
    toast(`Привязано устройств: ${r.added}`, "ok");
    await loadConfig(); drawHosts();
  }).catch(() => {});
  $$("[data-pick]", box).forEach(b => b.onclick = () => {
    const h = hosts.find(x => String(x.id) === b.dataset.pick);
    devicePicker({ title: `Устройство для «${esc(h.alias)}»`, hint: h.alias, onPick: async d => {
      await api("/api/bindings/add", { club_id: hostsView.club, host_id: h.id, host_alias: h.alias, connector_id: d.connector_id, device_id: d.id, device_name: d.name });
      toast(`${h.alias} → ${d.name}`, "ok");
      await loadConfig(); drawHosts();
    } });
  });
  $$("[data-bset]", box).forEach(b => b.onclick = () => bindingSettings(S.config.bindings.find(x => x.id === b.dataset.bset)));
  $$("[data-bdel]", box).forEach(b => b.onclick = async () => {
    const bd = S.config.bindings.find(x => x.id === b.dataset.bdel);
    if (!(await confirmBox(`Отвязать «${esc(bd.device_name || bd.device_id)}» от хоста «${esc(bd.host_alias)}»? Программа перестанет управлять этим устройством.`, "Отвязать"))) return;
    await api("/api/bindings/delete", { id: bd.id });
    toast("Отвязано"); await loadConfig(); drawHosts();
  });
}

function bindClubTabs(box) {
  $$("[data-club]", box).forEach(b => b.onclick = () => { selectClub(b.dataset.club); drawHosts(); });
}

function fmtDelay(s) { return s >= 60 ? `${Math.round(s / 6) / 10} мин` : `${s} с`; }

// ---- выбор устройства (общий для «Привязать» и «Добавить приставку»)
function devicePicker({ title, hint, onPick }) {
  const m = modal({ title, body: `<div class="row" style="margin-bottom:12px"><span class="search grow">${icon("search")}<input id="dp-q" placeholder="Поиск устройства" autofocus></span>
      <button class="btn" id="dp-refresh">${icon("refresh")}Обновить</button></div><div id="dp-list"><div class="empty">Загрузка устройств…</div></div>` });
  const draw = () => {
    const list = $("#dp-list", m.el);
    if (!list) return;
    if (!(S.config.connectors || []).length) {
      list.innerHTML = `<div class="empty">${icon("home")}<p>Не подключено ни одной системы умного дома.</p><button class="btn primary" id="dp-add">Добавить систему</button></div>`;
      hydrateIcons(list);
      $("#dp-add", list).onclick = () => { m.close(); go("systems"); setTimeout(() => addSystemDialog(), 300); };
      return;
    }
    const q = norm($("#dp-q", m.el).value);
    const all = flatDevices().filter(d => !q || norm(d.name).includes(q) || norm(d.room).includes(q));
    const best = hint ? all.filter(d => norm(d.name) === norm(hint) || (norm(hint) && norm(d.name).includes(norm(hint)))) : [];
    const item = d => {
      const used = bindingOfDevice(d.connector_id, d.id);
      return `<div class="pick" data-c="${esc(d.connector_id)}" data-d="${esc(d.id)}">${sysIcon(d.sys.type, 30)}
        <div class="grow" style="min-width:0"><div class="pick-name">${esc(d.name)}</div><div class="small muted">${esc([d.sys.name, d.room, d.kind].filter(Boolean).join(" · "))}</div></div>
        ${used ? `<span class="tag warn">уже у «${esc(used.host_alias)}»${multiClub() && used.club_id !== hostsView.club ? ` (${esc(clubName(used.club_id))})` : ""}</span>` : ""}
        ${!d.online ? '<span class="tag err">не в сети</span>' : d.state === true ? '<span class="tag ok">вкл</span>' : d.state === false ? '<span class="tag">выкл</span>' : ""}</div>`;
    };
    let html = "";
    if (best.length) html += `<div class="section-title">Подходят по названию</div>${best.map(item).join("")}`;
    (S.allDevices || []).forEach(sys => {
      // свободные устройства — сверху, уже привязанные к другим хостам — в конце
      const ds = all.filter(d => d.connector_id === sys.id && !best.includes(d))
        .sort((a, b) => (!!bindingOfDevice(a.connector_id, a.id)) - (!!bindingOfDevice(b.connector_id, b.id)));
      if (!sys.ok) html += `<div class="section-title">${esc(sys.name)}</div><div class="result err">${esc(sys.error)}</div>`;
      else if (ds.length) html += `<div class="section-title">${esc(sys.name)} · ${ds.length}</div>${ds.map(item).join("")}`;
    });
    if (!html) html = `<div class="empty">${q ? "Ничего не найдено" : "В подключённых системах нет устройств с функцией вкл/выкл"}</div>`;
    list.innerHTML = html;
    hydrateIcons(list);
    $$(".pick", list).forEach(p => p.onclick = async () => {
      const d = flatDevices().find(x => x.connector_id === p.dataset.c && x.id === p.dataset.d);
      p.classList.add("busy");
      try { await onPick(d); m.close(); } catch (e) { toast(e.message, "err"); p.classList.remove("busy"); }
    });
  };
  $("#dp-q", m.el).oninput = draw;
  $("#dp-refresh", m.el).onclick = e => busy(e.currentTarget, async () => { await loadAllDevices(true); draw(); }).catch(() => {});
  if (S.allDevices) draw();
  loadAllDevices(false).then(draw).catch(e => { $("#dp-list", m.el).innerHTML = `<div class="result err">${esc(e.message)}</div>`; });
  return m;
}

// ---- «Добавить приставку»: выбрать устройство → создать хост с тем же названием и привязать
function consoleDialog() {
  let club = hostsView.club;
  const groupsOf = () => ((S.clubsHosts || []).find(c => c.id === club) || {}).groups || S.groups || [];
  const pickGroup = () => (groupsOf().find(g => /консол|приставк|playstation|xbox|ps\d|vr|sim/i.test(g.title)) || groupsOf()[0] || {}).id;
  const groupOptions = () => groupsOf().map(g => `<option value="${g.id}" ${g.id === pickGroup() ? "selected" : ""}>${esc(g.title)}</option>`).join("");
  let chosen = null, autoName = true;
  const m = modal({ title: "Добавить приставку", narrow: true, body: `
    <p class="muted" style="margin-top:0">Для приставок, ТВ, VR, симуляторов — всего, на чём нет шелла SmartShell. Программа создаст хост на карте клуба,
      будет держать его «в сети» и включать выбранное устройство, когда администратор запустит сеанс.</p>
    <div class="stack">
      <div class="f"><span class="muted">1. Устройство (розетка), которое включать</span>
        <div id="cd-dev" class="pick empty-pick">${icon("plus")}<span>Выбрать устройство</span></div></div>
      <label class="f"><span>2. Название хоста на карте клуба <b>*</b></span><input id="cd-name" placeholder="PS5-1"></label>
      ${multiClub() ? `<label class="f"><span>Клуб</span><select id="cd-club">${(S.config.clubs || []).filter(c => c.enabled !== false)
        .map(c => `<option value="${c.id}" ${c.id === club ? "selected" : ""}>${esc(c.name)}</option>`).join("")}</select></label>` : ""}
      <label class="f"><span>3. Группа хостов</span><select id="cd-group">${groupOptions()}</select></label>
    </div>`,
    foot: `<button class="btn" data-x>Отмена</button><button class="btn primary" id="cd-ok">${icon("check")}Создать</button>` });
  hydrateIcons(m.el);
  $("[data-x]", m.el).onclick = m.close;
  const nameIn = $("#cd-name", m.el);
  nameIn.oninput = () => { autoName = !nameIn.value; };
  const drawChosen = () => {
    const box = $("#cd-dev", m.el);
    if (!chosen) return;
    box.className = "pick";
    box.innerHTML = `${sysIcon(chosen.sys.type, 30)}<div class="grow"><div class="pick-name">${esc(chosen.name)}</div><div class="small muted">${esc(chosen.sys.name)}</div></div><span class="small muted">изменить</span>`;
  };
  $("#cd-dev", m.el).onclick = () => devicePicker({ title: "Устройство для приставки", onPick: async d => {
    chosen = d; drawChosen();
    if (autoName || !nameIn.value) { nameIn.value = d.name; autoName = true; }
  } });
  const clubSel = $("#cd-club", m.el);
  if (clubSel) clubSel.onchange = () => { club = clubSel.value; $("#cd-group", m.el).innerHTML = groupOptions(); };
  if (!groupsOf().length) ensureHosts().then(() => { club = club || hostsView.club; $("#cd-group", m.el).innerHTML = groupOptions(); }).catch(() => {});
  $("#cd-ok", m.el).onclick = e => busy(e.currentTarget, async () => {
    const alias = nameIn.value.trim();
    if (!alias) { nameIn.focus(); throw new Error("Введите название хоста"); }
    const body = { alias, club_id: club || hostsView.club, group_id: +$("#cd-group", m.el).value || undefined };
    if (chosen) Object.assign(body, { connector_id: chosen.connector_id, device_id: chosen.id, device_name: chosen.name });
    const r = await api("/api/hosts/virtual", body);
    toast(chosen ? `Хост «${r.host.alias}» создан и привязан к «${chosen.name}»` : `Хост «${r.host.alias}» создан`, "ok");
    m.close();
    hostsView.club = body.club_id;  // показать клуб, где создан хост
    if (S.page === "bindings") await reloadHostsPage(true);
  }).catch(() => {});
}

// ---- настройки привязки
function bindingSettings(b) {
  const presets = [[0, "Сразу"], [30, "30 секунд"], [60, "1 минута"], [120, "2 минуты"], [300, "5 минут"], [600, "10 минут"]];
  const custom = !presets.some(p => p[0] === (b.off_delay || 0));
  const m = modal({ title: `${esc(b.host_alias)} → ${esc(b.device_name || b.device_id)}`, narrow: true, body: `<div class="stack">
    <label class="f"><span>Выключать после окончания сеанса</span><select id="bs-delay">${presets.map(([v, l]) => `<option value="${v}" ${!custom && v === (b.off_delay || 0) ? "selected" : ""}>${l}</option>`).join("")}
      <option value="custom" ${custom ? "selected" : ""}>Своя задержка…</option></select>
      <input type="number" min="0" id="bs-custom" class="${custom ? "" : "hidden"}" value="${b.off_delay || 0}" placeholder="секунд">
      <span class="help">Задержка даёт гостю время сохранить игру. Если сеанс продлят — устройство не выключится.</span></label>
    ${sw("bs-service", b.on_in_service, "Включать, когда хост в сервисном режиме")}
    ${sw("bs-invert", b.invert, "Инверсия: включено, пока хост свободен (например, лампа «свободно»)")}
    ${sw("bs-enabled", b.enabled !== false, "Управлять этим устройством")}
    <div class="docs"><div class="row"><span class="grow">Проверить устройство:</span><button class="btn sm" data-t="1">Вкл</button><button class="btn sm" data-t="0">Выкл</button></div>
      <div class="small" style="margin-top:6px">После ручной проверки автоуправление приостанавливается на 5 минут.</div></div></div>`,
    foot: `<button class="btn danger" id="bs-del" style="margin-right:auto">${icon("trash")}Отвязать</button><button class="btn primary" id="bs-ok">${icon("check")}Готово</button>` });
  const sel = $("#bs-delay", m.el), cin = $("#bs-custom", m.el);
  sel.onchange = () => cin.classList.toggle("hidden", sel.value !== "custom");
  $$("[data-t]", m.el).forEach(t => t.onclick = e => busy(e.currentTarget, async () => {
    await api("/api/devices/set", { binding_id: b.id, on: t.dataset.t === "1" });
    toast(t.dataset.t === "1" ? "Включено" : "Выключено", "ok");
  }).catch(() => {}));
  $("#bs-del", m.el).onclick = async () => {
    await api("/api/bindings/delete", { id: b.id });
    toast("Отвязано"); m.close(); await loadConfig(); drawHosts();
  };
  $("#bs-ok", m.el).onclick = e => busy(e.currentTarget, async () => {
    const delay = sel.value === "custom" ? Math.max(0, +cin.value || 0) : +sel.value;
    await api("/api/bindings/update", { id: b.id, off_delay: delay, on_in_service: $("#bs-service", m.el).checked,
      invert: $("#bs-invert", m.el).checked, enabled: $("#bs-enabled", m.el).checked });
    toast("Сохранено", "ok"); m.close(); await loadConfig(); drawHosts();
  }).catch(() => {});
}

// ================================================================= SYSTEMS
PAGES.systems = async el => {
  await loadConfig();
  if (!S.types.length) S.types = (await api("/api/connector-types")).types;
  const conns = S.config.connectors;
  const cards = conns.map(c => {
    const t = typeInfo(c.type), cs = S.state?.connectors[c.id];
    const tag = c.enabled === false ? '<span class="tag">Отключено</span>' : !cs || cs.ok === null ? '<span class="tag">Проверяется…</span>'
      : cs.ok ? '<span class="tag ok">На связи</span>' : `<span class="tag err" title="${esc(cs.message)}">Нет связи</span>`;
    const used = S.config.bindings.filter(b => b.connector_id === c.id).length;
    return `<div class="card sys-card"><div class="row">${sysIcon(c.type)}<div class="grow"><div style="font-weight:600">${esc(c.name)}</div><div class="small muted">${esc(t.title)}</div></div>${tag}</div>
      ${cs && cs.ok === false ? `<div class="small" style="color:var(--err)">${esc(cs.message)}</div>` : ""}
      <div class="small muted">Привязок: ${used}</div>
      <div class="row"><button class="btn sm" data-edit="${c.id}">${icon("edit")}Настроить</button><button class="btn sm" data-test="${c.id}">${icon("check")}Проверить</button>
      <button class="btn sm" data-devs="${c.id}">${icon("list")}Устройства</button></div></div>`;
  }).join("");
  el.innerHTML = `<div class="head"><div><h1>Умный дом</h1><p class="sub">Подключённые системы умного дома. Можно использовать несколько одновременно.</p></div>
    <button class="btn primary" id="s-add">${icon("plus")}Добавить систему</button></div>
    ${conns.length ? `<div class="grid g3">${cards}</div>` : `<div class="card empty">${icon("home")}<h2>Нет подключённых систем</h2><p>Поддерживаются Яндекс, Home Assistant, Tuya, SmartThings, Shelly, Tasmota, Sonoff, MQTT и другие.</p><button class="btn primary" onclick="addSystemDialog()">Добавить систему</button></div>`}`;
  $("#s-add").onclick = () => addSystemDialog();
  $$("[data-edit]", el).forEach(b => b.onclick = () => editSystemDialog(conns.find(c => c.id === b.dataset.edit)));
  $$("[data-test]", el).forEach(b => b.onclick = e => busy(e.currentTarget, async () => { const r = await api("/api/connectors/test", { id: b.dataset.test }); toast(r.message, "ok"); }));
  $$("[data-devs]", el).forEach(b => b.onclick = () => devicesDialog(conns.find(c => c.id === b.dataset.devs)));
};

function addSystemDialog(after) {
  const groups = {};
  S.types.forEach(t => (groups[t.category] = groups[t.category] || []).push(t));
  const body = Object.entries(CATEGORIES).filter(([k]) => groups[k]).map(([k, label]) => `<div class="section-title">${label}</div><div class="type-grid">` +
    groups[k].map(t => `<div class="type-card" data-type="${t.type}">${sysIcon(t.type, 36)}<div><div class="t">${esc(t.title)}</div><div class="d">${esc(t.description)}</div></div></div>`).join("") + "</div>").join("")
    + `<div class="docs" style="margin-top:16px">Нет вашей системы? Подключите её через <b>Home Assistant</b> (Xiaomi, Aqara, Sber, HomeKit, Google Home и сотни других),
      <b>MQTT</b> или <b>HTTP-запросы</b>.</div>`;
  const m = modal({ title: "Добавить систему умного дома", body });
  $$("[data-type]", m.el).forEach(c => c.onclick = () => { m.close(); editSystemDialog({ type: c.dataset.type, enabled: true, settings: {} }, after); });
}

function fieldHtml(f, val) {
  const v = val === undefined || val === null || val === "" ? f.default : val;
  const req = f.required ? " <b>*</b>" : "";
  const help = f.help ? `<span class="help">${esc(f.help)}</span>` : "";
  if (f.type === "bool") return `<div class="f" style="justify-content:flex-end">${sw("", !!v, esc(f.label), `data-key="${f.key}"`)}${help}</div>`;
  if (f.type === "select") return `<label class="f"><span>${esc(f.label)}${req}</span><select data-key="${f.key}">${f.options.map(o => `<option value="${esc(o.value)}" ${o.value == v ? "selected" : ""}>${esc(o.label)}</option>`).join("")}</select>${help}</label>`;
  if (f.type === "table") {
    const rows = (Array.isArray(val) && val.length ? val : [{}]);
    return `<div class="f full"><span class="muted">${esc(f.label)}</span><div class="table-wrap"><table data-table="${f.key}"><thead><tr>${f.columns.map(c => `<th>${esc(c.label)}</th>`).join("")}<th></th></tr></thead>
      <tbody>${rows.map(r => tableRow(f, r)).join("")}</tbody></table></div>
      <div><button class="btn sm" type="button" data-addrow="${f.key}">${icon("plus")}Добавить устройство</button></div>${help}</div>`;
  }
  const type = f.type === "number" ? "number" : "text";
  const secret = f.type === "password" ? ' data-secret spellcheck="false"' : "";
  return `<label class="f"><span>${esc(f.label)}${req}</span><input type="${type}"${secret} data-key="${f.key}" value="${esc(v)}" placeholder="${esc(f.placeholder || "")}" autocomplete="off">${help}</label>`;
}
function tableRow(f, r) {
  return `<tr>${f.columns.map(c => `<td${c.type === "number" ? ' class="num"' : ""}><input type="${c.type === "number" ? "number" : "text"}"${c.type === "password" ? " data-secret" : ""} autocomplete="off" data-col="${c.key}" value="${esc(r[c.key] ?? c.default ?? "")}" placeholder="${esc(c.placeholder || "")}"></td>`).join("")}
    <td><button class="btn sm danger" type="button" data-delrow>${icon("trash")}</button></td></tr>`;
}
function collectFields(root, fields) {
  const out = {};
  fields.forEach(f => {
    if (f.type === "table") {
      out[f.key] = $$(`table[data-table="${f.key}"] tbody tr`, root).map(tr => {
        const r = {}; $$("[data-col]", tr).forEach(i => r[i.dataset.col] = i.type === "number" ? (i.value === "" ? "" : +i.value) : i.value.trim()); return r;
      }).filter(r => Object.values(r).some(v => String(v).trim() !== "" && v !== 0));
    } else {
      const el = $(`[data-key="${f.key}"]`, root);
      if (!el) return;
      out[f.key] = el.type === "checkbox" ? el.checked : el.type === "number" ? (el.value === "" ? "" : +el.value) : el.value.trim();
    }
  });
  return out;
}

function editSystemDialog(conn, after) {
  const t = typeInfo(conn.type);
  const isNew = !conn.id;
  const m = modal({
    title: `${isNew ? "Новая система" : "Настройка"}: ${esc(t.title)}`,
    body: `<div class="stack">${t.docs ? `<div class="docs"><b>Как подключить</b><div style="margin-top:4px">${t.docs}</div></div>` : ""}
      <div class="form"><label class="f"><span>Название в программе</span><input id="sys-name" value="${esc(conn.name || t.title)}"></label>
      <div class="f" style="justify-content:flex-end">${sw("sys-enabled", conn.enabled !== false, "Включено")}</div>
      ${t.fields.map(f => fieldHtml(f, conn.settings?.[f.key])).join("")}</div>
      ${conn.type === "yandex" ? '<div id="ya-link"></div>' : ""}
      <div id="sys-result"></div><div id="sys-devs"></div></div>`,
    foot: `${!isNew ? `<button class="btn danger" id="sys-del" style="margin-right:auto">${icon("trash")}Удалить</button>` : ""}
      <button class="btn" id="sys-test">${icon("check")}Проверить</button><button class="btn" id="sys-list">${icon("list")}Устройства</button>
      <button class="btn primary" id="sys-save">${icon("check")}Сохранить</button>`,
  });
  const root = m.el;
  const payload = () => ({ id: conn.id, type: conn.type, name: $("#sys-name", root).value, enabled: $("#sys-enabled", root).checked, settings: collectFields(root, t.fields) });
  const result = (ok, msg) => { $("#sys-result", root).innerHTML = `<div class="result ${ok ? "ok" : "err"}">${esc(msg)}</div>`; };
  root.addEventListener("click", e => {
    const add = e.target.closest("[data-addrow]");
    if (add) { const f = t.fields.find(x => x.key === add.dataset.addrow); $(`table[data-table="${f.key}"] tbody`, root).insertAdjacentHTML("beforeend", tableRow(f, {})); hydrateIcons(root); }
    const del = e.target.closest("[data-delrow]");
    if (del) del.closest("tr").remove();
  });
  if (conn.type === "yandex") {
    const upd = () => {
      const cid = ($('[data-key="client_id"]', root)?.value || "").trim();
      $("#ya-link", root).innerHTML = cid ? `<a class="btn sm" target="_blank" href="https://oauth.yandex.ru/authorize?response_type=token&client_id=${encodeURIComponent(cid)}">${icon("link")}Получить токен Яндекса</a>` : "";
    };
    $('[data-key="client_id"]', root).addEventListener("input", upd); upd();
  }
  $("#sys-test", root).onclick = e => busy(e.currentTarget, async () => {
    try { const r = await api("/api/connectors/test", payload()); result(true, r.message); } catch (err) { result(false, err.message); }
  }).catch(() => {});
  $("#sys-list", root).onclick = e => busy(e.currentTarget, async () => {
    try {
      const r = await api("/api/connectors/devices", payload());
      $("#sys-devs", root).innerHTML = devicesTable(r.devices, null);
    } catch (err) { result(false, err.message); }
  }).catch(() => {});
  $("#sys-save", root).onclick = e => busy(e.currentTarget, async () => {
    const r = await api("/api/connectors", payload());
    toast("Система сохранена", "ok");
    delete S.devices[r.connector.id];
    m.close();
    await loadConfig();
    if (after) after(r.connector); else render();
  }).catch(() => {});
  const delBtn = $("#sys-del", root);
  if (delBtn) delBtn.onclick = async () => {
    const used = S.config.bindings.filter(b => b.connector_id === conn.id).length;
    if (!(await confirmBox(`Удалить «${esc(conn.name)}»?${used ? ` Будут удалены и привязки (${used}).` : ""}`))) return;
    await api("/api/connectors/delete", { id: conn.id });
    toast("Удалено"); m.close(); await loadConfig(); render();
  };
}

function devicesTable(devs, cid) {
  if (!devs.length) return `<div class="empty">Устройства с функцией вкл/выкл не найдены</div>`;
  return `<div class="table-wrap" style="margin-top:12px"><table><thead><tr><th>Устройство</th><th>Комната / тип</th><th>Состояние</th>${cid ? "<th>Проверка</th>" : ""}</tr></thead><tbody>
    ${devs.map(d => `<tr><td><b>${esc(d.name)}</b><div class="small muted mono">${esc(d.id)}</div></td><td class="muted">${esc([d.room, d.kind].filter(Boolean).join(" · "))}</td>
      <td>${!d.online ? '<span class="tag err">не в сети</span>' : d.state === true ? '<span class="tag ok">включено</span>' : d.state === false ? '<span class="tag">выключено</span>' : '<span class="tag warn">неизвестно</span>'}</td>
      ${cid ? `<td><div class="row"><button class="btn sm" data-dset="${esc(d.id)}" data-name="${esc(d.name)}" data-on="1">Вкл</button><button class="btn sm" data-dset="${esc(d.id)}" data-name="${esc(d.name)}" data-on="0">Выкл</button></div></td>` : ""}</tr>`).join("")}
    </tbody></table></div>`;
}

async function devicesDialog(conn) {
  const m = modal({ title: `Устройства: ${esc(conn.name)}`, body: `<div id="dd-body" class="empty">Загрузка…</div>`,
    foot: `<button class="btn" id="dd-refresh">${icon("refresh")}Обновить</button>` });
  const load = async () => {
    try {
      const devs = await ensureDevices(conn.id, true);
      if (devs.error) throw new Error(devs.error);
      $("#dd-body", m.el).innerHTML = `<p class="muted small">Кнопки «Вкл/Выкл» позволяют проверить, что устройство управляется. Если устройство привязано к хосту,
        при включённой синхронизации состояние будет приведено к нужному на следующем цикле.</p>` + devicesTable(devs, conn.id);
      $("#dd-body", m.el).className = "";
      $$("[data-dset]", m.el).forEach(b => b.onclick = e => busy(e.currentTarget, async () => {
        await api("/api/devices/set", { connector_id: conn.id, device_id: b.dataset.dset, device_name: b.dataset.name, on: b.dataset.on === "1" });
        toast(`«${b.dataset.name}»: ${b.dataset.on === "1" ? "включено" : "выключено"}`, "ok");
        setTimeout(load, 1500);
      }).catch(() => {}));
    } catch (e) { $("#dd-body", m.el).innerHTML = `<div class="result err">${esc(e.message)}</div>`; }
  };
  $("#dd-refresh", m.el).onclick = e => busy(e.currentTarget, load);
  load();
}

// ================================================================= SMARTSHELL (клубы)
function clubState(id) { return (S.state?.clubs || []).find(c => c.id === id); }
function clubName(id) { return (S.config?.clubs || []).find(c => c.id === id)?.name || ""; }
function multiClub() { return (S.config?.clubs || []).length > 1; }

PAGES.smartshell = async el => {
  await loadConfig();
  const clubs = S.config.clubs || [];
  const vh = S.config.virtual_hosts || [];
  const card = c => {
    const cs = clubState(c.id);
    const tag = c.enabled === false ? '<span class="tag">Отключён</span>' : !cs || cs.ok === null ? '<span class="tag">Проверяется…</span>'
      : cs.ok ? '<span class="tag ok">На связи</span>' : '<span class="tag err">Нет связи</span>';
    const nb = S.config.bindings.filter(b => b.club_id === c.id).length;
    const nv = vh.filter(v => v.club_id === c.id).length;
    return `<div class="card sys-card"><div class="row"><div class="sys-icon club-ic">${icon("monitor")}</div>
      <div class="grow" style="min-width:0"><div style="font-weight:600">${esc(c.name)}</div><div class="small muted">ID ${esc(c.company_id)} · логин ${esc(c.login)}</div></div>${tag}</div>
      ${cs && cs.ok === false ? `<div class="small" style="color:var(--err)">${esc(cs.message)}</div>` : ""}
      <div class="small muted">${cs && cs.ok ? `Хостов: ${cs.hosts}, идёт сеансов: ${cs.active} · ` : ""}Привязок: ${nb}${nv ? ` · приставок: ${nv}` : ""}</div>
      <div class="row"><button class="btn sm" data-cedit="${c.id}">${icon("edit")}Изменить</button><button class="btn sm" data-ctest="${c.id}">${icon("check")}Проверить</button>
        <button class="btn sm" data-chosts="${c.id}">${icon("link")}Хосты</button></div></div>`;
  };
  el.innerHTML = `<div class="head"><div><h1>SmartShell</h1><p class="sub">Клубы, которыми управляет программа. Можно подключить несколько клубов, в том числе с разных аккаунтов.</p></div>
      <button class="btn primary" id="c-add">${icon("plus")}Добавить клуб</button></div>
    ${clubs.length ? `<div class="grid g3">${clubs.map(card).join("")}</div>`
      : `<div class="card empty">${icon("monitor")}<h2>Клуб не подключён</h2><p>Войдите с логином и паролем от billing.smartshell.gg — программа сама найдёт ваши клубы.</p>
         <button class="btn primary" onclick="addClubDialog()">${icon("plus")}Добавить клуб</button></div>`}
    <div class="docs" style="margin:16px 0">Используйте логин и пароль администратора или владельца от <a href="https://billing.smartshell.gg" target="_blank">billing.smartshell.gg</a>.
      Рекомендуем создать для программы отдельного сотрудника. Пароли хранятся зашифрованными средствами Windows.
      Лимит SmartShell API — не более 20 запросов в минуту на клуб — программа соблюдает сама.</div>
    <div class="card"><h2>Хосты для приставок</h2>
      ${vh.length ? `<div class="table-wrap"><table><thead><tr><th>Хост</th>${multiClub() ? "<th>Клуб</th>" : ""}<th>ID</th><th></th></tr></thead><tbody>${vh.map(v => `<tr><td><b>${esc(v.alias)}</b></td>
        ${multiClub() ? `<td>${esc(clubName(v.club_id) || "—")}</td>` : ""}<td class="muted">${v.host_id}</td>
        <td style="text-align:right"><button class="btn sm danger" data-vdel="${v.host_id}" data-vclub="${esc(v.club_id || "")}">${icon("trash")}Забыть</button></td></tr>`).join("")}</tbody></table></div>`
        : `<p class="muted">Нет хостов, созданных программой. Их можно создать в разделе «Хосты» → «Добавить приставку».</p>`}
      <p class="small muted">Программа держит эти хосты «в сети» на карте клуба. Если вы использовали старый PHP-скрипт — удалите старые хосты на карте клуба и создайте их здесь заново.</p></div>`;
  hydrateIcons(el);
  $("#c-add").onclick = () => addClubDialog();
  $$("[data-cedit]", el).forEach(b => b.onclick = () => editClubDialog(clubs.find(c => c.id === b.dataset.cedit)));
  $$("[data-ctest]", el).forEach(b => b.onclick = e => busy(e.currentTarget, async () => {
    const r = await api("/api/smartshell/test", { id: b.dataset.ctest }); toast(r.message, "ok");
  }).catch(() => {}));
  $$("[data-chosts]", el).forEach(b => b.onclick = () => { hostsView.club = b.dataset.chosts; go("bindings"); });
  $$("[data-vdel]", el).forEach(b => b.onclick = async () => {
    if (!(await confirmBox("Программа перестанет поддерживать этот хост в сети. Сам хост на карте клуба удалите в SmartShell.", "Забыть"))) return;
    await api("/api/hosts/virtual/delete", { host_id: +b.dataset.vdel, club_id: b.dataset.vclub }); render();
  });
};

// Поиск клубов по логину и паролю (общий для «Добавить клуб» и мастера настройки)
function clubFinderHTML() {
  return `<div class="form"><label class="f"><span>Логин (телефон) <b>*</b></span><input id="cf-login" placeholder="79001234567" autocomplete="off"></label>
      <label class="f"><span>Пароль <b>*</b></span><input id="cf-pass" type="text" data-secret autocomplete="off" spellcheck="false"></label></div>
    <div class="row" style="margin-top:12px"><button class="btn" type="button" id="cf-find">${icon("search")}Найти клубы</button>
      <span class="small muted">клубы загружаются по логину и паролю — ID вводить не нужно</span></div>
    <div id="cf-res"></div><div id="cf-list" class="stack" style="gap:8px;margin-top:10px"></div>
    <details class="small" style="margin-top:12px"><summary class="muted">Ввести ID клуба вручную</summary>
      <input id="cf-cid" placeholder="например 1234" style="margin-top:8px;max-width:220px"></details>`;
}
function bindClubFinder(root) {
  let found = [];
  const res = (ok, msg) => { $("#cf-res", root).innerHTML = `<div class="result ${ok ? "ok" : "err"}">${esc(msg)}</div>`; };
  const creds = () => ({ login: $("#cf-login", root).value.trim(), password: $("#cf-pass", root).value });
  const find = async () => {
    const c = creds();
    if (!c.login || !c.password) { res(false, "Введите логин и пароль"); throw new Error("Введите логин и пароль SmartShell"); }
    try {
      found = (await api("/api/smartshell/clubs", c)).clubs;
    } catch (e) { found = []; $("#cf-list", root).innerHTML = ""; res(false, e.message); throw e; }
    $("#cf-list", root).innerHTML = found.map((k, i) => sw(`cf-c${i}`, !k.added,
      `<b>${esc(k.name)}</b>${k.address ? ` <span class="muted">— ${esc(k.address)}</span>` : ""}${k.added ? ' <span class="tag">уже добавлен</span>' : ""}`,
      k.added ? "disabled" : "")).join("");
    const fresh = found.filter(k => !k.added).length;
    res(true, !fresh ? `Все клубы этого аккаунта (${found.length}) уже добавлены` : found.length > 1 ? `Найдено клубов: ${found.length}. Отметьте, какими управлять` : `Найден клуб «${found[0].name}»`);
  };
  $("#cf-find", root).onclick = e => busy(e.currentTarget, find).catch(() => {});
  $("#cf-pass", root).onkeydown = e => { if (e.key === "Enter") $("#cf-find", root).click(); };
  return {
    /** Добавить отмеченные клубы. Возвращает добавленные клубы. */
    async submit() {
      const c = creds();
      const manual = $("#cf-cid", root).value.trim();
      if (!found.length && !manual) {
        await find();
        // несколько клубов — пусть пользователь сам отметит нужные
        if (found.filter(k => !k.added).length > 1) throw new Error(`Найдено клубов: ${found.length}. Отметьте нужные и нажмите кнопку ещё раз`);
      }
      const items = found.filter((k, i) => !k.added && $(`#cf-c${i}`, root)?.checked).map(k => ({ company_id: String(k.id), name: k.name }));
      if (manual && !items.some(i => i.company_id === manual)) {
        await api("/api/smartshell/test", { ...c, company_id: manual });
        items.push({ company_id: manual, name: "" });
      }
      if (!items.length) throw new Error(found.some(k => !k.added) ? "Отметьте хотя бы один клуб" : "Новых клубов для добавления нет");
      return (await api("/api/clubs/add-many", { ...c, clubs: items })).clubs;
    },
  };
}

function addClubDialog(after) {
  const m = modal({ title: "Добавить клуб SmartShell", narrow: true, body: `<p class="muted" style="margin-top:0">Введите логин и пароль от billing.smartshell.gg —
      покажем все клубы этого аккаунта. Клубы с другими логинами добавьте так же, ещё раз.</p>${clubFinderHTML()}`,
    foot: `<button class="btn" data-x>Отмена</button><button class="btn primary" id="ac-ok">${icon("check")}Добавить</button>` });
  $("[data-x]", m.el).onclick = m.close;
  const finder = bindClubFinder(m.el);
  $("#ac-ok", m.el).onclick = e => busy(e.currentTarget, async () => {
    const added = await finder.submit();
    toast(added.length > 1 ? `Добавлены клубы: ${added.map(c => c.name).join(", ")}` : `Клуб «${added[0].name}» добавлен`, "ok");
    m.close(); await loadConfig(); setTimeout(pollState, 1500);
    if (after) after(added); else if (S.page === "smartshell") render();
  }).catch(() => {});
  setTimeout(() => $("#cf-login", m.el)?.focus(), 50);
}

function editClubDialog(c) {
  const m = modal({ title: esc(c.name), narrow: true, body: `<div class="stack">
      <label class="f"><span>Название (для вас)</span><input id="ec-name" value="${esc(c.name)}"></label>
      <label class="f"><span>Логин (телефон)</span><input id="ec-login" value="${esc(c.login)}" autocomplete="off"></label>
      <label class="f"><span>Пароль</span><input id="ec-pass" type="text" data-secret autocomplete="off" spellcheck="false" value="${esc(c.password)}"></label>
      <div class="small muted">ID клуба в SmartShell: <b>${esc(c.company_id)}</b></div>
      ${sw("ec-enabled", c.enabled !== false, "Управлять устройствами этого клуба")}
      <div id="ec-res"></div></div>`,
    foot: `<button class="btn danger" id="ec-del" style="margin-right:auto">${icon("trash")}Удалить</button><button class="btn" id="ec-test">${icon("check")}Проверить</button>
      <button class="btn primary" id="ec-ok">${icon("check")}Сохранить</button>` });
  const body = () => ({ id: c.id, name: $("#ec-name", m.el).value.trim(), login: $("#ec-login", m.el).value.trim(),
    password: $("#ec-pass", m.el).value, enabled: $("#ec-enabled", m.el).checked });
  $("#ec-test", m.el).onclick = e => busy(e.currentTarget, async () => {
    try { const r = await api("/api/smartshell/test", body()); $("#ec-res", m.el).innerHTML = `<div class="result ok">${esc(r.message)}</div>`; }
    catch (err) { $("#ec-res", m.el).innerHTML = `<div class="result err">${esc(err.message)}</div>`; }
  }).catch(() => {});
  $("#ec-ok", m.el).onclick = e => busy(e.currentTarget, async () => {
    await api("/api/clubs", body()); toast("Сохранено", "ok"); m.close(); await loadConfig(); render();
  }).catch(() => {});
  $("#ec-del", m.el).onclick = async () => {
    const nb = S.config.bindings.filter(b => b.club_id === c.id).length;
    if (!(await confirmBox(`Удалить клуб «${esc(c.name)}» из программы?${nb ? ` Будут удалены и его привязки (${nb}).` : ""} В самом SmartShell ничего не изменится.`, "Удалить"))) return;
    await api("/api/clubs/delete", { id: c.id }); toast("Клуб удалён"); m.close(); await loadConfig(); render();
  };
}

// ================================================================= LOGS
const LOG_LEVELS = { DEBUG: 10, INFO: 20, SUCCESS: 25, WARNING: 30, ERROR: 40 };
const LOG_CATS = { system: "Система", engine: "Синхронизация", smartshell: "SmartShell", devices: "Устройства", config: "Настройки", diag: "Диагностика", notify: "Уведомления" };
const LOG_LV_RU = { DEBUG: "ОТЛАДКА", INFO: "ИНФО", SUCCESS: "УСПЕХ", WARNING: "ВНИМАНИЕ", ERROR: "ОШИБКА" };
const logFilter = { level: "INFO", cat: "", q: "", auto: true };

PAGES.logs = async el => {
  S.unseenErrors = 0; $("#log-badge").hidden = true;
  el.innerHTML = `<div class="head"><div><h1>Журнал</h1><p class="sub">Все события программы. Файлы журнала хранятся 5 последних частей по 2 МБ.</p></div>
    <div class="row"><button class="btn" id="l-folder">${icon("folder")}Папка журналов</button><button class="btn" id="l-export">${icon("download")}Сохранить</button></div></div>
    <div class="row" style="margin-bottom:12px">
      <select id="l-level" style="width:auto"><option value="DEBUG">Все, включая отладку</option><option value="INFO">Информация и выше</option><option value="WARNING">Предупреждения и ошибки</option><option value="ERROR">Только ошибки</option></select>
      <select id="l-cat" style="width:auto"><option value="">Все разделы</option>${Object.entries(LOG_CATS).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select>
      <input id="l-q" placeholder="Поиск…" style="max-width:260px">
      <span class="grow"></span>${sw("l-auto", logFilter.auto, "Автопрокрутка")}<button class="btn ghost sm" id="l-clear">Очистить экран</button></div>
    <div class="log" id="log"></div>`;
  $("#l-level").value = logFilter.level; $("#l-cat").value = logFilter.cat; $("#l-q").value = logFilter.q;
  const redraw = () => { $("#log").innerHTML = ""; appendLogs(S.logs); };
  $("#l-level").onchange = e => { logFilter.level = e.target.value; redraw(); };
  $("#l-cat").onchange = e => { logFilter.cat = e.target.value; redraw(); };
  $("#l-q").oninput = e => { logFilter.q = e.target.value.toLowerCase(); redraw(); };
  $("#l-auto").onchange = e => { logFilter.auto = e.target.checked; };
  $("#l-clear").onclick = () => { S.logs = []; redraw(); };
  $("#l-folder").onclick = () => api("/api/logs/open", {});
  $("#l-export").onclick = () => {
    const text = S.logs.map(i => `${fmtDateTime(i.ts)} [${i.level}] [${i.cat}] ${i.msg}`).join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob(["﻿" + text], { type: "text/plain;charset=utf-8" }));
    a.download = `smartshell-bridge-${new Date().toISOString().slice(0, 10)}.log`; a.click();
  };
  redraw();
};

function appendLogs(items) {
  const box = $("#log");
  if (!box) return;
  const min = LOG_LEVELS[logFilter.level] || 0;
  const html = items.filter(i => (LOG_LEVELS[i.level] || 20) >= min && (!logFilter.cat || i.cat === logFilter.cat) && (!logFilter.q || i.msg.toLowerCase().includes(logFilter.q)))
    .map(i => `<div class="log-row"><span class="muted">${fmtDateTime(i.ts)}</span><span class="lv ${i.level}">${LOG_LV_RU[i.level] || i.level}</span><span class="muted">${LOG_CATS[i.cat] || esc(i.cat)}</span><span class="msg">${esc(i.msg)}</span></div>`).join("");
  if (!html && !box.children.length) { box.innerHTML = `<div class="empty">Записей нет</div>`; return; }
  if (box.querySelector(".empty")) box.innerHTML = "";
  box.insertAdjacentHTML("beforeend", html);
  if (logFilter.auto) box.scrollTop = box.scrollHeight;
}

// ================================================================= DIAGNOSTICS
PAGES.diag = async el => {
  const st = S.state || {};
  el.innerHTML = `<div class="head"><div><h1>Диагностика</h1><p class="sub">Полная проверка: интернет, SmartShell, каждая система умного дома и каждая привязка</p></div>
    <button class="btn primary" id="dg-run">${icon("play")}Запустить проверку</button></div>
    <div class="grid" style="grid-template-columns: 2fr 1fr; align-items:start">
      <div class="card" id="dg-res"><div class="empty">${icon("check")}<p>Нажмите «Запустить проверку». Это займёт несколько секунд.</p></div></div>
      <div class="card"><h2>О системе</h2><div class="stack small">
        <div><span class="muted">Версия:</span> ${esc(st.version)}</div>
        <div><span class="muted">Работает:</span> ${fmtDur(st.uptime || 0)}</div>
        <div><span class="muted">Циклов синхронизации:</span> ${st.cycles}</div>
        <div><span class="muted">Последний цикл:</span> ${st.last_cycle_ms} мс</div>
        <div><span class="muted">Автозапуск:</span> ${st.autostart ? "включён" : "выключен"}</div>
        <div><span class="muted">Уведомления Telegram:</span> ${st.telegram ? "настроены" : "не настроены"}</div>
        <div><span class="muted">Папка данных:</span><div class="mono" style="word-break:break-all">${esc(S.config?.data_dir || "")}</div></div>
      </div></div></div>`;
  $("#dg-run").onclick = e => busy(e.currentTarget, async () => {
    $("#dg-res").innerHTML = `<div class="empty">Выполняется проверка…</div>`;
    const r = await api("/api/selftest", {});
    const ok = r.checks.filter(c => c.ok).length;
    $("#dg-res").innerHTML = `<h2>${ok === r.checks.length ? "Все проверки пройдены" : `Пройдено ${ok} из ${r.checks.length}`}</h2>` +
      r.checks.map(c => `<div class="check"><div class="ic ${c.ok ? "ok" : "err"}">${icon(c.ok ? "check" : "x")}</div><div class="grow"><div style="font-weight:600">${esc(c.name)}</div>
        <div class="small ${c.ok ? "muted" : ""}" style="${c.ok ? "" : "color:var(--err)"}">${esc(c.message)}</div></div><span class="small muted">${c.ms} мс</span></div>`).join("");
  });
};

// ================================================================= SETTINGS
PAGES.settings = async el => {
  await loadConfig();
  const g = S.config.general, n = S.config.notify;
  el.innerHTML = `<div class="head"><div><h1>Настройки</h1><p class="sub">Работа программы, запуск и уведомления</p></div></div>
    <div class="stack">
    <div class="card"><h2>Синхронизация</h2><div class="form">
      <label class="f"><span>Интервал проверки, секунд</span><input type="number" min="5" max="600" id="g-poll" value="${g.poll_interval}"><span class="help">Рекомендуется 10–15. Минимум 5.</span></label>
      <label class="f"><span>Лимит запросов к SmartShell в минуту</span><input type="number" min="3" max="19" id="g-rpm" value="${g.max_billing_rpm}"><span class="help">API SmartShell разрешает до 20 запросов/мин на клуб</span></label>
      <label class="f"><span>Интервал «пульса» хостов-приставок, секунд</span><input type="number" min="15" max="300" id="g-ka" value="${g.keepalive_interval}"></label>
      <div class="f full">${sw("g-enforce", g.enforce_state, "Поддерживать состояние: если устройство переключили вручную — вернуть как должно быть")}</div>
      <div class="f full">${sw("g-dry", g.dry_run, "Тестовый режим: только писать в журнал, что было бы сделано, не переключая устройства")}</div>
    </div></div>
    <div class="card"><h2>Запуск</h2><div class="form">
      <div class="f full">${sw("g-auto", S.state?.autostart ?? g.autostart, "Запускать вместе с Windows")}</div>
      <div class="f full">${sw("g-min", g.start_minimized, "При автозапуске — сразу сворачивать в трей")}</div>
    </div></div>
    <div class="card"><h2>Доступ к панели</h2><div class="form">
      <label class="f"><span>Порт панели</span><input type="number" id="g-port" value="${g.web_port}"></label>
      <label class="f"><span>PIN-код для доступа по сети</span><input type="text" data-secret autocomplete="off" spellcheck="false" id="g-pin" value="${esc(g.lan_pin)}"></label>
      <div class="f full">${sw("g-lan", g.allow_lan, "Разрешить открывать панель с других компьютеров/телефона в сети клуба (требуется PIN-код)")}</div>
    </div><div class="small muted" style="margin-top:8px">Изменение порта и доступа по сети применяется после перезапуска программы.</div></div>
    <div class="row"><button class="btn primary" id="g-save">${icon("check")}Сохранить настройки</button></div>
    <div class="card"><h2>Уведомления в Telegram</h2><div class="form">
      <label class="f"><span>Токен бота</span><input type="text" data-secret autocomplete="off" spellcheck="false" id="n-token" value="${esc(n.telegram_token)}" placeholder="123456:ABC..."><span class="help">Создайте бота у @BotFather</span></label>
      <label class="f"><span>Chat ID</span><input id="n-chat" value="${esc(n.telegram_chat_id)}" placeholder="123456789"><span class="help">Узнать можно у @userinfobot (для группы — с минусом)</span></label>
      <div class="f full">${sw("n-err", n.on_errors, "Сообщать о сбоях и восстановлении")}</div>
      <div class="f full">${sw("n-sw", n.on_switch, "Сообщать о каждом включении/выключении устройств")}</div>
    </div><div class="row" style="margin-top:14px"><button class="btn" id="n-test">${icon("send")}Отправить тест</button><button class="btn primary" id="n-save">${icon("check")}Сохранить</button></div></div>
    <div class="card"><h2>Мастер настройки</h2><p class="muted">Пошаговая настройка с нуля: SmartShell → умный дом → привязки.</p><button class="btn" onclick="wizard()">${icon("wand")}Открыть мастер</button></div>
    </div>`;
  if (g.allow_lan && g.lan_pin === "") toast("Задайте PIN-код для доступа по сети", "err");
  $("#g-save").onclick = e => busy(e.currentTarget, async () => {
    if ($("#g-lan").checked && !$("#g-pin").value) throw new Error("Для доступа по сети задайте PIN-код");
    const r = await api("/api/general", { poll_interval: +$("#g-poll").value, max_billing_rpm: +$("#g-rpm").value, keepalive_interval: +$("#g-ka").value,
      enforce_state: $("#g-enforce").checked, dry_run: $("#g-dry").checked, autostart: $("#g-auto").checked, start_minimized: $("#g-min").checked,
      web_port: +$("#g-port").value, allow_lan: $("#g-lan").checked, lan_pin: $("#g-pin").value });
    toast(r.restart_needed ? "Сохранено. Перезапустите программу, чтобы применить настройки доступа." : "Настройки сохранены", "ok");
    pollState();
  }).catch(() => {});
  const notifyBody = () => ({ telegram_token: $("#n-token").value, telegram_chat_id: $("#n-chat").value, on_errors: $("#n-err").checked, on_switch: $("#n-sw").checked });
  $("#n-save").onclick = e => busy(e.currentTarget, async () => { await api("/api/notify", notifyBody()); toast("Сохранено", "ok"); }).catch(() => {});
  $("#n-test").onclick = e => busy(e.currentTarget, async () => { await api("/api/notify", notifyBody()); const r = await api("/api/notify/test", {}); toast(r.message, "ok"); }).catch(() => {});
};

// ================================================================= WIZARD
async function wizard(step = 1) {
  await loadConfig();
  if (!S.types.length) S.types = (await api("/api/connector-types")).types;
  const steps = `<div class="steps">${[1, 2, 3].map(i => `<div class="step ${i <= step ? "done" : ""}"></div>`).join("")}</div>`;
  const finish = async () => { await api("/api/wizard/done", {}); await pollState(); };
  if (step === 1) {
    const clubs = S.config.clubs || [];
    const m = modal({ title: "Мастер настройки · 1/3 · SmartShell", body: `${steps}
      <p>Добро пожаловать! Программа автоматически включает розетки и устройства умного дома, когда на хосте в SmartShell начинается сеанс, и выключает, когда он заканчивается.</p>
      ${clubs.length ? `<div class="docs">Подключено клубов: ${clubs.length} — ${clubs.map(c => `<b>${esc(c.name)}</b>`).join(", ")}.
          <div class="row" style="margin-top:10px"><button class="btn sm" id="wz-more">${icon("plus")}Добавить ещё клуб</button></div></div>`
        : `<div style="margin-top:14px">${clubFinderHTML()}</div>`}`,
      foot: `<button class="btn ghost" id="wz-skip" style="margin-right:auto">Пропустить мастер</button><button class="btn primary" id="wz-next">Далее</button>`,
      onClose: () => {} });
    const finder = clubs.length ? null : bindClubFinder(m.el);
    const more = $("#wz-more", m.el);
    if (more) more.onclick = () => { m.close(); addClubDialog(() => wizard(1)); };
    $("#wz-skip", m.el).onclick = async () => { m.close(); await finish(); };
    $("#wz-next", m.el).onclick = e => busy(e.currentTarget, async () => {
      if (finder) {
        const added = await finder.submit();
        toast(added.length > 1 ? `Добавлены клубы: ${added.map(c => c.name).join(", ")}` : `Клуб «${added[0].name}» подключён`, "ok");
      }
      m.close(); wizard(2);
    }).catch(() => {});
  } else if (step === 2) {
    const conns = S.config.connectors;
    const m = modal({ title: "Мастер настройки · 2/3 · Умный дом", body: `${steps}
      <p>Выберите систему умного дома, в которой находятся ваши розетки/устройства.</p>
      ${conns.length ? `<div class="docs" style="margin-bottom:12px">Уже подключено: ${conns.map(c => `<b>${esc(c.name)}</b>`).join(", ")}</div>` : ""}
      <div class="type-grid">${S.types.map(t => `<div class="type-card" data-type="${t.type}">${sysIcon(t.type, 36)}<div><div class="t">${esc(t.title)}</div><div class="d">${esc(t.description)}</div></div></div>`).join("")}</div>`,
      foot: `<button class="btn" id="wz-back" style="margin-right:auto">Назад</button>${conns.length ? `<button class="btn primary" id="wz-next">Далее</button>` : ""}` });
    $("#wz-back", m.el).onclick = () => { m.close(); wizard(1); };
    const nx = $("#wz-next", m.el); if (nx) nx.onclick = () => { m.close(); wizard(3); };
    $$("[data-type]", m.el).forEach(c => c.onclick = () => { m.close(); editSystemDialog({ type: c.dataset.type, enabled: true, settings: {} }, () => wizard(3)); });
  } else {
    const m = modal({ title: "Мастер настройки · 3/3 · Привязки", body: `${steps}<div id="wz-b" class="empty">Ищем устройства с такими же названиями, как хосты SmartShell…</div>
      <div class="docs" style="margin-top:16px">${sw("wz-autostart", true, "Запускать программу вместе с Windows (рекомендуется — иначе после перезагрузки ПК устройства не будут управляться)")}</div>`,
      foot: `<button class="btn" id="wz-back" style="margin-right:auto">Назад</button><button class="btn" id="wz-manual">Настрою вручную</button><button class="btn primary" id="wz-done">Готово</button>` });
    let matches = [];
    $("#wz-back", m.el).onclick = () => { m.close(); wizard(2); };
    $("#wz-manual", m.el).onclick = async () => { m.close(); await finish(); go("bindings"); };
    $("#wz-done", m.el).onclick = e => busy(e.currentTarget, async () => {
      const chosen = matches.filter((_, i) => $(`#wzm-${i}`, m.el)?.checked);
      if (chosen.length) await api("/api/bindings", { bindings: [...S.config.bindings, ...chosen] });
      if ($("#wz-autostart", m.el).checked) await api("/api/general", { autostart: true });
      await finish(); m.close(); toast("Настройка завершена! Программа работает в фоне — значок в трее рядом с часами.", "ok"); go("dashboard");
    }).catch(() => {});
    try {
      matches = (await api("/api/bindings/auto-match", {})).matches;
      $("#wz-b", m.el).className = "";
      $("#wz-b", m.el).innerHTML = matches.length ? `<p>Найдены совпадения по названиям. Отметьте нужные:</p><div class="stack" style="gap:8px">${matches.map((x, i) =>
        sw(`wzm-${i}`, true, `<b>${esc(x.host_alias)}</b> → ${esc(x.device_name)} <span class="muted">(${esc(connName(x.connector_id))}${multiClub() ? ` · ${esc(clubName(x.club_id))}` : ""})</span>`)).join("")}</div>`
        : `<p>Совпадений по названиям не найдено.</p><p class="muted">Назовите устройства в умном доме так же, как хосты в SmartShell (например «PS5-1»), или нажмите «Настрою вручную» и выберите пары в таблице.</p>`;
    } catch (e) { $("#wz-b", m.el).innerHTML = `<div class="result err">${esc(e.message)}</div>`; }
  }
}

// ================================================================= theme & init
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  $("#theme-toggle").innerHTML = icon(t === "light" ? "moon" : "sun");
  try { localStorage.setItem("ssb-theme", t); } catch (e) { /* ignore */ }
}

// Внешние ссылки открываем в браузере по умолчанию (через программу),
// а не внутри окна панели. Если программа недоступна — обычным способом.
document.addEventListener("click", e => {
  const a = e.target.closest("a[href]");
  if (!a) return;
  let url;
  try { url = new URL(a.getAttribute("href"), location.href); } catch (err) { return; }
  if (url.origin === location.origin || !/^https?:$/.test(url.protocol)) return;
  e.preventDefault();
  api("/api/open-url", { url: url.href }).catch(() => window.open(url.href, "_blank", "noopener"));
});

function showClosed() {
  $("#closed").hidden = false;
  if (S.quitting) setTimeout(() => window.close(), 600);
}

(function init() {
  let theme = null;
  try { theme = localStorage.getItem("ssb-theme"); } catch (e) { /* ignore */ }
  applyTheme(theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"));
  $("#app-quit").onclick = async () => {
    if (!confirm("Выйти из SmartShell Bridge?\n\nСинхронизация хостов с умным домом остановится до следующего запуска программы.")) return;
    S.quitting = true;
    try { await api("/api/app/quit", {}); } catch (e) { /* уже закрыта */ }
    showClosed();
  };
  $("#closed-close").onclick = () => window.close();
  $("#closed-retry").onclick = () => { S.quitting = false; S.fails = 0; pollState(); };
  $("#theme-toggle").onclick = () => applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
  hydrateIcons();
  $$("#nav a").forEach(a => a.onclick = () => go(a.dataset.page));
  const h = location.hash.slice(1);
  if (PAGES[h]) S.page = h;
  $$("#nav a").forEach(a => a.classList.toggle("active", a.dataset.page === S.page));
  api("/api/connector-types").then(r => { S.types = r.types; }).catch(() => {});
  pollState().then(render);
  pollLogs();
  setInterval(pollState, 2000);
  setInterval(pollLogs, 2000);
  window.addEventListener("beforeunload", e => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });
})();
