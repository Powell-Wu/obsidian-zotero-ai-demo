#!/usr/bin/env node
/* Headless Chromium/Edge smoke test; writes only an ignored local profile and a public result JSON. */
const { spawn } = require("node:child_process");
const { existsSync, writeFileSync } = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const root = path.resolve(__dirname, "..");
const resultPath = path.join(root, "99附件", "浏览器验证.json");
const profile = path.join(root, ".tools", "browser-profile");
const edge = process.env["PROGRAMFILES(X86)"]
  ? path.join(process.env["PROGRAMFILES(X86)"], "Microsoft", "Edge", "Application", "msedge.exe") : "";
const chrome = process.env.ProgramFiles
  ? path.join(process.env.ProgramFiles, "Google", "Chrome", "Application", "chrome.exe") : "";
const browserPath = [edge, chrome].find(candidate => candidate && existsSync(candidate));
const checks = [];
const consoleErrors = [];
let child;

function record(name, pass, detail) {
  checks.push({ name, pass: Boolean(pass), detail });
}

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    const timer = setTimeout(() => reject(new Error("WebSocket connection timeout")), 15000);
    ws.onopen = () => { clearTimeout(timer); resolve(ws); };
    ws.onerror = event => { clearTimeout(timer); reject(new Error("WebSocket error: " + event.message)); };
  });
}

function client(ws) {
  let serial = 0;
  const pending = new Map();
  const listeners = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result || {});
    } else if (message.method && listeners.has(message.method)) {
      listeners.get(message.method)(message.params || {});
    }
  };
  return {
    on(method, callback) { listeners.set(method, callback); },
    send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const id = ++serial;
        pending.set(id, { resolve, reject });
        ws.send(JSON.stringify({ id, method, params }));
      });
    },
    close() { ws.close(); }
  };
}

async function evaluate(page, expression) {
  const response = await page.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
  return response.result ? response.result.value : undefined;
}

async function waitFor(page, expression, timeout = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evaluate(page, expression)) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error("Timed out waiting for: " + expression);
}

async function run() {
  if (!browserPath) throw new Error("No local Edge or Chrome executable found");
  const args = [
    "--headless=new", "--disable-gpu", "--disable-background-networking",
    "--disable-component-update", "--disable-sync", "--metrics-recording-only",
    "--no-first-run", "--no-default-browser-check", "--remote-debugging-address=127.0.0.1",
    "--remote-debugging-port=0", "--user-data-dir=" + profile, "about:blank"
  ];
  child = spawn(browserPath, args, { stdio: ["ignore", "ignore", "pipe"] });
  const browserWs = await new Promise((resolve, reject) => {
    let stderr = "";
    const timer = setTimeout(() => reject(new Error("DevTools startup timeout: " + stderr)), 15000);
    child.stderr.on("data", chunk => {
      stderr += chunk.toString();
      const match = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) { clearTimeout(timer); resolve(match[1]); }
    });
    child.once("error", reject);
    child.once("exit", code => { clearTimeout(timer); reject(new Error("Browser exited early: " + code)); });
  });

  const browser = client(await connect(browserWs));
  let page;
  try {
    const { targetId } = await browser.send("Target.createTarget", { url: "about:blank" });
    const port = new URL(browserWs).port;
    page = client(await connect(`ws://127.0.0.1:${port}/devtools/page/${targetId}`));
    page.on("Runtime.exceptionThrown", params => consoleErrors.push(params.exceptionDetails?.text || "Runtime exception"));
    page.on("Log.entryAdded", params => { if (params.entry?.level === "error") consoleErrors.push(params.entry.text); });
    await page.send("Page.enable");
    await page.send("Runtime.enable");
    await page.send("Log.enable");
    await page.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await page.send("Page.navigate", { url: pathToFileURL(path.join(root, "showcase.html")).href });
    await waitFor(page, "document.readyState === 'complete' && !!document.querySelector('#step-1')");

    const initial = await evaluate(page, `(() => ({
      protocol: location.protocol,
      title: document.title,
      visible: [...document.querySelectorAll('.step-panel')].filter(p => !p.hidden).map(p => p.id),
      resources: performance.getEntriesByType('resource').map(r => r.name),
      panels: document.querySelectorAll('.step-panel').length
    }))()`);
    record("离线 file:// 加载", initial.protocol === "file:" && initial.panels === 6 && initial.visible.join() === "step-1", JSON.stringify(initial.visible));
    record("无外部静态资源请求", initial.resources.every(url => !/^https?:/i.test(url)), initial.resources.length + " 个资源请求");

    const desktop = await evaluate(page, `(() => {
      const overflow = [];
      for (let i = 0; i < 6; i++) {
        document.querySelector('.step-button[data-step="' + i + '"]').click();
        const visible = [...document.querySelectorAll('.step-panel')].filter(p => !p.hidden).map(p => p.id).join();
        if (visible !== 'step-' + (i + 1)) overflow.push('navigation:' + i);
        if (document.documentElement.scrollWidth > window.innerWidth + 1) overflow.push('desktop-overflow:' + (i + 1));
      }
      return overflow;
    })()`);
    record("六步导航与桌面布局", desktop.length === 0, desktop.length ? desktop.join(", ") : "6/6 步可切换，无页面级横向溢出");

    const stages = await evaluate(page, `(() => {
      document.querySelector('.step-button[data-step="2"]').click();
      document.querySelector('[data-stage="pass2"]').click();
      return {
        pass2: !document.getElementById('stage-pass2').hidden,
        beforeHidden: document.getElementById('stage-before').hidden,
        selected: document.querySelector('[data-stage="pass2"]').getAttribute('aria-selected')
      };
    })()`);
    record("AI 阶段对照交互", stages.pass2 && stages.beforeHidden && stages.selected === "true", JSON.stringify(stages));

    const filter = await evaluate(page, `(() => {
      document.querySelector('.step-button[data-step="4"]').click();
      const input = document.getElementById('evidence-filter');
      input.value = 'MBI';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      return {
        visible: [...document.querySelectorAll('.evidence-row')].filter(r => !r.hidden).length,
        status: document.getElementById('filter-status').textContent
      };
    })()`);
    record("证据筛选", filter.visible === 1 && filter.status.includes("1 / 6"), JSON.stringify(filter));

    const outline = await evaluate(page, `(() => {
      document.querySelector('.step-button[data-step="5"]').click();
      document.getElementById('expand-outline').click();
      return {
        open: [...document.querySelectorAll('.outline-slide')].filter(d => d.open).length,
        citations: document.querySelectorAll('.outline-slide .citation').length
      };
    })()`);
    record("组会大纲展开与出处", outline.open === 8 && outline.citations === 8, JSON.stringify(outline));

    await page.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    const mobile = await evaluate(page, `(() => {
      const overflow = [];
      for (let i = 0; i < 6; i++) {
        document.querySelector('.step-button[data-step="' + i + '"]').click();
        if (document.documentElement.scrollWidth > window.innerWidth + 1) overflow.push(i + 1);
      }
      return overflow;
    })()`);
    record("390px 移动布局", mobile.length === 0, mobile.length ? "溢出步骤：" + mobile.join(",") : "6/6 步无页面级横向溢出");
    record("浏览器控制台", consoleErrors.length === 0, consoleErrors.length ? consoleErrors.join(" | ") : "0 个错误");

    const result = {
      date: new Date().toISOString().slice(0, 10),
      status: checks.every(check => check.pass) ? "PASS" : "FAIL",
      browser: await evaluate(page, "navigator.userAgent"),
      checks,
      consoleErrors
    };
    writeFileSync(resultPath, JSON.stringify(result, null, 2) + "\n", "utf8");
    await browser.send("Browser.close");
    if (result.status !== "PASS") throw new Error("Browser smoke test failed; see result JSON");
    console.log(`PASS: ${checks.length} 项浏览器检查；结果 99附件/浏览器验证.json`);
  } finally {
    if (page) page.close();
    browser.close();
  }
}

run().catch(error => {
  if (!checks.some(check => check.name === "运行错误")) {
    writeFileSync(resultPath, JSON.stringify({ date: new Date().toISOString().slice(0, 10), status: "FAIL", checks, error: String(error), consoleErrors }, null, 2) + "\n", "utf8");
  }
  if (child && !child.killed) child.kill();
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
