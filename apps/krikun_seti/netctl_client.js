'use strict';
/**
 * Клиент → root: запросы в /run/krikun-xray/requests/<id>.json, ответ в responses/
 * Ограничения под МГУ: один async-тест, без висящих setTimeout, лимит обхода USB.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const REQ_DIR = '/run/krikun-xray/requests';
const RES_DIR = '/run/krikun-xray/responses';
const MEDIA_ROOTS = ['/media', '/run/media'];
const TEST_PROGRESS = '/run/krikun-xray/connectivity-test.progress';
const MAX_JSON_LIST = 50;

/** @type {string|null} */
let activeTestId = null;
/** @type {NodeJS.Timeout|null} */
let activeTestPoll = null;
/** @type {function|null} */
let activeTestOnDone = null;

function clearActiveTestPoll() {
	if (activeTestPoll !== null) {
		clearTimeout(activeTestPoll);
		activeTestPoll = null;
	}
}

function listMedia() {
	const out = [];
	for (const root of MEDIA_ROOTS) {
		try {
			for (const name of fs.readdirSync(root)) {
				const p = path.join(root, name);
				try {
					if (fs.statSync(p).isDirectory()) out.push({ id: name, path: p });
				} catch (_) { /* skip */ }
			}
		} catch (_) { /* нет каталога */ }
	}
	return out;
}

function listJsonOnMount(mountPath) {
	const found = [];
	const walk = (dir, depth) => {
		if (depth > 4 || found.length >= MAX_JSON_LIST) return;
		let names;
		try { names = fs.readdirSync(dir); } catch (_) { return; }
		for (const n of names) {
			if (found.length >= MAX_JSON_LIST) break;
			if (n.startsWith('.')) continue;
			const p = path.join(dir, n);
			let st;
			try { st = fs.statSync(p); } catch (_) { continue; }
			if (st.isDirectory()) walk(p, depth + 1);
			else if (st.isFile() && (n === 'xray.json' || n.endsWith('.json'))) {
				found.push({ name: n, path: p, size: st.size });
			}
		}
	};
	walk(mountPath, 0);
	return found;
}

function writeRequest(op, extra) {
	const id = crypto.randomBytes(8).toString('hex');
	const body = Object.assign({ op }, extra || {});
	fs.mkdirSync(REQ_DIR, { recursive: true });
	fs.writeFileSync(path.join(REQ_DIR, `${id}.json`), JSON.stringify(body));
	return id;
}

function yieldMs(ms) {
	const end = Date.now() + ms;
	while (Date.now() < end) { /* короткая пауза без spawn */ }
}

function waitResponse(id, timeoutMs, pollMs) {
	const resPath = path.join(RES_DIR, `${id}.json`);
	const t0 = Date.now();
	const step = pollMs || 400;
	while (Date.now() - t0 < (timeoutMs || 15000)) {
		try {
			if (fs.existsSync(resPath)) {
				const raw = fs.readFileSync(resPath, 'utf8');
				fs.unlinkSync(resPath);
				return JSON.parse(raw);
			}
		} catch (_) { /* retry */ }
		yieldMs(step);
	}
	return { ok: false, error: 'timeout' };
}

function importFile(filePath) {
	const id = writeRequest('import', { path: filePath });
	return waitResponse(id);
}

function deleteConfig() {
	const id = writeRequest('delete_config');
	return waitResponse(id);
}

function startTunnel() {
	const id = writeRequest('start');
	return waitResponse(id);
}

function stopTunnel() {
	const id = writeRequest('stop');
	return waitResponse(id);
}

function readTestProgress() {
	try {
		if (fs.existsSync(TEST_PROGRESS)) {
			return fs.readFileSync(TEST_PROGRESS, 'utf8').trim();
		}
	} catch (_) { /* */ }
	return '';
}

function finishActiveTest(r) {
	clearActiveTestPoll();
	const cb = activeTestOnDone;
	activeTestId = null;
	activeTestOnDone = null;
	if (typeof cb === 'function') cb(r);
}

function runConnectivityTest() {
	if (activeTestId || activeTestPoll) {
		return { ok: false, error: 'тест уже выполняется' };
	}
	const id = writeRequest('connectivity_test');
	return waitResponse(id, 45000);
}

function runConnectivityTestAsync(onDone) {
	if (activeTestId || activeTestPoll) {
		if (typeof onDone === 'function') {
			onDone({ ok: false, error: 'тест уже выполняется' });
		}
		return activeTestId;
	}
	clearActiveTestPoll();
	activeTestOnDone = onDone;
	activeTestId = writeRequest('connectivity_test');
	const id = activeTestId;
	const resPath = path.join(RES_DIR, `${id}.json`);
	const t0 = Date.now();
	const timeoutMs = 45000;

	const step = () => {
		activeTestPoll = null;
		if (!activeTestId || activeTestId !== id) return;

		if (Date.now() - t0 > timeoutMs) {
			finishActiveTest({ ok: false, error: 'timeout' });
			return;
		}
		try {
			if (fs.existsSync(resPath)) {
				const raw = fs.readFileSync(resPath, 'utf8');
				fs.unlinkSync(resPath);
				finishActiveTest(JSON.parse(raw));
				return;
			}
		} catch (_) { /* retry */ }
		activeTestPoll = setTimeout(step, 400);
	};
	activeTestPoll = setTimeout(step, 0);
	return id;
}

function cancelConnectivityTest() {
	clearActiveTestPoll();
	const extra = activeTestId ? { reply_to: activeTestId } : {};
	writeRequest('cancel_connectivity_test', extra);
	return { ok: true, sent: true };
}

function getActiveTestId() {
	return activeTestId;
}

function releaseUiState() {
	clearActiveTestPoll();
	activeTestId = null;
	activeTestOnDone = null;
}

module.exports = {
	listMedia,
	listJsonOnMount,
	importFile,
	deleteConfig,
	startTunnel,
	stopTunnel,
	runConnectivityTest,
	runConnectivityTestAsync,
	cancelConnectivityTest,
	readTestProgress,
	getActiveTestId,
	releaseUiState,
	MAX_JSON_LIST,
};