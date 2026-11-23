'use strict';
/**
 * Параметры Filmix API v2 (mobile / FilmixProMax / Lampa filmix plugin).
 * Сеть: proxy Store (updater.local.conf) — та же строка, что пишет krikun-xray при «Запустить обход».
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const tls = require('tls');
const proxy = require('./proxy.js');

const DEFAULT_HOST = process.env.FILMIX_API_HOST || 'http://filmixapp.cyou';
const CONSOLES_URL = process.env.FILMIX_CONSOLES_URL || 'https://filmix.gg/consoles';

const DEV = {
    apk: process.env.FILMIX_DEV_APK || '2.2.13',
    name: process.env.FILMIX_DEV_NAME || 'BMW_MGU',
    os: process.env.FILMIX_DEV_OS || '12',
    vendor: process.env.FILMIX_DEV_VENDOR || 'BMW',
    lang: 'ru_RU',
};

function uid16() {
    const a = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let s = '';
    for (let i = 0; i < 16; i++) s += a[crypto.randomInt(a.length)];
    return s;
}

function loadDeviceId(stateDir) {
    const f = path.join(stateDir, 'device_id');
    try {
        const s = fs.readFileSync(f, 'utf8').trim();
        if (s.length >= 8) return s.slice(0, 32);
    } catch (e) { /* none */ }
    const id = uid16();
    try {
        fs.mkdirSync(stateDir, { recursive: true, mode: 0o700 });
        fs.writeFileSync(f, id + '\n', { mode: 0o600 });
    } catch (e) { /* best effort */ }
    return id;
}

function devQuery(deviceId, token) {
    const q = [
        'app_lang=' + encodeURIComponent(DEV.lang),
        'user_dev_apk=' + encodeURIComponent(DEV.apk),
        'user_dev_id=' + encodeURIComponent(deviceId),
        'user_dev_name=' + encodeURIComponent(DEV.name),
        'user_dev_os=' + encodeURIComponent(DEV.os),
        'user_dev_vendor=' + encodeURIComponent(DEV.vendor),
        'user_dev_token=' + encodeURIComponent(token || ''),
    ];
    return q.join('&');
}

function apiUrl(base, segment, query) {
    const b = base.replace(/\/+$/, '');
    const seg = String(segment || '').replace(/^\/+/, '');
    return b + '/api/v2/' + seg + (query ? '?' + String(query).replace(/^[?&]/, '') : '');
}

/** Как Store/RideTube: нет строки proxy → прямой выход; есть → SOCKS (обычно 127.0.0.1:1080 при работающем Xray). */
function readProxyVia() {
    const s = proxy.readSetting(proxy.STORE_CONF);
    if (!s) return null;
    if (s.error) return { error: s.error };
    return s.proxy;
}

function proxyStatus() {
    const s = proxy.readSetting(proxy.STORE_CONF);
    if (!s) return { mode: 'direct' };
    if (s.error) return { mode: 'error', msg: s.error };
    return { mode: 'store', via: s.proxy.label };
}

function httpGet(url, timeoutMs) {
    const via = readProxyVia();
    if (via && via.error) return Promise.reject(new Error(via.error));

    return new Promise((resolve, reject) => {
        const u = new URL(url);
        const isHttps = u.protocol === 'https:';
        const lib = isHttps ? https : http;
        const port = Number(u.port) || (isHttps ? 443 : 80);
        const ms = timeoutMs || 15000;
        let done = false;
        let req = null;

        const fail = (e) => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            reject(e);
        };

        const start = (createConnection) => {
            const o = {
                hostname: u.hostname,
                port,
                path: u.pathname + u.search,
                method: 'GET',
                timeout: ms,
            };
            if (createConnection) {
                Object.assign(o, {
                    port,
                    defaultPort: port,
                    createConnection,
                });
            }
            req = lib.get(o, (res) => {
                let body = '';
                res.on('data', (d) => { body += d; });
                res.on('end', () => {
                    if (done) return;
                    done = true;
                    clearTimeout(timer);
                    resolve({ status: res.statusCode, body });
                });
            });
            req.on('error', fail);
            req.on('timeout', () => { req.destroy(); fail(new Error('timeout')); });
        };

        const timer = setTimeout(() => {
            fail(new Error('timeout'));
            if (req) req.destroy();
        }, ms);

        if (!via) return start(null);

        proxy.connect(via, u.hostname, port, { timeoutMs: ms }, (e, sock) => {
            if (e) return fail(e);
            if (done) return sock.destroy();
            if (isHttps) {
                start(() => tls.connect({ socket: sock, servername: u.hostname }));
            } else {
                start(() => sock);
            }
        });
    });
}

async function getJson(url, timeoutMs, log) {
    const r = await httpGet(url, timeoutMs);
    let j = null;
    try { j = JSON.parse(r.body); } catch (e) { /* */ }
    return { status: r.status, j, body: r.body };
}

module.exports = {
    DEFAULT_HOST,
    CONSOLES_URL,
    DEV,
    loadDeviceId,
    devQuery,
    apiUrl,
    getJson,
    proxyStatus,
    readProxyVia,
};