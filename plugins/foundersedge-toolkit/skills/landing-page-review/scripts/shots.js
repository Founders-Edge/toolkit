// landing-page-review — IN-BROWSER screenshots (fallback for bot-walled pages only;
// prefer scripts/shoot.mjs, which renders more faithfully). See references/advanced.md.
//
// Paste the WHOLE file into Claude in Chrome's javascript_tool, after setting
// window.__LPR_OPTS in the same call, e.g.
//
//   window.__LPR_OPTS = { prefix: "lpr-shot-acme-rivalone" };
//   <contents of this file>
//
// Renders with html2canvas and downloads the same tile layout as shoot.mjs:
//   <prefix>-desktop-01.png … (1440px layout, 1800px per tile, max 3, saved at 0.75 scale)
//   <prefix>-mobile-01.png  … ( 390px layout, 1600px per tile, max 2)
// Result also on window.__LPR_RESULT (re-query until status is "done" or "error").

(() => {
  const O = Object.assign({
    prefix: "lpr-page",
    desktopWidth: 1440, desktopTile: 1800, desktopMaxTiles: 3, desktopScale: 0.75,
    mobileWidth: 390, mobileTile: 1600, mobileMaxTiles: 2,
    h2cUrl: "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js",
  }, window.__LPR_OPTS || {});

  const R = { prefix: O.prefix, url: location.href, files: [], warnings: [], status: "running" };
  window.__LPR_RESULT = R;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const abs = (u) => { try { return new URL(u, document.baseURI).href; } catch { return u; } };
  const txt = (el) => (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim();

  function download(name, blob) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    R.files.push(name);
  }

  // Keep the consent logic in sync with PAGE_HELPERS in shoot.mjs. Accept buttons are
  // searched in open shadow roots too (Usercentrics v3 and others render there).
  const CONSENT_SEL = '#onetrust-consent-sdk,#CybotCookiebotDialog,#usercentrics-root,#usercentrics-cmp-ui,aside#usercentrics-cmp-ui,.cc-window,#cookie-banner,#cookie-consent,[id*="cookie-consent"],[class*="cookie-banner"],[class*="CookieBanner"],[aria-label*="cookie" i][role="dialog"],#didomi-host,#truste-consent-track,.osano-cm-window,#hs-eu-cookie-confirmation';
  const ACCEPT_RE = /^(accept|accept all|accept all cookies|accept cookies|allow all|allow all cookies|i agree|agree|got it|i understand|ok|okay)$/i;
  function dismissConsent() {
    const roots = [document, ...[...document.querySelectorAll("*")].filter((el) => el.shadowRoot).map((el) => el.shadowRoot)];
    for (const root of roots) {
      const b = [...root.querySelectorAll('button,[role="button"]')].find((x) => ACCEPT_RE.test((x.innerText || x.textContent || "").trim()));
      if (b) { b.click(); break; }
    }
    document.querySelectorAll(CONSENT_SEL).forEach((el) => el.remove());
  }

  async function warmUp() {
    dismissConsent();
    await sleep(400);
    // scroll-behavior:smooth makes scrollTo() animate; force instant so captures don't land mid-scroll.
    const ss = document.createElement("style");
    ss.id = "lpr-instant-scroll";
    ss.textContent = "html,body{scroll-behavior:auto!important}";
    document.head.appendChild(ss);
    const h = () => document.documentElement.scrollHeight;
    for (let y = 0; y < h() && y < 20000; y += Math.round(innerHeight * 0.8)) {
      scrollTo(0, y);
      await sleep(120);
    }
    for (let i = 0; i < 5 && scrollY !== 0; i++) { scrollTo({ top: 0, left: 0, behavior: "instant" }); await sleep(300); }
    dismissConsent();  // again: many consent tools inject late
    await sleep(300);
  }


  async function loadH2C() {
    if (window.html2canvas) return true;
    return new Promise((resolve) => {
      const s = document.createElement("script");
      s.src = O.h2cUrl;
      s.onload = () => resolve(!!window.html2canvas);
      s.onerror = () => resolve(false);
      document.head.appendChild(s);
      setTimeout(() => resolve(!!window.html2canvas), 8000);
    });
  }

  // Count above-the-fold cross-origin images html2canvas will likely drop (no CORS headers).
  async function corsCheck() {
    const imgs = [...document.images].filter((i) => i.getBoundingClientRect().top < 2000 && i.currentSrc &&
      new URL(i.currentSrc).origin !== location.origin && !i.currentSrc.startsWith("data:")).slice(0, 15);
    let blocked = 0;
    await Promise.all(imgs.map((i) => fetch(i.currentSrc, { mode: "cors" }).then((r) => { if (!r.ok) blocked++; }).catch(() => blocked++)));
    return { checked: imgs.length, blocked };
  }

  async function render(width, maxH) {
    let cloneH = 0;
    const bg = getComputedStyle(document.body).backgroundColor;
    const canvas = await window.html2canvas(document.documentElement, {
      windowWidth: width, width, height: maxH, x: 0, y: 0, scrollX: 0, scrollY: 0, scale: 1,
      useCORS: true, logging: false,
      backgroundColor: bg && bg !== "rgba(0, 0, 0, 0)" ? bg : "#ffffff",
      onclone: (d) => {
        const st = d.createElement("style");
        st.textContent = "*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;transition:none!important}";
        d.head.appendChild(st);
        cloneH = d.documentElement.scrollHeight;
      },
    });
    const h = Math.min(maxH, cloneH || maxH, canvas.height);
    return { canvas, h };
  }

  const toBlob = (c) => new Promise((r) => c.toBlob(r, "image/png"));

  function crop(src, y, w, h, scale = 1) {
    const c = document.createElement("canvas");
    c.width = Math.round(w * scale); c.height = Math.round(h * scale);
    c.getContext("2d").drawImage(src, 0, y, w, h, 0, 0, c.width, c.height);
    return c;
  }

  async function shots() {
    if (!(await loadH2C())) {
      R.warnings.push("html2canvas could not load (likely CSP) — use the headless Chrome fallback for screenshots");
      R.shots = { ok: false, reason: "h2c-blocked" };
      return;
    }
    R.cors = await corsCheck();
    if (R.cors.blocked) R.warnings.push(`${R.cors.blocked}/${R.cors.checked} above-fold cross-origin images may render blank`);

    // Desktop: vertical tiles.
    const D = await render(O.desktopWidth, O.desktopTile * O.desktopMaxTiles);
    const nD = Math.ceil(D.h / O.desktopTile);
    for (let i = 0; i < nD; i++) {
      const th = Math.min(O.desktopTile, D.h - i * O.desktopTile);
      download(`${O.prefix}-desktop-${String(i + 1).padStart(2, "0")}.png`, await toBlob(crop(D.canvas, i * O.desktopTile, O.desktopWidth, th, O.desktopScale)));
      await sleep(250); // Chrome throttles bursts of downloads
    }

    // Mobile: html2canvas re-lays the clone out at 390px, so media queries apply.
    const M = await render(O.mobileWidth, O.mobileTile * O.mobileMaxTiles);
    const nM = Math.ceil(M.h / O.mobileTile);
    for (let i = 0; i < nM; i++) {
      const th = Math.min(O.mobileTile, M.h - i * O.mobileTile);
      download(`${O.prefix}-mobile-${String(i + 1).padStart(2, "0")}.png`, await toBlob(crop(M.canvas, i * O.mobileTile, O.mobileWidth, th)));
      await sleep(250);
    }

    R.shots = { ok: true, desktopTiles: nD, desktopPx: D.h, mobileTiles: nM, mobilePx: M.h,
      truncated: document.documentElement.scrollHeight > O.desktopTile * O.desktopMaxTiles };
  }

  const run = (async () => {
    try {
      await warmUp();
      await shots();
      R.status = "done";
    } catch (e) {
      R.status = "error";
      R.error = String((e && e.stack) || e).slice(0, 500);
    }
    return JSON.stringify(R);
  })();
  return run;
})();
