'use strict';
const net = require('net');

const SOCKET = process.env.FILMIX_CTL_SOCKET || '/run/jap-filmix-d/ctl.sock';
const CONSOLES_URL = process.env.FILMIX_CONSOLES_URL || 'https://filmix.gg/consoles';

class Ctl {
    constructor(path, log) {
        this.path = path || SOCKET;
        this.log = log;
        this.sock = null;
        this.up = false;
        this.buf = '';
        this.closed = false;
        this.handlers = { msg: [], up: [], down: [] };
    }
    on(ev, fn) { this.handlers[ev].push(fn); return this; }
    _emit(ev, a) { this.handlers[ev].forEach((fn) => { try { fn(a); } catch (e) { this.log.error('fx ' + ev, e); } }); }
    connect() {
        if (this.closed) return this;
        const s = this.sock = net.createConnection(this.path);
        s.setEncoding('utf8');
        s.on('connect', () => { this.up = true; this.buf = ''; this.log.info('jap-filmix-d: connected'); this._emit('up'); });
        s.on('data', (d) => {
            this.buf += d;
            let i;
            while ((i = this.buf.indexOf('\n')) >= 0) {
                const line = this.buf.slice(0, i).trim();
                this.buf = this.buf.slice(i + 1);
                if (!line) continue;
                try { const m = JSON.parse(line); if (m && m.ev) this._emit('msg', m); } catch (e) { /* */ }
            }
        });
        s.on('close', () => {
            const was = this.up;
            this.up = false;
            this.sock = null;
            if (was) this._emit('down');
            if (!this.closed) this.retry = setTimeout(() => this.connect(), 2000);
        });
        return this;
    }
    send(obj) {
        if (!this.up || !this.sock) return false;
        this.sock.write(JSON.stringify(obj) + '\n');
        return true;
    }
    close() {
        this.closed = true;
        clearTimeout(this.retry);
        if (this.sock) this.sock.destroy();
    }
}

class Model {
    constructor(send) {
        this.send = send;
        this.connected = false;
        this.auth = { state: 'unknown', code: null, url: CONSOLES_URL, login: '', tier: 'guest', msg: null };
        this.rev = 0;
    }
    _changed() { this.rev++; }
    onMsg(m) {
        if (m.ev === 'auth') {
            this.auth = {
                state: String(m.state || 'signed_out'),
                code: m.code || null,
                url: m.url || CONSOLES_URL,
                login: m.login || '',
                tier: m.tier || 'guest',
                pro_date: m.pro_date || null,
                msg: m.msg || null,
                expires: m.expires,
            };
            this._changed();
        }
    }
    setConnected(on) {
        this.connected = on;
        if (on) {
            this.send({ cmd: 'hello', app: 'filmix_promax' });
            this.send({ cmd: 'auth_status' });
        } else {
            this.auth = { state: 'unknown', code: null, url: CONSOLES_URL, login: '', tier: 'guest', msg: null };
            this._changed();
        }
    }
    authStart() {
        if (!this.connected) return false;
        return this.send({ cmd: 'auth' });
    }
    signOut() { return this.connected ? this.send({ cmd: 'sign_out' }) : false; }
    refreshAuth() { return this.connected ? this.send({ cmd: 'auth_refresh' }) : false; }
}

module.exports = { Ctl, Model, SOCKET, CONSOLES_URL };