// landing-page-review — headless capture: runs capture.js inside headless Chrome the way
// Claude in Chrome's javascript_tool would, with the download saved to OUT_DIR. Needs no
// browser extension and nobody to approve downloads, so parallel runs can use it.
//
//   node capture_headless.mjs URL OUT_DIR '{"prefix":"lpr-acme-v0"}'
//   -> OUT_DIR/lpr-acme-v0.html
//
// Prints capture.js's JSON result (page intel, fonts, warnings).
import { spawn } from "node:child_process";
import { readFileSync, mkdtempSync, mkdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const [url, outDir, optsJson = "{}"] = process.argv.slice(2);
if (!url || !outDir) { console.error("usage: node capture_headless.mjs URL OUT_DIR [OPTS_JSON]"); process.exit(2); }
mkdirSync(outDir, { recursive: true });
const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "capture.js"), "utf8");
const chromePath = [
  process.env.CHROME,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
].find((c) => c && existsSync(c));
if (!chromePath) { console.error("Chrome not found; set CHROME=/path/to/chrome"); process.exit(1); }
const profile = mkdtempSync(join(tmpdir(), "lpr-harness-"));
const chrome = spawn(chromePath, ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
  "--window-size=1440,900", "about:blank"], { stdio: ["ignore", "ignore", "pipe"] });
const ws0 = await new Promise((r) => { let b = ""; chrome.stderr.on("data", (d) => { b += d; const m = b.match(/(ws:\/\/\S+)/); if (m) r(m[1]); }); });
const port = new URL(ws0).port;

const browser = new WebSocket(ws0);
await new Promise((r) => (browser.onopen = r));
browser.send(JSON.stringify({ id: 1, method: "Browser.setDownloadBehavior", params: { behavior: "allow", downloadPath: resolve(outDir) } }));

const { webSocketDebuggerUrl } = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map(); let loadCb = null;
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } if (m.method === "Page.loadEventFired" && loadCb) loadCb(); };
const send = (method, params = {}) => new Promise((r) => { pend.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
const loaded = new Promise((r) => (loadCb = r));
await send("Page.navigate", { url });
await loaded;
await new Promise((r) => setTimeout(r, 1500));

const res = await send("Runtime.evaluate", { expression: `window.__LPR_OPTS = ${optsJson};\n${src}`, awaitPromise: true, returnByValue: true, timeout: 120000 });
console.log(res.result?.result?.value ?? JSON.stringify(res.result?.exceptionDetails ?? res));
await new Promise((r) => setTimeout(r, 3000)); // let downloads flush
chrome.kill();
process.exit(0);
