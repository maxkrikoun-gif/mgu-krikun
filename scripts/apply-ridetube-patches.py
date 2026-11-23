#!/usr/bin/env python3
"""Патчи YouT (бывш. RideTube) под mgu-krikun (после fetch-ridetube.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps/jap_ridetube/app.json"
TOOL = ROOT / "native/jap-ridetube-d/component.json"
MAIN_JS = ROOT / "apps/jap_ridetube/main.js"
YT_JS = ROOT / "apps/jap_ridetube/yt.js"
YTD_JS = ROOT / "native/jap-ridetube-d/ytd.js"
NEWS_JS = ROOT / "apps/jap_ridetube/news.js"
RU_LOCALE = ROOT / "kit/runtime/locales/ru.json"

BRAND = "YouT"
APP_TEXTS_RU = {
    "title": BRAND,
    "description": (
        "YouTube в машине: подписки, поиск, история. Звук — медиаплеер BMW. "
        "Видео в движении включено по умолчанию (настройка). "
        "Служба jap-ridetube-d. Обход: proxy Store (krikun-xray)."
    ),
}
TOOL_TEXTS_RU = {
    "title": f"{BRAND} (сервис)",
    "description": "Демон YouTube: сеть, декод, MediaPlayer. Proxy — из настроек Store.",
}


def patch_app() -> None:
    data = json.loads(APP.read_text(encoding="utf-8"))
    data["title"] = BRAND
    data["iconGlyph"] = "YT"
    data["texts"] = {"ru": APP_TEXTS_RU}
    for s in data.get("settings", []):
        if s.get("key") == "language":
            s["default"] = "ru"
        if s.get("key") == "store_proxy":
            s["default"] = True
        if s.get("key") == "video_driving":
            s["default"] = True
    for scr in data.get("screens", []):
        if scr.get("name") == "VIEW":
            scr["title"] = BRAND
        if scr.get("name") == "MAIN":
            scr["title"] = f"{BRAND}: поиск"
    APP.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_tool() -> None:
    data = json.loads(TOOL.read_text(encoding="utf-8"))
    data["texts"] = {"ru": TOOL_TEXTS_RU}
    for ent in data.get("files", []):
        if ent.get("path") == "LICENSE":
            ent["from"] = "../../licenses/ridetube/LICENSE"
        if ent.get("path") == "THIRD_PARTY_LICENSES":
            ent["from"] = "../../licenses/ridetube/THIRD_PARTY_LICENSES"
    TOOL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


DRIVE_LOCK_UPSTREAM = """// The drive lock of "Video while driving": the setting counts only once it is on while parked, so a press while moving
// cannot bring the picture up; off works at once. That parked yes is kept with the settings (video_driving_ok), so a
// restart while driving (an update, the head unit) keeps the passenger's picture. Settings from before 0.6.3 have no
// video_driving_ok: on there counts as said yes (as riskAgreed does), and every check saves the answer, false too.
// Returns (on, moving) => no video.
function driveLock(settings) {
    let ok = settings.get('video_driving') === true && settings.get('video_driving_ok') !== false;
    return (on, moving) => {
        ok = moving ? ok && on : on;
        if (settings.get('video_driving_ok') !== ok) settings.set('video_driving_ok', ok);
        return moving && !ok;
    };
}"""

DRIVE_LOCK_KRIKUN = """// krikun: видео в движении без «включить на стоянке» и video_driving_ok. Returns (on, moving) => no video.
function driveLock(settings) {
    return (on, moving) => moving && !on;
}"""


YTD_CLIENT_CLOSE_UPSTREAM = """    c.on('close', () => {
        if (this.client !== c) return;
        this.client = null;
        this.log('client gone: stop');
        this.rc.off('the app went away');
        this.stop('idle').catch((e) => this.log('stop: ' + e));
    });"""

YTD_CLIENT_CLOSE_KRIKUN = """    c.on('close', () => {
        if (this.client !== c) return;
        this.client = null;
        this.rc.off('the app went away');
        // krikun: пауза вместо stop — при следующем запуске приложения продолжить с того же места
        if (this.state === 'playing') {
            this.log('client gone: pause (krikun)');
            this.pause().catch((e) => this.log('pause: ' + e));
        } else if (this.state === 'paused') {
            this.log('client gone: left paused (krikun)');
        } else {
            this.log('client gone: stop');
            this.stop('idle').catch((e) => this.log('stop: ' + e));
        }
    });"""


def patch_ytd_js() -> None:
    if not YTD_JS.is_file():
        return
    text = YTD_JS.read_text(encoding="utf-8")
    if "client gone: pause (krikun)" in text:
        return
    if YTD_CLIENT_CLOSE_UPSTREAM in text:
        text = text.replace(YTD_CLIENT_CLOSE_UPSTREAM, YTD_CLIENT_CLOSE_KRIKUN)
        YTD_JS.write_text(text, encoding="utf-8")
    else:
        print("  WARN: ytd.js client close не найден", file=sys.stderr)


def patch_yt_js() -> None:
    if not YT_JS.is_file():
        return
    text = YT_JS.read_text(encoding="utf-8")
    if DRIVE_LOCK_UPSTREAM in text and DRIVE_LOCK_KRIKUN.split("\n")[0] not in text:
        text = text.replace(DRIVE_LOCK_UPSTREAM, DRIVE_LOCK_KRIKUN)
    if "    pause()" not in text and "    toggle()" in text:
        text = text.replace(
            "    toggle()",
            """    pause() {
        if (this.state === 'playing') return this.send({ cmd: 'pause' });
        return false;
    }
    resume() {
        if (this.state === 'paused') return this.send({ cmd: 'resume' });
        return false;
    }
    toggle()""",
            1,
        )
    YT_JS.write_text(text, encoding="utf-8")


def patch_main_js() -> None:
    if not MAIN_JS.is_file():
        return
    text = MAIN_JS.read_text(encoding="utf-8")
    text = text.replace("cv.text('RideTube',", f"cv.text('{BRAND}',")
    pairs = [
        (
            "        const lock = driveLock(settings);   // Video while driving counts only once switched on while parked (yt.js)\n"
            "        // the disclaimer (risk page): switched on, the setting counts only once I agree is pressed; already on at start = agreed before\n"
            "        let riskAgreed = settings.get('video_driving') === true, riskAsk = false, riskFrom = 'home';\n"
            "        const noVideo = () => lock(settings.get('video_driving') === true && riskAgreed, parked.moving());",
            "        const lock = driveLock(settings);   // krikun: без parked-lock (yt.js)\n"
            "        let riskAgreed = true, riskAsk = false, riskFrom = 'home';   // krikun: без disclaimer\n"
            "        const noVideo = () => lock(settings.get('video_driving') === true, parked.moving());",
        ),
        (
            "if (mode === 'risk' && m !== 'risk' && riskAsk) { riskAsk = false; settings.set('video_driving', false); }   // left without I agree",
            "if (mode === 'risk' && m !== 'risk' && riskAsk) { riskAsk = false; }   // krikun: без отката настройки",
        ),
        (
            "            if (settings.get('video_driving') !== true) { riskAgreed = false; if (mode === 'risk' && riskAsk) { riskAsk = false; goBack(riskFrom); } }\n"
            "            else if (!riskAgreed && mode !== 'risk') { riskFrom = mode; show('risk'); }",
            "            if (settings.get('video_driving') !== true) { if (mode === 'risk' && riskAsk) { riskAsk = false; goBack(riskFrom); } }\n"
            "            else { riskAgreed = true; }   // krikun: без экрана «Согласен»",
        ),
    ]
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
    text = text.replace(
        "        const changed = () => { dirty = true; if (ctx.background) ctx.background('playing', model.active()); labels(); };",
        "        const changed = () => { dirty = true; labels(); };   // krikun: без фонового hold — закрытие ставит на паузу",
    )
    if "krikun: пауза при уходе" not in text:
        ctl_up = """        ctl.on('up', () => { model.setConnected(true); changed(); });
        ctl.on('down', () => { model.setConnected(false); if (remote) remote.down(); changed(); });
        ctl.on('msg', (m) => {
            model.onMsg(m);
            if (remote) remote.onMsg(m);
            if (m.ev === 'error') log.warn('jap-ridetube-d: ' + m.msg);
            if (m.ev === 'state') log.info('jap-ridetube-d: ' + m.state + (m.id ? ' ' + m.id : ''));
            if (m.ev === 'auth') { log.info('jap-ridetube-d: account ' + m.state); if (m.state === 'signed_in') { if (mode === 'signin') show('home'); openFeed(); } }
            changed();
        });
        ctl.connect();

        /* ---------- hidden channels"""
        ctl_krikun = """        ctl.on('down', () => { model.setConnected(false); if (remote) remote.down(); changed(); });
        let autoResumeOnOpen = false;
        const tryAutoResume = () => {
            if (!autoResumeOnOpen || !model.id || model.state !== 'paused') return;
            autoResumeOnOpen = false;
            log.info('resume playback on open (krikun)');
            model.resume();
            if (mode !== 'player') show('player');
        };
        ctl.on('msg', (m) => {
            model.onMsg(m);
            if (remote) remote.onMsg(m);
            if (m.ev === 'error') log.warn('jap-ridetube-d: ' + m.msg);
            if (m.ev === 'state') {
                log.info('jap-ridetube-d: ' + m.state + (m.id ? ' ' + m.id : ''));
                tryAutoResume();
            }
            if (m.ev === 'auth') { log.info('jap-ridetube-d: account ' + m.state); if (m.state === 'signed_in') { if (mode === 'signin') show('home'); openFeed(); } }
            changed();
        });
        ctl.connect();
        /* krikun: пауза при уходе с экрана / закрытии; при открытии — resume */
        const trackScreens = ['VIEW', 'MAIN', 'SETTINGS'];
        const anyScreenVisible = () => trackScreens.some((n) => ui.isVisible(n));
        let hidePauseT = null;
        const pauseIfPlaying = () => { if (model.state === 'playing') model.pause(); };
        const onAppHide = () => {
            clearTimeout(hidePauseT);
            if (anyScreenVisible()) return;
            hidePauseT = setTimeout(() => { if (!anyScreenVisible()) pauseIfPlaying(); }, 800);
        };
        const onAppShow = () => {
            clearTimeout(hidePauseT);
            if (!anyScreenVisible()) return;
            autoResumeOnOpen = true;
            tryAutoResume();
        };
        ui.onVisible(() => { onAppHide(); onAppShow(); });
        if (ctx.app && ctx.app.on) {
            ctx.app.on('changeVisibility', (d) => {
                if (d && d.visible === false) pauseIfPlaying();
                else if (d && d.visible === true) onAppShow();
            });
            ctx.app.on('shutdown', () => pauseIfPlaying());
        }
        ctl.on('up', () => { autoResumeOnOpen = true; model.setConnected(true); changed(); });

        /* ---------- hidden channels"""
        if ctl_up in text:
            text = text.replace(ctl_up, ctl_krikun)
    MAIN_JS.write_text(text, encoding="utf-8")


def patch_news_js() -> None:
    if not NEWS_JS.is_file():
        return
    text = NEWS_JS.read_text(encoding="utf-8")
    text = text.replace("What's new in RideTube", f"What's new in {BRAND}")
    NEWS_JS.write_text(text, encoding="utf-8")


def patch_ru_locale() -> None:
    if not RU_LOCALE.is_file():
        return
    data = json.loads(RU_LOCALE.read_text(encoding="utf-8"))
    changed = 0
    out = {}
    for k, v in data.items():
        if isinstance(v, str) and "RideTube" in v:
            v = v.replace("RideTube", BRAND)
            changed += 1
        nk = k.replace("RideTube", BRAND) if isinstance(k, str) else k
        out[nk] = v
    RU_LOCALE.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  ru.json: {changed} строк, ключи с брендом — {sum(1 for k in out if 'YouT' in k)}")


def main() -> int:
    if not APP.is_file():
        print("FATAL: нет apps/jap_ridetube/app.json", file=sys.stderr)
        return 1
    patch_app()
    patch_tool()
    patch_main_js()
    patch_yt_js()
    patch_ytd_js()
    patch_news_js()
    patch_ru_locale()
    print(f"Патчи {BRAND} применены (ru, store_proxy, брендинг)")
    return 0


if __name__ == "__main__":
    sys.exit(main())