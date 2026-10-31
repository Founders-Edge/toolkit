// landing-page-review — in-page capture of the TARGET page (HTML snapshot + page intel).
//
// Paste the WHOLE file into Claude in Chrome's javascript_tool, after setting
// window.__LPR_OPTS in the same call, e.g.
//
//   window.__LPR_OPTS = { prefix: "lpr-acme-v0" };
//   <contents of this file>
//
// One call: scrolls the page (lazy images, reveal-on-scroll), dismisses consent banners,
// returns compact page intel (title, headings, CTAs, meta) and downloads a self-contained
// HTML snapshot <prefix>.html to the browser's download folder.
// (In-browser screenshots for bot-walled pages live in shots.js, so this stays small.)
//
// The tool may not await promises: the result is also stored on window.__LPR_RESULT —
// if the call returns `{}` or a pending promise, query `JSON.stringify(window.__LPR_RESULT)`
// again until its status is "done" or "error". The intel is compact (the tool truncates
// long results); for the full page copy, read the downloaded HTML instead.

(() => {
  const O = Object.assign({
    prefix: "lpr-page",
    stripScripts: "auto",  // "auto" | true | false — strip JS from snapshot
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
  // Hide leftover banners, never remove them: if a framework owns the node, removing it under
  // React crashes the next re-render and unmounts the whole page.
  async function dismissConsent() {
    const roots = [document, ...[...document.querySelectorAll("*")].filter((el) => el.shadowRoot).map((el) => el.shadowRoot)];
    for (const root of roots) {
      const b = [...root.querySelectorAll('button,[role="button"]')].find((x) => ACCEPT_RE.test((x.innerText || x.textContent || "").trim()));
      if (b) { b.click(); await sleep(600); break; }
    }
    document.querySelectorAll(CONSENT_SEL).forEach((el) => el.style.setProperty("display", "none", "important"));
  }

  const textLen = () => (document.body.innerText || "").trim().length;

  async function warmUp() {
    // Single-page apps may not have rendered yet: give them up to 10 s.
    for (let i = 0; i < 20 && textLen() < 200; i++) await sleep(500);
    const before = textLen();
    await dismissConsent();
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
    await dismissConsent();  // again: many consent tools inject late
    await sleep(300);
    if (before > 200 && textLen() < before * 0.1)
      R.warnings.push(`page text dropped from ${before} to ${textLen()} characters during warm-up — the page likely crashed or went blank; check the snapshot before using it`);
  }


  function intel() {
    const q = (s) => [...document.querySelectorAll(s)];
    const meta = (n) => (document.querySelector(`meta[name="${n}"],meta[property="${n}"]`) || {}).content || "";
    const ctas = q("a,button").filter((el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const t = txt(el);
      const styled = cs.backgroundColor !== "rgba(0, 0, 0, 0)" || parseFloat(cs.borderTopWidth) > 0 ||
        /btn|button|cta/i.test(String(el.className));
      // Nav/header items only count when they read like an action ("Sign up", "Book a demo").
      const inNav = !!el.closest("nav,header");
      const actiony = /sign|start|try|demo|get|book|contact|buy|join|request|free/i.test(t);
      return t && t.length < 40 && r.width > 60 && r.height > 28 && styled && (!inNav || actiony);
    }).slice(0, 12).map(txt);
    return {
      title: document.title,
      description: meta("description") || meta("og:description"),
      h1: q("h1").map(txt).slice(0, 3),
      h2: q("h2").map(txt).filter(Boolean).map((t) => t.slice(0, 80)).slice(0, 10),
      ctas: [...new Set(ctas)].slice(0, 8),
      heroText: txt(document.querySelector("main") || document.body).slice(0, 300),
      pageHeight: document.documentElement.scrollHeight,
    };
  }

  async function snapshotHtml() {
    const doc = document.documentElement.cloneNode(true);
    // Keep authored CSS text wherever possible: Chrome's CSSOM serialization blanks
    // shorthands that use var() (e.g. `background: linear-gradient(var(--a), …)`).
    // Only <style> tags that are empty in the DOM — CSS-in-JS (styled-components,
    // emotion…) filling them via insertRule — are rebuilt from the live CSSOM.
    doc.querySelector("#lpr-instant-scroll")?.remove();
    const liveStyles = [...document.querySelectorAll("style")].filter((s) => s.id !== "lpr-instant-scroll");
    const cloneStyles = [...doc.querySelectorAll("style")];
    liveStyles.forEach((s, i) => {
      if (s.textContent.trim()) return;
      try {
        const css = [...s.sheet.cssRules].map((r) => r.cssText).join("\n");
        if (css && cloneStyles[i]) cloneStyles[i].textContent = css;
      } catch {}
    });
    for (const sheet of document.adoptedStyleSheets || []) {
      const st = document.createElement("style");
      st.textContent = [...sheet.cssRules].map((r) => r.cssText).join("\n");
      doc.querySelector("head").appendChild(st);
    }
    // Absolutize every asset reference so the snapshot works from localhost.
    for (const [sel, attr] of [["[src]", "src"], ["[href]", "href"], ["[poster]", "poster"], ["[action]", "action"]]) {
      doc.querySelectorAll(sel).forEach((el) => {
        const v = el.getAttribute(attr);
        if (v && !/^(#|data:|mailto:|tel:|javascript:)/i.test(v)) el.setAttribute(attr, abs(v));
      });
    }
    doc.querySelectorAll("[srcset]").forEach((el) => {
      el.setAttribute("srcset", el.getAttribute("srcset").split(",").map((p) => {
        const [u, ...rest] = p.trim().split(/\s+/);
        return [abs(u), ...rest].join(" ");
      }).join(", "));
    });
    // Lazy-loaded images: freeze whatever the live page actually resolved.
    const live = [...document.images];
    doc.querySelectorAll("img").forEach((el, i) => {
      if (live[i] && live[i].currentSrc) { el.setAttribute("src", live[i].currentSrc); el.removeAttribute("loading"); }
    });
    // Inline linked stylesheets from their original text (fetch); fall back to the
    // CSSOM only if the fetch fails. Unreadable cross-origin sheets stay as <link>s.
    const linkEls = [...doc.querySelectorAll('link[rel~="stylesheet"]')];
    for (const sheet of [...document.styleSheets]) {
      if (!sheet.href) continue;
      const link = linkEls.find((l) => l.getAttribute("href") === sheet.href);
      if (!link) continue;
      let css = null;
      try { const r = await fetch(sheet.href); if (r.ok) css = await r.text(); } catch {}
      if (css === null) {
        try { css = [...sheet.cssRules].map((r) => r.cssText).join("\n"); } catch { continue; }
        R.warnings.push(`inlined ${sheet.href} from CSSOM (fetch failed) — var() shorthands may be blank`);
      }
      css = css.replace(/url\((['"]?)(?!data:)([^'")]+)\1\)/g, (m, q, u) => `url("${new URL(u, sheet.href).href}")`);
      const style = document.createElement("style");
      style.setAttribute("data-lpr-from", sheet.href);
      if (link.getAttribute("media")) style.setAttribute("media", link.getAttribute("media"));
      style.textContent = css;
      link.replaceWith(style);
    }
    // Inline <style> blocks can contain relative url()s too.
    doc.querySelectorAll("style:not([data-lpr-from])").forEach((s) => {
      s.textContent = s.textContent.replace(/url\((['"]?)(?!data:)([^'")]+)\1\)/g, (m, q, u) => `url("${abs(u)}")`);
    });
    doc.querySelectorAll('meta[http-equiv="Content-Security-Policy"], base').forEach((el) => el.remove());

    // Embed web fonts as data URIs. Fonts need CORS, so the origin usually refuses them
    // when the snapshot is served from localhost and the page falls back to Arial —
    // an unfair handicap. Fetching here works: we're running on the live origin.
    const styles = [...doc.querySelectorAll("style")];
    const fontUrls = new Set();
    for (const st of styles)
      for (const block of st.textContent.match(/@font-face\s*{[^}]*}/g) || [])
        for (const m of block.matchAll(/url\((['"]?)(?!data:)([^'")]+)\1\)/g)) fontUrls.add(m[2]);
    const dataUris = {};
    let fontBytes = 0, fontFails = 0;
    await Promise.all([...fontUrls].map(async (u) => {
      try {
        const r = await fetch(u);
        if (!r.ok) throw 0;
        const blob = await r.blob();
        if (fontBytes + blob.size > 12e6) throw 0;
        fontBytes += blob.size;
        dataUris[u] = await new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(blob); });
      } catch { fontFails++; }
    }));
    for (const st of styles)
      st.textContent = st.textContent.replace(/url\((['"]?)(?!data:)([^'")]+)\1\)/g, (m, q, u) => dataUris[u] ? `url("${dataUris[u]}")` : m);
    R.fonts = { found: fontUrls.size, embedded: Object.keys(dataUris).length, kb: Math.round(fontBytes / 1024) };
    if (fontFails) R.warnings.push(`${fontFails}/${fontUrls.size} web fonts could not be embedded — check the local copy's typeface`);

    // Blanked declarations ("prop: ;") mean CSS was lost somewhere.
    const blanks = styles.reduce((n, st) => n + (st.textContent.match(/[\w-]:\s*;/g) || []).length, 0);
    if (blanks > 5) R.warnings.push(`${blanks} blank CSS declarations in snapshot — compare against live carefully`);

    // Framework bundles re-hydrate and overwrite edits, so strip them by default.
    const framework = !!(document.getElementById("__next") || document.getElementById("__nuxt") ||
      document.getElementById("___gatsby") || document.querySelector("[data-reactroot],[ng-version],[data-v-app]") ||
      document.querySelector('script[src*="/_next/"],script[src*="/_nuxt/"],script[src*="webflow"],script[type="module"][src*="/assets/index-"]') ||
      // Vite / Create React App / Vue single-page apps mount into #root or #app.
      [document.getElementById("root"), document.getElementById("app")].some((el) => el &&
        (el.__vue_app__ || el._reactRootContainer || Object.keys(el).some((k) => k.startsWith("__reactContainer")))));
    const strip = O.stripScripts === "auto" ? framework : !!O.stripScripts;
    if (strip) {
      doc.querySelectorAll('script:not([type="application/ld+json"]), link[rel="modulepreload"], link[as="script"]').forEach((el) => el.remove());
      // Animation libraries (GSAP and similar) set inline start states such as opacity:0 and only
      // reveal content from script. With the scripts gone, those sections would stay invisible.
      let revealed = 0;
      doc.querySelectorAll("body [style]").forEach((el) => {
        const st = el.style;
        if (!(st.opacity === "0" || st.visibility === "hidden" || /translate|scale/.test(st.transform))) return;
        if (!(el.textContent || "").trim() && !el.querySelector("img,svg,video,picture")) return;
        st.removeProperty("opacity"); st.removeProperty("visibility"); st.removeProperty("transform");
        revealed++;
      });
      if (revealed) R.warnings.push(`revealed ${revealed} element(s) left hidden by scroll animations (inline opacity/visibility/transform) — check the snapshot for menus or popups that should stay hidden`);
    }
    R.html = { framework, scriptsStripped: strip };

    // Things that render live but won't survive a static copy, so v0 would be judged at a
    // disadvantage: custom elements whose definitions get stripped (e.g. <mux-player>) and
    // third-party embeds that need their own JS/cookies (forms, schedulers).
    if (strip) {
      const custom = [...new Set([...document.querySelectorAll("*")].map((el) => el.localName)
        .filter((t) => t.includes("-") && customElements.get(t)))];
      if (custom.length) R.warnings.push(`custom elements will not render in the copy once scripts are stripped: <${custom.join(">, <")}> — restore their script or replace with a static poster/image`);
    }
    const embeds = [...document.querySelectorAll("iframe[src]")].map((f) => f.src)
      .filter((u) => /hsforms|hubspot|typeform|calendly|marketo|jotform|tally\.so|cal\.com|chilipiper|youtube|vimeo|loom|wistia/i.test(u));
    if (embeds.length) R.warnings.push(`${embeds.length} third-party embed(s) may render empty in the copy (${[...new Set(embeds.map((u) => new URL(u).hostname))].join(", ")}) — compare every v0 tile with live`);

    const html = "<!doctype html>\n<!-- captured by landing-page-review from " + location.href + " on " +
      new Date().toISOString() + " -->\n" + doc.outerHTML;
    download(O.prefix + ".html", new Blob([html], { type: "text/html" }));
  }


  const run = (async () => {
    try {
      await warmUp();
      R.intel = intel();
      await snapshotHtml();
      R.status = "done";
    } catch (e) {
      R.status = "error";
      R.error = String((e && e.stack) || e).slice(0, 500);
    }
    return JSON.stringify(R);
  })();
  return run;
})();
