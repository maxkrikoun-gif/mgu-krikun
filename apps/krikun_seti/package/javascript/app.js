'use strict';
/**
 * Krikun: сеть — клиент Xray (RU).
 * Экраны: главная (старт/стоп), импорт (носитель + файл), удалить конфиг.
 */
const fs = require('fs');
const netctl = require('./netctl_client.js');

const CONF = '/var/opt/krikun-xray/conf/config.json';
const STATE = '/run/krikun-xray/s/state';

const UI = {
	home: {
		title: 'Сеть',
		start: 'Запустить обход',
		stop: 'Остановить обход',
		import: 'Импорт с USB',
		delete: 'Удалить конфиг с ГУ',
		test: 'Тест: YouTube, Google, IP',
		proxyHint: 'YouT: proxy Store должен быть вкл. Затем Health check.',
	},
	test: {
		title: 'Проверка связи',
		running: 'Проверяем…',
		run: 'Запустить тест',
		stop: 'Остановить тест',
		back: 'Назад',
		order: 'YouTube (3) → Google (3) → внешний IP',
	},
	import: {
		title: 'Импорт',
		pickMedia: 'Выбрать флешку',
		pickFile: 'Выбрать файл',
		confirm: 'Импортировать',
		back: 'Назад',
	},
};

function readStatusLine() {
	let line = '';
	try {
		if (fs.existsSync(STATE)) line = fs.readFileSync(STATE, 'utf8').trim();
	} catch (_) { /* */ }
	if (!line) {
		if (fs.existsSync(CONF)) line = 'Конфиг на ГУ есть. Запустите обход.';
		else line = 'Нет конфига. Импорт: флешка → файл.';
	}
	if (view.proxyOn) line += '\n' + UI.home.proxyHint;
	return line;
}

/** @type {{ screen: string, testRunning?: boolean, testProgress?: string, testResult?: object, proxyOn?: boolean, media?: string, file?: string, mediaList?: object[], fileList?: object[] }} */
const view = { screen: 'home', testRunning: false, proxyOn: false };

function clearImportLists() {
	view.mediaList = null;
	view.fileList = null;
	view.media = undefined;
	view.file = undefined;
}

function onCloseImport() {
	clearImportLists();
	view.screen = 'home';
}

function onOpenImport() {
	view.screen = 'import';
	clearImportLists();
	view.mediaList = netctl.listMedia();
	view.media = view.mediaList[0] && view.mediaList[0].path;
	view.fileList = view.media ? netctl.listJsonOnMount(view.media) : [];
	const hit = view.fileList.find((f) => f.name === 'xray.json');
	view.file = (hit && hit.path) || (view.fileList[0] && view.fileList[0].path);
}

function onSelectMedia(mountPath) {
	view.media = mountPath;
	view.fileList = netctl.listJsonOnMount(mountPath);
	const hit = view.fileList.find((f) => f.name === 'xray.json');
	view.file = (hit && hit.path) || (view.fileList[0] && view.fileList[0].path);
}

function onSelectFile(filePath) {
	view.file = filePath;
}

function onImportConfirm() {
	if (!view.file) return { ok: false, error: 'Файл не выбран' };
	return netctl.importFile(view.file);
}

function onDeleteConfig() {
	return netctl.deleteConfig();
}

function onStart() {
	const r = netctl.startTunnel();
	if (r && r.ok) view.proxyOn = true;
	return r;
}

function onStop() {
	const r = netctl.stopTunnel();
	if (r && r.ok) view.proxyOn = false;
	return r;
}

function onOpenTest() {
	view.screen = 'test';
	view.testResult = null;
	view.testRunning = false;
	view.testProgress = '';
	clearImportLists();
}

function onLeaveTest() {
	view.testResult = null;
	view.testProgress = '';
	view.testRunning = false;
	netctl.releaseUiState();
}

function onRunConnectivityTest() {
	if (view.testRunning || netctl.getActiveTestId()) {
		return { ok: false, error: 'Тест уже выполняется' };
	}
	view.testRunning = true;
	view.testResult = null;
	view.testProgress = UI.test.running;
	netctl.runConnectivityTestAsync((r) => {
		view.testRunning = false;
		view.testProgress = netctl.readTestProgress() || '';
		view.testResult = r;
	});
	return { ok: true, started: true };
}

function onStopConnectivityTest() {
	if (!view.testRunning && !netctl.getActiveTestId()) {
		return { ok: false, error: 'Тест не выполняется' };
	}
	const r = netctl.cancelConnectivityTest();
	view.testProgress = 'Остановка…';
	return r;
}

function readTestProgressLine() {
	if (view.testRunning) {
		const p = netctl.readTestProgress();
		if (p) view.testProgress = p;
	}
	return view.testProgress || '';
}

/** Текст для экрана теста (RU) */
function formatTestResult(r) {
	if (!r) return view.testRunning ? (view.testProgress || UI.test.running) : '';
	if (r.cancelled) {
		const lines = ['Остановлено пользователем.'];
		const y = r.ping_youtube || {};
		const g = r.ping_google || {};
		if (y.detail && y.detail !== 'не выполнялся') {
			lines.push('YouTube: ' + (y.ok === true || y.ok === 'true' ? 'OK' : 'нет') + ' — ' + y.detail);
		}
		if (g.detail && g.detail !== 'не выполнялся') {
			lines.push('Google: ' + (g.ok === true || g.ok === 'true' ? 'OK' : 'нет') + ' — ' + g.detail);
		}
		return lines.join('\n');
	}
	if (r.ok === false) {
		return (r && r.error) ? String(r.error) : 'Ошибка теста';
	}
	const lines = [];
	const g = r.ping_google || {};
	const y = r.ping_youtube || {};
	lines.push('YouTube: ' + (y.ok ? 'OK' : 'нет') + (y.detail ? ' — ' + y.detail : ''));
	lines.push('Google: ' + (g.ok ? 'OK' : 'нет') + (g.detail ? ' — ' + g.detail : ''));
	lines.push('Внешний IP: ' + (r.external_ip || '—'));
	if (r.ip_via) lines.push('Канал IP: ' + r.ip_via);
	return lines.join('\n');
}

module.exports = {
	UI,
	readStatusLine,
	view,
	onOpenImport,
	onCloseImport,
	onLeaveTest,
	onSelectMedia,
	onSelectFile,
	onImportConfirm,
	onDeleteConfig,
	onStart,
	onStop,
	onOpenTest,
	onRunConnectivityTest,
	onStopConnectivityTest,
	readTestProgressLine,
	formatTestResult,
};

const mgu = require("./kit/mgu");

mgu.run({
	async start(ctx) {
		const { ui, log } = ctx;
		let dirty = true;
		let msg = '';

		const show = (name) => {
			ui.open(name);
			dirty = true;
		};

		const redraw = () => {
			dirty = true;
		};

		ui.onClick('BTN_EXIT', () => {
			if (ctx.exitApp) ctx.exitApp(() => onStop());
		});

		ui.onClick('BTN_PAGE', () => {
			const top = ui.topScreen();
			if (top === 'MAIN') {
				onOpenImport();
				show('IMPORT');
			} else {
				if (top === 'TEST') onLeaveTest();
				if (top === 'IMPORT') onCloseImport();
				view.screen = 'home';
				show('MAIN');
			}
			redraw();
		});

		ui.onClick('BTN_SETTINGS', () => {
			const top = ui.topScreen();
			if (top === 'MAIN') {
				onOpenTest();
				show('TEST');
			} else if (top === 'TEST') {
				const r = onRunConnectivityTest();
				if (r && !r.ok && r.error) msg = r.error;
			} else if (top === 'IMPORT') {
				const r = onImportConfirm();
				if (r && r.ok) {
					msg = 'Конфиг импортирован.';
					onCloseImport();
					show('MAIN');
				} else msg = (r && r.error) ? r.error : 'Импорт не выполнен';
			}
			redraw();
		});

		ui.onClick('BTN_CANCEL', () => {
			if (ui.topScreen() === 'TEST') {
				onStopConnectivityTest();
				redraw();
			}
		});

		const draw = async (screen) => {
			if (!dirty) return;
			const cv = ctx.canvas(1200, 400);
			cv.fillRect(0, 0, cv.w, cv.h, '#1a1a1a');
			let title = UI.home.title;
			let body = readStatusLine();
			if (screen === 'TEST') {
				title = UI.test.title;
				body = formatTestResult(view.testResult) || view.testProgress || UI.test.order;
			} else if (screen === 'IMPORT') {
				title = UI.import.title;
				body = (view.media ? 'Носитель: ' + view.media : 'Выберите носитель') + '\n'
					+ (view.file ? 'Файл: ' + view.file : 'Выберите файл');
			}
			if (msg) body = msg + '\n\n' + body;
			cv.text(title, 40, 48, 32, '#ffffff', { literal: true, font: 'bold' });
			cv.text(body, 40, 100, 24, '#cccccc', { literal: true });
			await ui.image(screen, cv);
			dirty = false;
		};

		['MAIN', 'TEST', 'IMPORT'].forEach((name) => {
			ctx.loop(name, 2, () => (ui.isVisible(name) ? draw(name) : null));
		});

		show('MAIN');
		log.info('krikun_seti started');
	},
});