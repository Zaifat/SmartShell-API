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
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
};
function icon(n) { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[n] || ""}</svg>`; }
function hydrateIcons(root = document) { root.querySelectorAll("i[data-i]").forEach(el => { el.innerHTML = icon(el.dataset.i); }); }

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
  unseenErrors: 0, bindingsDraft: null, dirty: false };

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
      <label class="f"><span>PIN-код</span><input type="password" id="pin-in" autofocus></label><div id="pin-err"></div>`,
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
  location.hash = page;
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
  } catch (e) {
    $("#status-pill .dot").className = "dot error";
    $("#status-text").textContent = "Нет связи с программой";
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
        <div class="grow" style="min-width:0"><div class="tile-name">${esc(b.host_alias || "—")}</div><div class="tile-dev">${esc(b.device_name || b.device_id)} · ${esc(connName(b.connector_id))}</div></div></div>
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
        <div class="hint">${st.smartshell.ok === false ? `<span style="color:var(--err)">${esc(st.smartshell.message)}</span>` : "активных сеансов" + (st.smartshell.club ? " · " + esc(st.smartshell.club) : "")}</div></div>
      <div class="card stat"><div class="label">${icon("home").replace("<svg", '<svg width="14"')} Умный дом</div>
        <div class="value">${cOk}<span class="muted" style="font-size:16px"> / ${conns.length}</span></div><div class="hint">систем на связи</div></div>
      <div class="card stat"><div class="label">${icon("link").replace("<svg", '<svg width="14"')} Привязки</div>
        <div class="value">${st.bindings.filter(b => b.state?.actual).length}<span class="muted" style="font-size:16px"> / ${st.bindings.length}</span></div><div class="hint">устройств включено</div></div>
      <div class="card stat"><div class="label">${icon("shield").replace("<svg", '<svg width="14"')} Запросы к SmartShell</div>
        <div class="value">${st.smartshell.rpm_used}<span class="muted" style="font-size:16px"> / 20</span></div><div class="hint">за последнюю минуту (лимит API)</div></div>
    </div>
    ${st.bindings.length ? `<div class="grid g3">${tiles}</div>` :
      `<div class="card empty">${icon("link")}<h2>Пока нет привязок</h2><p>Свяжите хосты SmartShell с розетками или устройствами умного дома.</p>
       <div class="row" style="justify-content:center"><button class="btn primary" onclick="wizard()">Мастер настройки</button><button class="btn" onclick="go('bindings')">Перейти к привязкам</button></div></div>`}`;
  $("#d-run").onclick = e => busy(e.currentTarget, async () => { await api("/api/engine", { action: "run" }); toast("Проверка запущена"); setTimeout(pollState, 1500); });
  $("#d-pause").onclick = e => busy(e.currentTarget, async () => { await api("/api/engine", { action: st.paused ? "resume" : "pause" }); await pollState(); });
  $$("[data-man]", box).forEach(b => b.onclick = e => busy(e.currentTarget, async () => {
    await api("/api/devices/set", { binding_id: b.dataset.man, on: b.dataset.on === "1" });
    toast("Команда выполнена. Автоуправление этим устройством приостановлено на 5 минут", "ok");
    setTimeout(pollState, 800);
  }));
  $$("[data-release]", box).forEach(b => b.onclick = async () => { await api("/api/bindings/release", { binding_id: b.dataset.release }); toast("Автоматическое управление восстановлено"); setTimeout(pollState, 1200); });
}

// ================================================================= BINDINGS
async function ensureHosts(refresh = false) {
  const r = await api("/api/hosts" + (refresh ? "?refresh=1" : ""));
  S.hosts = r.hosts; S.groups = r.groups;
}
async function ensureDevices(cid, refresh = false) {
  if (!cid) return [];
  if (S.devices[cid] && !refresh) return S.devices[cid];
  try { S.devices[cid] = (await api("/api/connectors/devices", { id: cid })).devices; }
  catch (e) { S.devices[cid] = []; S.devices[cid].error = e.message; }
  return S.devices[cid];
}

PAGES.bindings = async el => {
  await loadConfig();
  el.innerHTML = `<div class="head"><div><h1>Привязки</h1><p class="sub">Какое устройство включать, когда на хосте SmartShell идёт сеанс</p></div>
    <div class="row"><button class="btn" id="b-auto">${icon("wand")}Подобрать по названиям</button><button class="btn" id="b-vhost">${icon("plus")}Хост для приставки</button>
    <button class="btn primary" id="b-save">${icon("check")}Сохранить</button></div></div><div id="b-body"><div class="card empty">Загрузка хостов SmartShell и устройств…</div></div>`;
  hydrateIcons(el);
  let hostErr = "";
  try { await ensureHosts(); } catch (e) { hostErr = e.message; S.hosts = S.hosts || []; }
  const conns = S.config.connectors;
  await Promise.all(conns.map(c => ensureDevices(c.id)));
  if (!S.bindingsDraft) S.bindingsDraft = JSON.parse(JSON.stringify(S.config.bindings));
  drawBindings(hostErr);
  $("#b-save").onclick = e => busy(e.currentTarget, saveBindings);
  $("#b-auto").onclick = e => busy(e.currentTarget, autoMatch);
  $("#b-vhost").onclick = virtualHostDialog;
};

function drawBindings(hostErr) {
  const box = $("#b-body");
  const conns = S.config.connectors;
  if (!conns.length) {
    box.innerHTML = `<div class="card empty">${icon("home")}<h2>Сначала добавьте систему умного дома</h2><p>Например, Яндекс Умный дом, Home Assistant или Tuya.</p><button class="btn primary" onclick="go('systems')">Добавить систему</button></div>`;
    return;
  }
  const hostOpts = sel => {
    const groups = {};
    (S.hosts || []).forEach(h => (groups[h.group] = groups[h.group] || []).push(h));
    let html = `<option value="">— выберите хост —</option>`;
    for (const [g, hs] of Object.entries(groups))
      html += `<optgroup label="${esc(g)}">` + hs.map(h => `<option value="${h.id}" ${String(h.id) === String(sel) ? "selected" : ""}>${esc(h.alias)}${h.virtual ? " (приставка)" : ""}</option>`).join("") + "</optgroup>";
    if (sel && !(S.hosts || []).some(h => String(h.id) === String(sel))) html += `<option value="${esc(sel)}" selected>Хост #${esc(sel)} (не найден)</option>`;
    return html;
  };
  const devOpts = (cid, sel, selName) => {
    const devs = S.devices[cid] || [];
    let html = `<option value="">— устройство —</option>` + devs.map(d => `<option value="${esc(d.id)}" ${d.id === sel ? "selected" : ""}>${esc(d.name)}${d.room ? " · " + esc(d.room) : ""}</option>`).join("");
    if (sel && !devs.some(d => d.id === sel)) html += `<option value="${esc(sel)}" selected>${esc(selName || sel)} (нет связи)</option>`;
    return html;
  };
  const rows = S.bindingsDraft.map((b, i) => `<tr data-i="${i}">
      <td>${sw("", b.enabled !== false, "", 'data-f="enabled"')}</td>
      <td><select data-f="host_id">${hostOpts(b.host_id)}</select></td>
      <td><select data-f="connector_id">${conns.map(c => `<option value="${c.id}" ${c.id === b.connector_id ? "selected" : ""}>${esc(c.name)}</option>`).join("")}</select></td>
      <td><select data-f="device_id">${devOpts(b.connector_id, b.device_id, b.device_name)}</select></td>
      <td class="num"><input type="number" min="0" step="10" data-f="off_delay" value="${b.off_delay || 0}" title="Задержка выключения после окончания сеанса, секунд"></td>
      <td><div class="stack" style="gap:4px">${sw("", b.on_in_service, "в сервисном режиме", 'data-f="on_in_service"')}${sw("", b.invert, "инверсия", 'data-f="invert"')}</div></td>
      <td><button class="btn sm danger" data-del="${i}" title="Удалить">${icon("trash")}</button></td></tr>`).join("");
  const devErrors = conns.filter(c => S.devices[c.id]?.error).map(c => `<div class="result err">${esc(c.name)}: ${esc(S.devices[c.id].error)}</div>`).join("");
  box.innerHTML = `${hostErr ? `<div class="result err" style="margin-bottom:12px">SmartShell: ${esc(hostErr)}</div>` : ""}${devErrors}
    <div class="table-wrap"><table><thead><tr><th>Вкл</th><th>Хост SmartShell</th><th>Система</th><th>Устройство</th><th>Задержка, с</th><th>Включать также</th><th></th></tr></thead>
    <tbody>${rows || `<tr><td colspan="7" class="empty">Привязок пока нет. Нажмите «Добавить» или «Подобрать по названиям».</td></tr>`}</tbody></table></div>
    <div class="row" style="margin-top:12px"><button class="btn" id="b-add">${icon("plus")}Добавить привязку</button><button class="btn ghost" id="b-reload">${icon("refresh")}Обновить списки</button>
    <span class="grow"></span><span class="small muted" id="b-dirty">${S.dirty ? "Есть несохранённые изменения" : ""}</span></div>
    <div class="docs" style="margin-top:16px"><b>Как это работает.</b> Когда на хосте начинается сеанс — устройство включается, когда сеанс заканчивается — выключается
    (с необязательной задержкой, например чтобы гость успел сохранить игру). «Сервисный режим» — включать устройство, когда администратор перевёл хост в сервис.
    «Инверсия» — наоборот: включено, пока хост свободен (например, лампа «свободно»).</div>`;
  hydrateIcons(box);
  const mark = () => { S.dirty = true; $("#b-dirty").textContent = "Есть несохранённые изменения"; };
  $$("tbody tr[data-i]", box).forEach(tr => {
    const i = +tr.dataset.i, b = S.bindingsDraft[i];
    $$("[data-f]", tr).forEach(inp => inp.onchange = async () => {
      const f = inp.dataset.f;
      if (inp.type === "checkbox") b[f] = inp.checked;
      else if (f === "off_delay") b[f] = +inp.value || 0;
      else b[f] = inp.value;
      if (f === "host_id") b.host_alias = (S.hosts.find(h => String(h.id) === inp.value) || {}).alias || "";
      if (f === "device_id") b.device_name = (S.devices[b.connector_id] || []).find(d => d.id === inp.value)?.name || "";
      if (f === "connector_id") { b.device_id = ""; b.device_name = ""; await ensureDevices(b.connector_id); drawBindings(); }
      mark();
    });
  });
  $$("[data-del]", box).forEach(btn => btn.onclick = () => { S.bindingsDraft.splice(+btn.dataset.del, 1); S.dirty = true; drawBindings(); });
  $("#b-add").onclick = () => { S.bindingsDraft.push({ enabled: true, connector_id: conns[0].id, off_delay: 0 }); S.dirty = true; drawBindings(); };
  $("#b-reload").onclick = e => busy(e.currentTarget, async () => { await ensureHosts(true); await Promise.all(conns.map(c => ensureDevices(c.id, true))); drawBindings(); toast("Списки обновлены"); });
}

async function saveBindings() {
  const incomplete = S.bindingsDraft.filter(b => !b.host_id || !b.device_id);
  if (incomplete.length && !(await confirmBox(`Незаполненных строк: ${incomplete.length}. Они не будут сохранены. Продолжить?`, "Сохранить"))) return;
  const r = await api("/api/bindings", { bindings: S.bindingsDraft });
  S.dirty = false; S.bindingsDraft = null;
  toast(`Сохранено привязок: ${r.count}`, "ok");
  await loadConfig(); S.bindingsDraft = JSON.parse(JSON.stringify(S.config.bindings)); drawBindings();
}

async function autoMatch() {
  const r = await api("/api/bindings/auto-match", {});
  if (!r.matches.length) { toast("Совпадений названий не найдено. Назовите устройства так же, как хосты в SmartShell, или привяжите вручную."); return; }
  const existing = new Set(S.bindingsDraft.map(b => b.connector_id + "|" + b.device_id));
  const fresh = r.matches.filter(m => !existing.has(m.connector_id + "|" + m.device_id));
  S.bindingsDraft.push(...fresh);
  S.dirty = true; drawBindings();
  toast(`Найдено совпадений: ${fresh.length}. Проверьте и нажмите «Сохранить».`, "ok");
}

function virtualHostDialog() {
  const m = modal({ title: "Хост для приставки", narrow: true, body: `
    <p class="muted">Для приставок (PS5, Xbox, VR и т.п.), на которых нет шелла SmartShell. Программа создаст хост на карте клуба
    и будет поддерживать его «в сети», чтобы администратор мог запускать на нём сеансы.</p>
    <div class="stack"><label class="f"><span>Название хоста <b>*</b></span><input id="vh-alias" placeholder="PS5-1"></label>
    <label class="f"><span>Группа</span><select id="vh-group">${S.groups.map(g => `<option value="${g.id}">${esc(g.title)}</option>`).join("")}</select></label></div>
    <div class="docs" style="margin-top:14px">Удобно назвать хост так же, как розетку в умном доме — тогда привязка подберётся автоматически.</div>`,
    foot: `<button class="btn" data-close2>Отмена</button><button class="btn primary" id="vh-ok">Создать</button>` });
  $("[data-close2]", m.el).onclick = m.close;
  $("#vh-ok").onclick = e => busy(e.currentTarget, async () => {
    const r = await api("/api/hosts/virtual", { alias: $("#vh-alias").value, group_id: +$("#vh-group").value });
    toast(`Хост «${r.host.alias}» создан`, "ok");
    m.close(); await ensureHosts(true); drawBindings();
  });
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
  const type = f.type === "password" ? "password" : f.type === "number" ? "number" : "text";
  return `<label class="f"><span>${esc(f.label)}${req}</span><input type="${type}" data-key="${f.key}" value="${esc(v)}" placeholder="${esc(f.placeholder || "")}" autocomplete="off">${help}</label>`;
}
function tableRow(f, r) {
  return `<tr>${f.columns.map(c => `<td${c.type === "number" ? ' class="num"' : ""}><input type="${c.type === "number" ? "number" : c.type === "password" ? "password" : "text"}" data-col="${c.key}" value="${esc(r[c.key] ?? c.default ?? "")}" placeholder="${esc(c.placeholder || "")}"></td>`).join("")}
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

// ================================================================= SMARTSHELL
PAGES.smartshell = async el => {
  await loadConfig();
  const ss = S.config.smartshell;
  const vh = S.config.virtual_hosts || [];
  el.innerHTML = `<div class="head"><div><h1>SmartShell</h1><p class="sub">Подключение к вашему клубу в SmartShell</p></div></div>
    <div class="stack">
    <div class="card"><h2>Учётная запись</h2>
      <div class="form">${smartshellFields(ss)}</div>
      <div id="ss-result"></div>
      <div class="row" style="margin-top:16px"><button class="btn" id="ss-test">${icon("check")}Проверить подключение</button><button class="btn primary" id="ss-save">${icon("check")}Сохранить</button></div>
      <div class="docs" style="margin-top:16px">Используйте логин и пароль администратора/владельца от <a href="https://billing.smartshell.gg" target="_blank">billing.smartshell.gg</a>.
      Рекомендуем создать для программы отдельного сотрудника. Пароль хранится зашифрованным средствами Windows.
      Программа учитывает лимит SmartShell API — не более 20 запросов в минуту.</div></div>
    <div class="card"><h2>Хосты для приставок</h2>
      ${vh.length ? `<div class="table-wrap"><table><thead><tr><th>Хост</th><th>ID</th><th></th></tr></thead><tbody>${vh.map(v => `<tr><td><b>${esc(v.alias)}</b></td><td class="muted">${v.host_id}</td>
        <td style="text-align:right"><button class="btn sm danger" data-vdel="${v.host_id}">${icon("trash")}Забыть</button></td></tr>`).join("")}</tbody></table></div>`
        : `<p class="muted">Нет хостов, созданных программой. Их можно создать в разделе «Привязки» → «Хост для приставки».</p>`}
      <p class="small muted">Программа держит эти хосты «в сети» на карте клуба. Если вы использовали старый PHP-скрипт — удалите старые хосты на карте клуба и создайте их здесь заново.</p></div>
    </div>`;
  bindSmartshellForm(el, "#ss-result");
  $("#ss-save").onclick = e => busy(e.currentTarget, async () => { await api("/api/smartshell", readSmartshell(el)); toast("Сохранено", "ok"); });
  $$("[data-vdel]", el).forEach(b => b.onclick = async () => {
    if (!(await confirmBox("Программа перестанет поддерживать этот хост в сети. Сам хост на карте клуба удалите в SmartShell.", "Забыть"))) return;
    await api("/api/hosts/virtual/delete", { host_id: +b.dataset.vdel }); render();
  });
};

function smartshellFields(ss) {
  return `<label class="f"><span>Логин (телефон) <b>*</b></span><input id="ss-login" value="${esc(ss.login)}" placeholder="79001234567" autocomplete="off"></label>
    <label class="f"><span>Пароль <b>*</b></span><input id="ss-pass" type="password" value="${esc(ss.password)}" autocomplete="new-password"></label>
    <label class="f"><span>Клуб <b>*</b></span><div class="row" style="flex-wrap:nowrap"><select id="ss-club">${ss.company_id ? `<option value="${esc(ss.company_id)}">${esc(ss.club_name || "Клуб #" + ss.company_id)}</option>` : `<option value="">— нажмите «Найти» —</option>`}</select>
      <button class="btn" type="button" id="ss-find">Найти</button></div><span class="help">Клубы загружаются по логину и паролю — ID вводить не нужно</span></label>
    <label class="f"><span>ID клуба (вручную)</span><input id="ss-cid" value="${esc(ss.company_id)}" placeholder="заполнится автоматически"></label>`;
}
function readSmartshell(root) {
  const sel = $("#ss-club", root);
  const cid = $("#ss-cid", root).value.trim() || sel.value;
  const name = sel.value === cid ? sel.options[sel.selectedIndex]?.text || "" : "";
  return { login: $("#ss-login", root).value.trim(), password: $("#ss-pass", root).value, company_id: cid, club_name: name };
}
function bindSmartshellForm(root, resultSel) {
  const result = (ok, msg) => { $(resultSel, root).innerHTML = `<div class="result ${ok ? "ok" : "err"}">${esc(msg)}</div>`; };
  $("#ss-club", root).onchange = () => { $("#ss-cid", root).value = $("#ss-club", root).value; };
  $("#ss-find", root).onclick = e => busy(e.currentTarget, async () => {
    try {
      const r = await api("/api/smartshell/clubs", readSmartshell(root));
      $("#ss-club", root).innerHTML = r.clubs.map(c => `<option value="${c.id}">${esc(c.name)}${c.address ? " — " + esc(c.address) : ""}</option>`).join("");
      $("#ss-cid", root).value = r.clubs[0].id;
      result(true, `Найдено клубов: ${r.clubs.length}`);
    } catch (err) { result(false, err.message); }
  }).catch(() => {});
  const testBtn = $("#ss-test", root);
  if (testBtn) testBtn.onclick = e => busy(e.currentTarget, async () => {
    try { const r = await api("/api/smartshell/test", readSmartshell(root)); result(true, r.message); } catch (err) { result(false, err.message); }
  }).catch(() => {});
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
      <label class="f"><span>PIN-код для доступа по сети</span><input type="password" id="g-pin" value="${esc(g.lan_pin)}" autocomplete="new-password"></label>
      <div class="f full">${sw("g-lan", g.allow_lan, "Разрешить открывать панель с других компьютеров/телефона в сети клуба (требуется PIN-код)")}</div>
    </div><div class="small muted" style="margin-top:8px">Изменение порта и доступа по сети применяется после перезапуска программы.</div></div>
    <div class="row"><button class="btn primary" id="g-save">${icon("check")}Сохранить настройки</button></div>
    <div class="card"><h2>Уведомления в Telegram</h2><div class="form">
      <label class="f"><span>Токен бота</span><input type="password" id="n-token" value="${esc(n.telegram_token)}" placeholder="123456:ABC..."><span class="help">Создайте бота у @BotFather</span></label>
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
    const m = modal({ title: "Мастер настройки · 1/3 · SmartShell", body: `${steps}
      <p>Добро пожаловать! Программа автоматически включает розетки и устройства умного дома, когда на хосте в SmartShell начинается сеанс, и выключает, когда он заканчивается.</p>
      <div class="form" style="margin-top:14px">${smartshellFields(S.config.smartshell)}</div><div id="wz-res"></div>`,
      foot: `<button class="btn ghost" id="wz-skip" style="margin-right:auto">Пропустить мастер</button><button class="btn primary" id="wz-next">Далее</button>`,
      onClose: () => {} });
    bindSmartshellForm(m.el, "#wz-res");
    $("#wz-skip", m.el).onclick = async () => { m.close(); await finish(); };
    $("#wz-next", m.el).onclick = e => busy(e.currentTarget, async () => {
      const data = readSmartshell(m.el);
      if (!data.company_id) throw new Error("Нажмите «Найти» и выберите клуб");
      const r = await api("/api/smartshell/test", data);
      await api("/api/smartshell", data);
      toast(r.message, "ok");
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
        sw(`wzm-${i}`, true, `<b>${esc(x.host_alias)}</b> → ${esc(x.device_name)} <span class="muted">(${esc(connName(x.connector_id))})</span>`)).join("")}</div>`
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

(function init() {
  let theme = null;
  try { theme = localStorage.getItem("ssb-theme"); } catch (e) { /* ignore */ }
  applyTheme(theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"));
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
