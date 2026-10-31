#!/usr/bin/env node
// landing-page-review — headless screenshotter (fallback for capture.js).
//
// Drives Chrome over the DevTools protocol with a real emulated viewport, so
// 100vh heroes and mobile breakpoints render the way a visitor sees them.
// No npm install: needs Node >= 22 (built-in WebSocket) and Chrome/Chromium.
//
//   node shoot.mjs [--keep-popups] --out DIR NAME=URL [NAME=URL ...]
//   -> DIR/NAME-desktop-01.png … (1440px viewport, 1800px of page per tile, max 3,
//                                  saved at 0.75 scale: 1080 wide, to save judge tokens)
//      DIR/NAME-mobile-01.png  … ( 390px viewport, 1600px per tile, max 2)
//
// Pages are shot up to 3 at a time, desktop and mobile in parallel. Cookie banners, chat
// widgets and popups are hidden on every page (--keep-popups keeps the popups).
//
// Same file layout as capture.js, so judges see identical formats either way.
// Prints one JSON line per page with tile counts and warnings.

import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync, existsSync, mkdirSync, readdirSync, unlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const VIEWPORTS = [
  // A normal desktop UA: the default "HeadlessChrome" UA invites bot walls.
  { kind: "desktop", width: 1440, height: 900, tile: 1800, maxTiles: 3, mobile: false, scale: 0.75,
    ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36" },
  { kind: "mobile", width: 390, height: 844, tile: 1600, maxTiles: 2, mobile: true, scale: 1,
    ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" },
];

const args = process.argv.slice(2);
const KEEP_POPUPS = args.includes("--keep-popups");
if (KEEP_POPUPS) args.splice(args.indexOf("--keep-popups"), 1);
const outIdx = args.indexOf("--out");
if (outIdx < 0 || !args[outIdx + 1]) {
  console.error("usage: node shoot.mjs [--keep-popups] --out DIR NAME=URL [NAME=URL ...]");
  process.exit(2);
}
const outDir = args[outIdx + 1];
const pages = args.filter((_, i) => i !== outIdx && i !== outIdx + 1).map((a) => {
  const eq = a.indexOf("=");
  if (eq < 1) { console.error(`bad page arg: ${a}`); process.exit(2); }
  return { name: a.slice(0, eq), url: a.slice(eq + 1) };
});
mkdirSync(outDir, { recursive: true });

function findChrome() {
  const candidates = [
    process.env.CHROME,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    process.env.LOCALAPPDATA && join(process.env.LOCALAPPDATA, "Google", "Chrome", "Application", "chrome.exe"),
  ];
  const hit = candidates.find((c) => c && existsSync(c));
  if (!hit) { console.error("Chrome not found; set CHROME=/path/to/chrome"); process.exit(1); }
  return hit;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// In-page helpers, injected as source. Keep the consent logic in sync with capture.js.
const PAGE_HELPERS = `
  // Cookie/consent overlays would cover the hero in every screenshot. Click an accept
  // button if there is one (searching open shadow roots too: Usercentrics v3 and others
  // render there), then hide the common consent containers. Hide, never remove: removing a
  // node React owns crashes its next re-render and blanks the whole page.
  const CONSENT_SEL = '#onetrust-consent-sdk,#CybotCookiebotDialog,#usercentrics-root,#usercentrics-cmp-ui,aside#usercentrics-cmp-ui,.cc-window,#cookie-banner,#cookie-consent,[id*="cookie-consent"],[class*="cookie-banner"],[class*="CookieBanner"],[aria-label*="cookie" i][role="dialog"],#didomi-host,#truste-consent-track,.osano-cm-window,#hs-eu-cookie-confirmation';
  const ACCEPT_RE = /^(accept|accept all|accept all cookies|accept cookies|allow all|allow all cookies|i agree|agree|got it|i understand|ok|okay)$/i;
  const allRoots = () => {
    const roots = [document];
    for (const el of document.querySelectorAll("*")) if (el.shadowRoot) roots.push(el.shadowRoot);
    return roots;
  };
  const hide = (el) => el.style.setProperty("display", "none", "important");
  const dismissConsent = async () => {
    for (const root of allRoots()) {
      const b = [...root.querySelectorAll('button,[role="button"]')].find((x) => ACCEPT_RE.test((x.innerText || x.textContent || "").trim()));
      if (b) { b.click(); await sleep(600); break; }
    }
    document.querySelectorAll(CONSENT_SEL).forEach(hide);
  };
  // Chat bubbles, slide-ins and newsletter popups cover CTAs in some shots, and judges can't
  // see past them. Hide fixed elements that name themselves as one, or narrow boxes floating
  // below the header. Full-width bars (headers, sticky mobile CTAs) stay. Every page gets the
  // same pass, so conditions stay equal; --keep-popups turns it off.
  const POPUP_RE = /chat|intercom|drift|hubspot-messages|crisp|tawk|zendesk|tidio|livechat|popup|pop-up|modal|newsletter|slide-?in/i;
  const hidePopups = () => {
    let n = 0;
    for (const el of document.querySelectorAll("body *")) {
      if (el.closest("[data-lpr-hidden]")) continue;
      const cs = getComputedStyle(el);
      if (cs.position !== "fixed" || cs.display === "none") continue;
      const r = el.getBoundingClientRect();
      const name = [el.id, typeof el.className === "string" ? el.className : "", el.getAttribute("aria-label") || "", el.getAttribute("title") || ""].join(" ");
      if (POPUP_RE.test(name) || (r.top > 150 && r.width < innerWidth * 0.7)) {
        hide(el); el.setAttribute("data-lpr-hidden", ""); n++;
      }
    }
    return n;
  };
  // Anything fixed/sticky, covering >15% of the viewport, that talks about cookies/consent.
  const overlayLeft = () => [...document.querySelectorAll("body *")].some((el) => {
    const cs = getComputedStyle(el);
    if (cs.position !== "fixed" && cs.position !== "sticky") return false;
    const r = el.getBoundingClientRect();
    if (r.width * r.height < innerWidth * innerHeight * 0.15) return false;
    const t = (el.innerText || "") + " " + (el.shadowRoot ? el.shadowRoot.textContent : "");
    return /cookie|consent|privacy settings|gdpr/i.test(t) && cs.display !== "none" && cs.visibility !== "hidden";
  });
  // Some pages scroll inside a full-height container instead of the document, which
  // would capture as a single viewport. Unlock the largest such container.
  const unlockInnerScroll = () => {
    if (document.documentElement.scrollHeight > innerHeight + 50) return false;
    const box = [document.body, ...document.querySelectorAll("body *")].filter((el) => {
      const oy = getComputedStyle(el).overflowY;
      return (oy === "auto" || oy === "scroll") && el.scrollHeight > el.clientHeight + 50;
    }).sort((a, b) => b.scrollHeight - a.scrollHeight)[0];
    if (!box) return false;
    const st = document.createElement("style");
    st.textContent = "html,body{height:auto!important;overflow:visible!important}";
    document.head.appendChild(st);
    for (let el = box; el && el !== document.documentElement; el = el.parentElement) {
      el.style.setProperty("height", "auto", "important");
      el.style.setProperty("max-height", "none", "important");
      el.style.setProperty("overflow", "visible", "important");
    }
    return true;
  };`;

// Headings whose last rendered line is a single word ("…govern production / AI.").
// Run after the screenshots: it wraps words in spans to measure line breaks.
const FIND_WIDOWS = `(() => {
  const out = [];
  for (const h of document.querySelectorAll("h1,h2,h3,h4")) {
    const text = (h.innerText || "").trim();
    if (!text || text.split(/\\s+/).length < 3 || h.getBoundingClientRect().width === 0) continue;
    const walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    const spans = [];
    for (const n of nodes) {
      const frag = document.createDocumentFragment();
      for (const part of n.textContent.split(/(\\s+)/)) {
        if (!part) continue;
        // Whitespace and invisible tokens (zero-width joiners etc.) aren't words.
        if (!/[\\p{L}\\p{N}]/u.test(part)) { frag.appendChild(document.createTextNode(part)); continue; }
        const sp = document.createElement("span");
        sp.textContent = part;
        spans.push(sp);
        frag.appendChild(sp);
      }
      n.replaceWith(frag);
    }
    if (spans.length < 3) continue;
    const top = (sp) => Math.round(sp.getBoundingClientRect().top);
    const last = top(spans[spans.length - 1]);
    const lines = new Set(spans.map(top));
    if (lines.size > 1 && spans.filter((sp) => top(sp) === last).length === 1) out.push(text.slice(0, 90));
  }
  return out;
})()`;

async function launch() {
  const profile = mkdtempSync(join(tmpdir(), "lpr-chrome-"));
  const proc = spawn(findChrome(), [
    "--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
    "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });
  const wsUrl = await new Promise((resolve, reject) => {
    let buf = "";
    const t = setTimeout(() => reject(new Error("Chrome did not start")), 15000);
    proc.stderr.on("data", (d) => {
      buf += d;
      const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
      if (m) { clearTimeout(t); resolve(m[1]); }
    });
  });
  const port = new URL(wsUrl).port;
  const close = () => { proc.kill(); try { rmSync(profile, { recursive: true, force: true }); } catch {} };
  return { port, close };
}

async function connect(port) {
  const res = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" });
  const { webSocketDebuggerUrl } = await res.json();
  const ws = new WebSocket(webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0;
  const pending = new Map();
  const listeners = new Map();
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method && listeners.has(msg.method)) {
      listeners.get(msg.method).forEach((fn) => fn(msg.params));
    }
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    pending.set(++id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const once = (method, timeoutMs) => new Promise((resolve) => {
    const fns = listeners.get(method) || [];
    const fn = (p) => { listeners.set(method, (listeners.get(method) || []).filter((f) => f !== fn)); resolve(p); };
    listeners.set(method, [...fns, fn]);
    setTimeout(() => resolve(null), timeoutMs);
  });
  return { send, once, close: () => ws.close() };
}

const evaluate = async (cdp, expression) =>
  (await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result.value;

async function shootPage(cdp, page, vp) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: vp.mobile });
  await cdp.send("Emulation.setTouchEmulationEnabled", { enabled: vp.mobile });
  await cdp.send("Emulation.setUserAgentOverride", { userAgent: vp.ua });

  const warnings = [];
  const loaded = cdp.once("Page.loadEventFired", 30000);
  const nav = await cdp.send("Page.navigate", { url: page.url });
  if (nav.errorText) throw new Error(`navigation failed: ${nav.errorText}`);
  if (!(await loaded)) warnings.push("page load event timed out after 30s — check the screenshot for missing content");
  // Wait for web fonts, then a short settle, instead of a long fixed sleep.
  await evaluate(cdp, "Promise.race([document.fonts.ready.then(() => 1), new Promise((r) => setTimeout(r, 3000))])").catch(() => {});
  await sleep(500);

  // Scroll through to fire lazy-loading and reveal-on-scroll, then freeze animations.
  const info = await evaluate(cdp, `(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    ${PAGE_HELPERS}
    const textLen = () => (document.body.innerText || "").trim().length;
    // Single-page apps may not have rendered yet: give them up to 10 s.
    for (let i = 0; i < 20 && textLen() < 200; i++) await sleep(500);
    const textBefore = textLen();
    await dismissConsent();
    const unlocked = unlockInnerScroll();
    // scroll-behavior:smooth makes scrollTo() animate, so the capture would land mid-scroll
    // with fixed headers offset. Force instant scrolling.
    const ss = document.createElement("style");
    ss.textContent = "html,body{scroll-behavior:auto!important}";
    document.head.appendChild(ss);
    await sleep(400);
    for (let y = 0; y < document.documentElement.scrollHeight && y < 20000; y += innerHeight * 0.8) {
      scrollTo(0, y); await sleep(150);
    }
    for (let i = 0; i < 5 && scrollY !== 0; i++) { scrollTo({ top: 0, left: 0, behavior: "instant" }); await sleep(300); }
    await dismissConsent();  // again: many consent tools inject late, after the first scroll
    await sleep(300);
    // Popups often open a second or so after load or on scroll, so this runs last.
    const popups = ${KEEP_POPUPS ? "0" : "hidePopups()"};
    const st = document.createElement("style");
    st.textContent = "*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;transition:none!important}";
    document.head.appendChild(st);
    await sleep(200);
    return { height: document.documentElement.scrollHeight, title: document.title,
             text: (document.body.innerText || "").slice(0, 300), unlocked, overlay: overlayLeft(),
             textBefore, textAfter: textLen(), popups };
  })()`);

  if (/just a moment|attention required|access denied|captcha|are you a robot/i.test(info.title + " " + info.text))
    warnings.push("looks like a bot wall — swap in a reserve competitor, or switch the whole run to in-browser screenshots (references/advanced.md)");
  if (info.unlocked) warnings.push("page scrolls inside a container — unlocked it to capture the full page; check the tiles");
  if (info.overlay) warnings.push("a cookie/consent overlay may still cover the page — check desktop-01 and dismiss it before judging");
  if (info.textBefore > 200 && info.textAfter < info.textBefore * 0.1)
    warnings.push(`page text dropped from ${info.textBefore} to ${info.textAfter} characters while loading — the page likely crashed or went blank`);
  if (info.height <= vp.height + 50) warnings.push("only one viewport captured — the page may scroll in a way the script couldn't unlock");

  // Remove tiles from any earlier shot of this page so a shorter re-shoot leaves no strays.
  const stale = new RegExp(`^${page.name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}-${vp.kind}(-\\d\\d\\.png|\\.json)$`);
  for (const f of readdirSync(outDir)) if (stale.test(f)) unlinkSync(join(outDir, f));

  const h = Math.min(info.height, vp.tile * vp.maxTiles);
  const n = Math.max(1, Math.ceil(h / vp.tile));
  for (let i = 0; i < n; i++) {
    const th = Math.min(vp.tile, h - i * vp.tile);
    const shot = await cdp.send("Page.captureScreenshot", {
      format: "png", captureBeyondViewport: true,
      clip: { x: 0, y: i * vp.tile, width: vp.width, height: th, scale: vp.scale },
    });
    writeFileSync(join(outDir, `${page.name}-${vp.kind}-${String(i + 1).padStart(2, "0")}.png`), Buffer.from(shot.data, "base64"));
  }
  const widows = await evaluate(cdp, FIND_WIDOWS);
  if (widows.length) warnings.push(`${vp.kind}: one-word last line in ${widows.length} heading(s): ${widows.map((w) => `"${w}"`).join(", ")}`);
  // Sidecar for new_round.py: whether judges should be told the page continues below.
  writeFileSync(join(outDir, `${page.name}-${vp.kind}.json`), JSON.stringify({ px: h, fullHeight: info.height, truncated: info.height > h }));
  return { tiles: n, px: h, truncated: info.height > h, warnings };
}

async function shootAll(page) {
  const result = { name: page.name, url: page.url, warnings: [] };
  // Desktop and mobile in parallel, each in its own tab.
  await Promise.all(VIEWPORTS.map(async (vp) => {
    // One retry: some pages redirect client-side right after load ("target navigated").
    for (let attempt = 1; attempt <= 2; attempt++) {
      const cdp = await connect(chrome.port);
      try {
        await cdp.send("Page.enable");
        const r = await shootPage(cdp, page, vp);
        result[vp.kind] = { tiles: r.tiles, px: r.px, truncated: r.truncated };
        result.warnings.push(...r.warnings);
        return;
      } catch (e) {
        if (attempt === 2) result.error = (result.error ? result.error + "; " : "") + `${vp.kind}: ${e.message || e}`;
      } finally {
        cdp.close();
      }
    }
  }));
  result.warnings = [...new Set(result.warnings)];
  return result;
}

const chrome = await launch();
let failed = 0;
try {
  // Up to 3 pages at a time; print results in the order given.
  for (let i = 0; i < pages.length; i += 3) {
    const results = await Promise.all(pages.slice(i, i + 3).map(shootAll));
    for (const r of results) {
      if (r.error) failed++;
      console.log(JSON.stringify(r));
    }
  }
} finally {
  chrome.close();
}
process.exit(failed ? 1 : 0);
