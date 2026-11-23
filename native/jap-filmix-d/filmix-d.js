#!/usr/bin/env node
'use strict';
/**
 * jap-filmix-d — демон FilmixProMax на ГУ (пока: auth device-code, далее catalog/play).
 */
const fs = require('fs');
const net = require('net');
const path = require('path');
const { DEFAULT_HOST, loadDeviceId, proxyStatus } = require('./filmix-api');
const { Account } = require('./filmix-auth');

const SOCK = process.env.FILMIX_CTL_SOCKET || '/run/jap-filmix-d/ctl.sock';
const STATE = process.env.FILMIX_STATE_DIR || '/var/opt/jap-filmix-d/state';
const ACCOUNT = path.join(STATE, 'account.json');
const API_HOST = process.env.FILMIX_API_HOST || DEFAULT_HOST;

function logLine(msg) {
    const line = new Date().toISOString() + ' filmix-d: ' + msg + '\n';
    try { fs.appendFileSync(path.join(STATE, 'filmix-d.log'), line); } catch (e) { /* */ }
    try { process.stderr.write(line); } catch (e) { /* */ }
}

function Daemon() {
    this.client = null;
    this.deviceId = loadDeviceId(STATE);
    this.account = new Account({
        accountFile: ACCOUNT,
        apiHost: API_HOST,
        deviceId: this.deviceId,
        log: logLine,
        emit: (o) => this.emit(o),
    });
}

Daemon.prototype.emit = function (o) {
    if (!this.client) return;
    try { this.client.write(JSON.stringify(o) + '\n'); } catch (e) { logLine('emit: ' + e.message); }
};

Daemon.prototype.onLine = function (line) {
    let m;
    try { m = JSON.parse(line); } catch (e) { return this.emit({ ev: 'error', msg: 'bad json' }); }
    if (!m || typeof m.cmd !== 'string') return this.emit({ ev: 'error', msg: 'no cmd' });
    switch (m.cmd) {
    case 'hello':
        const px = proxyStatus();
        return this.emit({ ev: 'hello', caps: ['auth'], app: m.app, api: API_HOST, network: px });
    case 'auth_status':
        return this.emit(this.account.status());
    case 'auth':
        return this.account.start();
    case 'sign_out':
        return this.account.signOut();
    case 'auth_refresh':
        return this.account.refreshProfile();
    case 'status':
        return this.emit(Object.assign({ ev: 'status', state: 'idle' }, this.account.load() ? { signed_in: true } : {}));
    default:
        return this.emit({ ev: 'error', msg: 'unknown cmd ' + m.cmd });
    }
};

Daemon.prototype.onClient = function (c) {
    if (this.client) {
        const old = this.client;
        this.client = null;
        old.destroy();
    }
    this.client = c;
    c.setEncoding('utf8');
    let buf = '';
    c.on('data', (d) => {
        buf += d;
        let i;
        while ((i = buf.indexOf('\n')) >= 0) {
            const line = buf.slice(0, i).trim();
            buf = buf.slice(i + 1);
            if (line) this.onLine(line);
        }
    });
    c.on('close', () => {
        if (this.client === c) this.client = null;
    });
};

function serve(sockPath) {
    try { fs.mkdirSync(path.dirname(sockPath), { recursive: true, mode: 0o755 }); } catch (e) { /* */ }
    try { fs.unlinkSync(sockPath); } catch (e) { /* */ }
    const d = new Daemon();
    const srv = net.createServer((c) => d.onClient(c));
    srv.listen(sockPath, () => {
        try { fs.chmodSync(sockPath, 0o666); } catch (e) { /* */ }
        const px = proxyStatus();
        logLine('listening ' + sockPath + ' network=' + px.mode + (px.via ? ' via ' + px.via : ''));
        d.account.bootstrap().catch((e) => logLine('bootstrap: ' + e.message));
    });
    process.on('SIGTERM', () => { srv.close(); process.exit(0); });
}

if (require.main === module) {
    try { fs.mkdirSync(STATE, { recursive: true, mode: 0o700 }); } catch (e) { /* */ }
    serve(SOCK);
}

module.exports = { Daemon, SOCK };