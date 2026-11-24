'use strict';
const mgu = require('./kit/mgu');
const QR = require('./kit/qr');
const { Ctl, Model, SOCKET, CONSOLES_URL } = require('./fx');

const W = 1600;
const H = 520;
const C = { bg: '#0f0f0f', text: '#f1f1f1', dim: '#aaaaaa', accent: '#e50914' };

mgu.run({
    async start(ctx) {
        const { ui, settings, log } = ctx;
        const ctl = new Ctl(SOCKET, log);
        const model = new Model((o) => ctl.send(o));
        let dirty = true;

        const changed = () => { dirty = true; labels(); };
        const closeApp = () => { if (ctx.exitApp) ctx.exitApp(); };

        ctl.on('down', () => { model.setConnected(false); changed(); });
        ctl.on('up', () => { model.setConnected(true); changed(); });
        ctl.on('msg', (m) => { model.onMsg(m); changed(); });
        ctl.connect();

        function labels() {
            const a = model.auth;
            let st = 'Не подключено';
            if (model.connected) {
                if (a.state === 'signed_in') {
                    st = a.login + ' · ' + (a.tier === 'pro_plus' ? 'PRO+' : a.tier === 'pro' ? 'PRO' : 'без PRO');
                } else if (a.state === 'code') st = 'Введите код на сайте';
                else if (a.state === 'error') st = a.msg || 'Ошибка';
                else st = 'Не авторизован';
            }
            ui.text('MAIN_INFO', st, 0, 'Text', { literal: true });
        }
        labels();

        ui.onClick('BTN_EXIT', () => closeApp());
        ui.onClick('BTN_ACCOUNT', () => {
            if (model.auth.state === 'signed_in') model.signOut();
            else model.authStart();
        });
        ui.onClick('BTN_REFRESH', () => model.refreshAuth());

        const loop = ctx.loop('VIEW', 2, async () => {
            if (!dirty) return;
            const cv = ctx.canvas(W, H);
            cv.fillRect(0, 0, W, H, C.bg);
            const a = model.auth;
            cv.text('FilmixProMax', W / 2, 48, 36, C.text, { literal: true, font: 'bold', align: 'center' });

            if (!model.connected) {
                cv.text('Служба jap-filmix-d не запущена', W / 2, H / 2, 28, C.dim, { literal: true, align: 'center' });
            } else if (a.state === 'code' && a.code) {
                const consoles = a.url || CONSOLES_URL;
                cv.text('Добавьте устройство на сайте Filmix', W / 2, 100, 26, C.text, { literal: true, align: 'center' });
                cv.text(consoles, W / 2, 140, 22, C.dim, { literal: true, align: 'center' });
                cv.text(a.code, W / 2, 220, 72, C.accent, { literal: true, font: 'bold', align: 'center' });
                QR.draw(cv, consoles, W / 2 - 80, 280, 8);
                cv.text('После ввода кода нажмите «Обновить»', W / 2, H - 60, 22, C.dim, { literal: true, align: 'center' });
            } else if (a.state === 'signed_in') {
                cv.text('Аккаунт привязан', W / 2, 160, 32, C.text, { literal: true, align: 'center' });
                cv.text(a.login, W / 2, 220, 28, C.accent, { literal: true, align: 'center' });
                const tier = a.tier === 'pro_plus' ? 'PRO+' : a.tier === 'pro' ? 'PRO' : 'без подписки';
                cv.text(tier, W / 2, 270, 24, C.dim, { literal: true, align: 'center' });
                cv.text('Каталог и плеер — следующий этап', W / 2, 360, 22, C.dim, { literal: true, align: 'center' });
            } else if (a.state === 'error') {
                cv.text(a.msg || 'Ошибка API', W / 2, H / 2, 26, C.accent, { literal: true, align: 'center' });
            } else {
                cv.text('Нажмите «Аккаунт» — привязка по коду', W / 2, H / 2, 26, C.dim, { literal: true, align: 'center' });
            }

            await ui.image('VIEW', cv);
            dirty = false;
        });

        ui.onVisible((name) => { if (name === 'VIEW') dirty = true; });
        log.info('filmix_promax started');
    },
});