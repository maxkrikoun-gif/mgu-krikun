'use strict';
/**
 * Привязка устройства Filmix: token_request → код на filmix.gg/consoles → один user_profile.
 * Без фонового опроса: token_request и проверка профиля — при старте демона (или по «Обновить»).
 * Срок жизни кода на клиенте не выдумываем — как Lampa/Lampac, до привязки или «Выйти».
 */
const fs = require('fs');
const path = require('path');
const { devQuery, apiUrl, getJson, CONSOLES_URL } = require('./filmix-api');

function Account(opts) {
    this.opts = opts;
    this.log = opts.log;
    this.emit = opts.emit;
    this.deviceId = opts.deviceId;
    this.apiHost = opts.apiHost;
    this.pendingToken = null;
    this.pendingCode = null;
    this.starting = false;
    this.loadPendingFromDisk();
}

Account.prototype.accountFile = function () { return this.opts.accountFile; };

Account.prototype.pendingFile = function () {
    return path.join(path.dirname(this.accountFile()), 'pending.json');
};

Account.prototype.hasPending = function () {
    return !!(this.pendingToken && this.pendingCode);
};

Account.prototype.loadPendingFromDisk = function () {
    try {
        const p = JSON.parse(fs.readFileSync(this.pendingFile(), 'utf8'));
        if (p && p.token && p.user_code) {
            this.pendingToken = String(p.token);
            this.pendingCode = String(p.user_code);
        }
    } catch (e) { /* no pending */ }
};

Account.prototype.savePending = function () {
    if (!this.hasPending()) return;
    const f = this.pendingFile();
    const dir = path.dirname(f);
    const tmp = f + '.tmp';
    try { fs.mkdirSync(dir, { recursive: true, mode: 0o700 }); } catch (e) { /* */ }
    const out = { token: this.pendingToken, user_code: this.pendingCode };
    fs.writeFileSync(tmp, JSON.stringify(out), { mode: 0o600 });
    fs.renameSync(tmp, f);
};

Account.prototype.clearPending = function () {
    this.pendingToken = null;
    this.pendingCode = null;
    try { fs.unlinkSync(this.pendingFile()); } catch (e) { /* */ }
};

Account.prototype.load = function () {
    try {
        const a = JSON.parse(fs.readFileSync(this.accountFile(), 'utf8'));
        return a && a.token ? a : null;
    } catch (e) { return null; }
};

Account.prototype.save = function (data) {
    const f = this.accountFile();
    const dir = path.dirname(f);
    const tmp = f + '.tmp';
    try { fs.mkdirSync(dir, { recursive: true, mode: 0o700 }); } catch (e) { /* */ }
    const out = Object.assign({ deviceId: this.deviceId }, data);
    fs.writeFileSync(tmp, JSON.stringify(out), { mode: 0o600 });
    fs.renameSync(tmp, f);
};

Account.prototype.profileStatus = function (userData) {
    if (!userData) return { tier: 'guest', login: '' };
    const login = String(userData.login || userData.email || userData.name || '');
    let tier = 'free';
    if (userData.is_pro_plus) tier = 'pro_plus';
    else if (userData.is_pro) tier = 'pro';
    return { tier, login, pro_date: userData.pro_date || userData.pro_plus_date || null };
};

Account.prototype.status = function () {
    const a = this.load();
    if (a && a.token) {
        const st = this.profileStatus(a.user_data);
        return { ev: 'auth', state: 'signed_in', login: st.login, tier: st.tier, pro_date: st.pro_date };
    }
    if (this.hasPending()) {
        return { ev: 'auth', state: 'code', code: this.pendingCode, url: CONSOLES_URL };
    }
    return { ev: 'auth', state: 'signed_out' };
};

Account.prototype.signOut = function () {
    this.clearPending();
    try { fs.unlinkSync(this.accountFile()); } catch (e) { /* */ }
    this.emit(this.status());
    return true;
};

/** Старт демона: один token_request (если нужен) и один user_profile. */
Account.prototype.bootstrap = async function () {
    if (this.load()) {
        await this.refreshProfile();
        return;
    }
    this.loadPendingFromDisk();
    if (this.hasPending()) {
        this.emit(this.status());
        await this.pollOnce();
        return;
    }
    await this.start();
};

/**
 * `auth` из приложения: не дублируем token_request, пока есть сохранённый код (pending.json).
 */
Account.prototype.start = async function () {
    if (this.load()) {
        this.emit(this.status());
        return;
    }
    if (this.hasPending()) {
        this.emit(this.status());
        await this.pollOnce();
        return;
    }
    if (this.starting) return;
    this.starting = true;
    try {
        const q = devQuery(this.deviceId, '');
        const url = apiUrl(this.apiHost, 'token_request', q);
        const r = await getJson(url, 15000, this.log);
        const j = r.j || {};
        if (j.status !== 'ok' || !j.user_code || !j.code) {
            const msg = typeof j === 'string' ? j : (j.message || j.error || ('HTTP ' + r.status));
            this.log('filmix token_request: ' + msg);
            this.emit({ ev: 'auth', state: 'error', msg: String(msg) });
            return;
        }
        this.pendingToken = String(j.code);
        this.pendingCode = String(j.user_code);
        this.savePending();
        this.log('filmix: код ' + this.pendingCode);
        this.emit(this.status());
        await this.pollOnce();
    } catch (e) {
        this.log('filmix auth: ' + e.message);
        this.emit({ ev: 'auth', state: 'error', msg: e.message });
    } finally {
        this.starting = false;
    }
};

Account.prototype.pollOnce = async function () {
    if (!this.pendingToken) return;
    const q = devQuery(this.deviceId, this.pendingToken);
    const url = apiUrl(this.apiHost, 'user_profile', q);
    const r = await getJson(url, 12000, this.log);
    const j = r.j;
    if (!j || !j.user_data) return;
    const token = this.pendingToken;
    this.clearPending();
    this.save({ token, user_data: j.user_data });
    this.log('filmix: привязано, ' + (j.user_data.login || 'ok'));
    this.emit(this.status());
};

/** Одна проверка: pending → pollOnce; иначе обновить профиль уже привязанного. */
Account.prototype.refreshProfile = async function () {
    if (this.hasPending()) {
        await this.pollOnce();
        if (!this.load()) this.emit(this.status());
        return;
    }
    const a = this.load();
    if (!a || !a.token) return this.emit(this.status());
    try {
        const q = devQuery(this.deviceId, a.token);
        const url = apiUrl(this.apiHost, 'user_profile', q);
        const r = await getJson(url, 12000, this.log);
        if (r.j && r.j.user_data) {
            this.save({ token: a.token, user_data: r.j.user_data });
        }
    } catch (e) { this.log('profile: ' + e.message); }
    this.emit(this.status());
};

module.exports = { Account, CONSOLES_URL };