(function() {
  'use strict';

  const ORIGIN = window.location.origin;
  const IS_EX = ORIGIN.includes('exhentai');

  const REGEX = {
    imageURL: [
      /<a href="(\S+?\/fullimg(?:\.php\?|\/)\S+?)"/i,
      /<img id="img" src="(\S+?)"/i,
      /<\/(?:script|iframe)><a[\s\S]+?><img src="(\S+?)"/i,
      /<img[^>]+src="(\S+?)"[^>]*id="img"/i,
      /fullimg\.php\?[^"']+['"][^>]*href="(\S+?)"/i,
    ],
    nextPage: [
      /<a id="next"[\s\S]+?href="(\S+?\/s\/\S+?)"/i,
      /<a href="(\S+?\/s\/\S+?)"><img src="https?:\/\/ehgt\.org\/g\/n\.png"/i,
    ],
    pagesLength: /([\d,]+)\s*<\/a>[^<]*<\/td><td[^>]*>\s*<\/td>\s*<td[^>]*>\s*<\/td>\s*<\/tr>\s*<\/table>\s*<\/td>\s*<td\s+class="gdt2">/,
    pagesLength2: /<table class="ptt".+?>(\d+)<\/a>.+?<\/table>/,
    galleryTitle: /<h1[^>]*id="gn"[^>]*>([\s\S]*?)<\/h1>/i,
    galleryTitle2: /<h1[^>]*>([\s\S]*?)<\/h1>/i,
    firstPageLink: /<a[^>]*href="(\/s\/[^"]+)"[^>]*><img[^>]+alt="([^"]+)"|<a[^>]*href="(\/s\/[^"]+)"[^>]*><div[^>]+class="gdt2"[^>]*>/i,
    dangerChars: /[:"*?|<>\/\\\n]/g,
  };

  let settings = {}, imageList = [], imageData = [], retryCountMap = {};
  let isDownloading = false, isPaused = false, downloadAbort = false;
  let downloadedCount = 0, failedCount = 0, fetchCount = 0, totalCount = 0;
  let pagesRange = [], needNumberImages = false, galleryTitle = '';

  let rateLimitState = {
    consecutive429: 0, consecutiveErrors: 0, totalErrors: 0,
    lastErrorTime: 0, currentDelay: 800, banDetected: false,
    banUntil: 0, totalRequests: 0, successfulRequests: 0, adaptiveMultiplier: 1,
  };

  function bg(type, data) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type, ...data }, (resp) => {
        if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
        else if (resp && resp.ok) resolve(resp);
        else reject(new Error((resp && resp.error) || 'Unknown error'));
      });
    });
  }

  function isPeakHours() {
    const now = new Date(), d = now.getUTCDay(), h = now.getUTCHours();
    return d === 0 ? (h >= 5 && h < 20) : (h >= 14 && h < 20);
  }

  function getGalleryAgeDays() {
    const m = document.documentElement.innerHTML.match(/Posted:<\/td><td[^>]*>(.*?)<\/td>/);
    if (!m) return 999;
    return Math.floor((Date.now() - Date.parse(m[1].trim() + '+0000')) / 86400000);
  }

  function calcDelay() {
    let d = settings.delayBetweenImages || 800;
    if (rateLimitState.consecutiveErrors > 0) {
      d = Math.min(d * Math.pow(2, Math.min(rateLimitState.consecutiveErrors, 6)), settings.maxDelay || 15000);
    }
    if (rateLimitState.consecutive429 > 0) {
      d = Math.max(d, 3000 * rateLimitState.consecutive429);
    }
    if (isPeakHours()) d = Math.max(d, d * 1.5);
    if (rateLimitState.totalRequests > 10) {
      const sr = rateLimitState.successfulRequests / rateLimitState.totalRequests;
      if (sr < 0.8) rateLimitState.adaptiveMultiplier = Math.min(rateLimitState.adaptiveMultiplier * 1.2, 3);
      else if (sr > 0.95) rateLimitState.adaptiveMultiplier = Math.max(rateLimitState.adaptiveMultiplier * 0.95, 1);
      d = Math.round(d * rateLimitState.adaptiveMultiplier);
    }
    rateLimitState.currentDelay = d;
    return d;
  }

  function log(msg, type = '') {
    const el = document.getElementById('ehd-log');
    if (!el) return;
    el.style.display = 'block';
    const e = document.createElement('div');
    e.className = 'ehd-log-entry' + (type ? ' ' + type : '');
    e.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    el.appendChild(e);
    el.scrollTop = el.scrollHeight;
  }

  function status(msg) {
    const el = document.getElementById('ehd-status');
    if (el) el.textContent = msg;
  }

  function progress(cur, total) {
    const c = document.getElementById('ehd-progress-container');
    const f = document.getElementById('ehd-progress-fill');
    const t = document.getElementById('ehd-progress-text');
    if (!c || !f || !t) return;
    c.style.display = 'block';
    const p = total > 0 ? Math.round((cur / total) * 100) : 0;
    f.style.width = p + '%';
    t.textContent = `${cur} / ${total} (${p}%)`;
  }

  function buttons(dl) {
    const s = document.getElementById('ehd-start-btn');
    const p = document.getElementById('ehd-pause-btn');
    const st = document.getElementById('ehd-stop-btn');
    const r = document.getElementById('ehd-range-input');
    if (s) s.disabled = dl;
    if (p) p.disabled = !dl;
    if (st) st.disabled = !dl;
    if (r) r.disabled = dl;
  }

  function safeName(str) {
    return settings.replaceDangerChars !== false
      ? str.trim().replace(REGEX.dangerChars, '-').replace(/-{2,}/g, '-')
      : str.trim();
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  async function startDownload() {
    if (isDownloading) return;
    const rs = document.getElementById('ehd-range-input')?.value || '';
    pagesRange = parseRange(rs);
    needNumberImages = document.getElementById('ehd-number-check')?.checked || false;

    rateLimitState = { consecutive429: 0, consecutiveErrors: 0, totalErrors: 0,
      lastErrorTime: 0, currentDelay: settings.delayBetweenImages || 800,
      banDetected: false, banUntil: 0, totalRequests: 0,
      successfulRequests: 0, adaptiveMultiplier: 1 };

    isDownloading = true; isPaused = false; downloadAbort = false;
    downloadedCount = 0; failedCount = 0; fetchCount = 0;
    retryCountMap = {}; imageList = []; imageData = [];
    buttons(true);

    const age = getGalleryAgeDays();
    if (isPeakHours()) log('PEAK HOURS (14-20 UTC) - descarga m�s lenta.', 'error');
    if (age < 30) log(`Galer�a reciente (${age} d�as) - delay extra.`, 'info');

    log('Iniciando descarga...', 'info');
    try {
      await collectAllPages();
      if (imageList.length === 0) { log('No se encontraron im�genes.', 'error'); status('Error: 0 im�genes'); return; }
      log(`${imageList.length} im�genes encontradas.`, 'info');
      status(`Descargando ${imageList.length} im�genes...`);

      await downloadAllImages();
      if (downloadAbort) return;

      log('Creando ZIP...', 'info');
      status('Creando ZIP...');
      await createZip();
      log('ZIP guardado.', 'success');
      status('�Completado!');
    } catch (err) {
      log(`Error: ${err.message}`, 'error');
      status('Error: ' + err.message);
    }
    isDownloading = false; buttons(false);
    progress(downloadedCount, totalCount);
  }

  async function collectAllPages() {
    const html = document.documentElement.outerHTML;

    // Get total pages from pagination
    let totalPages = 1;
    const pt = html.match(REGEX.pagesLength);
    if (pt) totalPages = parseInt(pt[1].replace(/,/g, ''), 10);
    else {
      const pt2 = html.match(REGEX.pagesLength2);
      if (pt2) totalPages = parseInt(pt2[1], 10);
    }

    // Get gallery title
    const t = html.match(REGEX.galleryTitle);
    galleryTitle = t ? t[1].trim() : 'E-Hentai Gallery';
    log(`Galer�a: "${galleryTitle}" (${totalPages} p�ginas)`, 'info');

    // Parse first image page from gallery page
    let firstPageURL = null;
    const fp = html.match(REGEX.firstPageLink);
    if (fp && fp[1]) firstPageURL = fp[1];
    else if (fp && fp[3]) firstPageURL = fp[3];

    if (!firstPageURL) {
      // Try to find first image link from the gallery thumbnails
      const links = html.match(/<a[^>]*href="(\/s\/[^"]+)"[^>]*>/g);
      if (links && links.length > 0) {
        const m = links[0].match(/href="(\/s\/[^"]+)"/);
        if (m) { firstPageURL = m[1]; }
      }
    }

    if (!firstPageURL) { log('No se pudo encontrar el enlace a la primera imagen.', 'error'); return; }

    // Special case: try to extract image URL directly from gallery page
    // Gallery pages sometimes embed inline images
    const inlineImg = html.match(/<img[^>]+src="(https?:\/\/[^"]+\.(?:jpg|jpeg|png|gif|webp)[^"]*)"[^>]*class="gdt"/i);
    const inlineImg2 = html.match(/<img[^>]+src="(https?:\/\/[^"]+)"[^>]*style="[^"]*max-width[^"]*"/i);

    let currentURL = resolveURL(firstPageURL);
    let pageNum = 1;

    while (currentURL && pageNum <= totalPages) {
      if (downloadAbort) break;
      if (!isInRange(pageNum)) { pageNum++; continue; }
      if (pageNum > 1) await sleep(Math.max(200, calcDelay() * 0.3));

      let pageHTML = null;
      for (let r = 0; r < 3; r++) {
        try {
          const res = await bg('FETCH_HTML', { url: currentURL });
          if (res.status === 429 || res.status === 403) {
            rateLimitState.consecutive429++;
            rateLimitState.consecutiveErrors++;
            const w = Math.min(30000, 3000 * rateLimitState.consecutive429);
            log(`Rate limit (${res.status}) - esperando ${Math.round(w/1000)}s...`, 'error');
            await sleep(w);
            continue;
          }
          pageHTML = res.html;
          rateLimitState.consecutiveErrors = 0;
          break;
        } catch (e) {
          rateLimitState.consecutiveErrors++;
          log(`Error p�gina ${pageNum} (${r+1}/3): ${e.message}`, 'error');
          await sleep(calcDelay());
        }
      }
      if (!pageHTML) { log(`Fallo p�gina ${pageNum}, deteniendo.`, 'error'); break; }
      if (pageHTML.length < 100) { log(`P�gina ${pageNum} vac�a, deteniendo.`, 'error'); break; }

      // Extract image URL
      let imgURL = null;
      let nextURL = null;
      const status404 = pageHTML.includes('This image or gallery has been removed');

      // Parse image URL from various patterns
      for (const re of REGEX.imageURL) {
        const m = pageHTML.match(re);
        if (m) { imgURL = m[1]; break; }
      }

      // If no normal image URL found, try to get from inline page data
      if (!imgURL) {
        const imgTag = pageHTML.match(/<img[^>]+src="(https?:\/\/[^"]+)"[^>]*>/i);
        if (imgTag) {
          const src = imgTag[1];
          if (!src.includes('ehgt.org') && !src.includes('gif')) imgURL = src;
        }
      }

      // If still no image URL, check if the page might have a .gallery embed
      if (!imgURL && status404) {
        log(`P�gina ${pageNum}: imagen removida.`, 'error');
        pageNum++;
        currentURL = null;
        break;
      }

      // Parse next page URL
      for (const re of REGEX.nextPage) {
        const m = pageHTML.match(re);
        if (m) { nextURL = m[1]; break; }
      }
      if (!nextURL) {
        const nextLink = pageHTML.match(/<a[^>]+id="next"[^>]+href="([^"]+)"/i);
        if (nextLink) nextURL = nextLink[1];
      }

      if (imgURL) {
        imageList.push({
          pageURL: currentURL.split('?')[0],
          imageURL: imgURL,
          index: pageNum,
          imageName: imgURL.split('/').pop().split('?')[0] || `image_${pageNum}.jpg`,
        });
        rateLimitState.totalRequests++;
      }

      currentURL = nextURL ? resolveURL(nextURL) : null;
      pageNum++;
    }

    totalCount = imageList.length;
    progress(0, totalCount);
    log(`Total: ${totalCount} im�genes recolectadas.`, 'info');
  }

  function resolveURL(url) {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    if (url.startsWith('/')) return ORIGIN + url;
    return ORIGIN + '/' + url;
  }

  function isInRange(n) {
    if (!pagesRange || pagesRange.length === 0) return true;
    for (const r of pagesRange) { if (n >= r[0] && n <= r[1]) return true; }
    return false;
  }

  function parseRange(s) {
    if (!s || !s.trim()) return [];
    return s.split(',').map(p => {
      const m = p.trim().match(/^(\d+)(?:-(\d+))?$/);
      return m ? [parseInt(m[1], 10), m[2] ? parseInt(m[2], 10) : parseInt(m[1], 10)] : null;
    }).filter(Boolean);
  }

  async function downloadAllImages() {
    const maxT = Math.min(settings.maxThreads || 3, 5);
    const queue = [...imageList];
    const workers = [];
    for (let i = 0; i < maxT; i++) workers.push(downloadWorker(queue));
    await Promise.all(workers);
  }

  async function downloadWorker(queue) {
    while (queue.length > 0) {
      if (downloadAbort) break;
      if (isPaused) { await sleep(500); continue; }

      const item = queue.shift();
      if (!item) break;

      fetchCount++;
      let success = false;
      for (let r = 0; r <= settings.retryCount && !success && !downloadAbort; r++) {
        try {
          const res = await bg('FETCH_IMAGE', { url: item.imageURL, index: item.index });
          const bin = atob(res.data);
          const buf = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
          imageData[item.index - 1] = buf;
          downloadedCount++;
          rateLimitState.successfulRequests++;
          success = true;
          log(`[${item.index}/${totalCount}] OK ${(r > 0 ? `(${r+1} intentos) ` : '')}${item.imageName}`, 'success');
        } catch (e) {
          if (e.message.includes('429') || e.message.includes('403')) {
            rateLimitState.consecutive429++;
            rateLimitState.consecutiveErrors++;
          } else {
            rateLimitState.consecutiveErrors++;
          }
          if (r < settings.retryCount) {
            const wait = calcDelay();
            log(`[${item.index}/${totalCount}] Retry ${r+1}/${settings.retryCount}: ${e.message} (espera ${Math.round(wait/1000)}s)`, 'error');
            await sleep(wait);
          }
        }
      }
      if (!success) {
        failedCount++;
        log(`[${item.index}/${totalCount}] FALL�`, 'error');
      }
      fetchCount--;
      progress(downloadedCount + failedCount, totalCount);
      status(`${downloadedCount} OK / ${failedCount} fail / ${totalCount - downloadedCount - failedCount} restantes | delay: ${Math.round(rateLimitState.currentDelay/1000)}s`);
      await sleep(calcDelay());
    }
  }

  async function createZip() {
    const zip = new JSZip();
    const title = safeName(galleryTitle);
    let info = `Title: ${galleryTitle}\nURL: ${window.location.href}\nGID: ${(document.documentElement.innerHTML.match(/var gid\s*=\s*(\d+)/) || ['', ''])[1]}\nAge: ${getGalleryAgeDays()} days\nDownloaded: ${new Date().toISOString()}\n\nGenerated by E-Hentai Downloader\n`;

    if (imageList.length > 0) {
      if (settings.savePageLinks !== false) {
        info += '\nPages:\n';
        for (const item of imageList) {
          if (item) info += `  ${item.index}: ${item.pageURL}\n`;
        }
      }
      zip.file('info.txt', info);
      for (let i = 0; i < imageList.length; i++) {
        if (imageData[i]) {
          let name;
          if (needNumberImages) {
            const num = String(i + 1).padStart(3, '0');
            const sep = settings.numberSeparator || ': ';
            name = num + sep + imageList[i].imageName;
          } else {
            name = imageList[i].imageName || `image_${i + 1}.jpg`;
          }
          zip.file(name, imageData[i], { binary: true, createFolders: false });
        }
      }
    }

    const content = await zip.generateAsync({ type: 'base64', compression: 'DEFLATE', compressionOptions: { level: 6 } });
    await bg('DOWNLOAD_ZIP', { zipBase64: content, fileName: title, saveAsCbz: settings.saveAsCbz });
    imageData = [];
  }

  function injectUI() {
    if (document.getElementById('ehd-box')) return;
    const html = document.documentElement.innerHTML;
    const t = html.match(REGEX.galleryTitle);
    galleryTitle = t ? t[1].trim() : getGalleryTitle();
    console.log('[EHD] Injecting UI:', galleryTitle);

    const c = document.createElement('div');
    c.className = 'ehd-box';
    c.innerHTML = `
      <fieldset>
        <legend>E-Hentai Downloader</legend>
        <div class="ehd-actions">
          <button id="ehd-start-btn" class="ehd-btn ehd-btn-primary">Download Gallery</button>
          <button id="ehd-pause-btn" class="ehd-btn" disabled>Pause</button>
          <button id="ehd-stop-btn" class="ehd-btn ehd-btn-danger" disabled>Stop</button>
          <span style="color:#b2a89e">|</span>
          <label class="ehd-label"><input type="checkbox" id="ehd-number-check"> Number</label>
          <label class="ehd-label">Range: <input type="text" id="ehd-range-input" class="ehd-input" placeholder="1-5,10-15" style="width:130px" disabled></label>
          <span style="color:#b2a89e">|</span>
          <button id="ehd-settings-btn" class="ehd-btn">Settings</button>
          <button id="ehd-log-toggle" class="ehd-btn">Log</button>
        </div>
        <div id="ehd-rate-status" style="display:none"></div>
        <div id="ehd-status" class="ehd-status">Ready</div>
        <div id="ehd-progress-container" class="ehd-progress-container">
          <div class="ehd-progress-bar"><div id="ehd-progress-fill" class="ehd-progress-fill"></div><div id="ehd-progress-text" class="ehd-progress-text">0 / 0</div></div>
        </div>
        <div id="ehd-settings-panel" class="ehd-settings-panel">
          <table style="width:100%;border-collapse:collapse">
            <tr><td style="padding:2px 6px;font-size:11px;color:#555;white-space:nowrap">Threads:</td><td style="padding:2px 6px"><input type="number" id="ehd-threads" class="ehd-input" value="${settings.maxThreads || 3}" min="1" max="5"></td>
            <td style="padding:2px 6px;font-size:11px;color:#555;white-space:nowrap">Retries:</td><td style="padding:2px 6px"><input type="number" id="ehd-retries" class="ehd-input" value="${settings.retryCount || 3}" min="0" max="10"></td></tr>
            <tr><td style="padding:2px 6px;font-size:11px;color:#555;white-space:nowrap">Base delay (ms):</td><td style="padding:2px 6px"><input type="number" id="ehd-delay" class="ehd-input" value="${settings.delayBetweenImages || 800}" min="300" max="5000" step="100"></td>
            <td style="padding:2px 6px;font-size:11px;color:#555;white-space:nowrap">Max delay (ms):</td><td style="padding:2px 6px"><input type="number" id="ehd-maxdelay" class="ehd-input" value="${settings.maxDelay || 15000}" min="5000" max="60000" step="1000"></td></tr>
            <tr><td style="padding:2px 6px;font-size:11px;color:#555;white-space:nowrap">Ban pause (min):</td><td style="padding:2px 6px"><input type="number" id="ehd-banpause" class="ehd-input" value="${settings.banPauseMinutes || 5}" min="1" max="30"></td>
            <td style="padding:2px 6px;font-size:11px;color:#555;white-space:nowrap">Separator:</td><td style="padding:2px 6px"><input type="text" id="ehd-separator" class="ehd-input" value="${settings.numberSeparator || ': '}"></td></tr>
          </table>
          <div style="margin-top:4px;display:flex;gap:14px;flex-wrap:wrap">
            <label class="ehd-label"><input type="checkbox" id="ehd-cbz-check"> Save as CBZ</label>
            <label class="ehd-label"><input type="checkbox" id="ehd-safefile-check" checked> Safe filenames</label>
            <label class="ehd-label"><input type="checkbox" id="ehd-infolist-check" checked> Include info.txt</label>
          </div>
        </div>
        <div id="ehd-log" class="ehd-log"></div>
      </fieldset>`;

    const targets = ['#gdt', '.gdt', '#gd2', '#gd', '#download', '.gm'];
    let ins = false;
    for (const sel of targets) {
      const t = document.querySelector(sel);
      if (t) { t.parentNode.insertBefore(c, t); ins = true; break; }
    }
    if (!ins) {
      const gm = document.querySelector('.gm');
      if (gm) gm.appendChild(c);
      else document.body.prepend(c);
    }

    bind('ehd-start-btn', startDownload, 'click');
    bind('ehd-pause-btn', () => { isPaused = !isPaused; const b = document.getElementById('ehd-pause-btn'); if (b) { b.textContent = isPaused ? 'Resume' : 'Pause'; b.classList.toggle('ehd-btn-primary', !isPaused); b.classList.toggle('ehd-btn-success', isPaused); } log(isPaused ? 'Pausado.' : 'Reanudado.', 'info'); }, 'click');
    bind('ehd-stop-btn', () => { downloadAbort = true; isPaused = false; isDownloading = false; buttons(false); log('Detenido por usuario.', 'error'); status('Detenido.'); }, 'click');
    bind('ehd-settings-btn', togglePanel, 'click');
    bind('ehd-log-toggle', () => { const l = document.getElementById('ehd-log'); if (l) l.style.display = l.style.display === 'block' ? 'none' : 'block'; }, 'click');
    bind('ehd-threads', (e) => { settings.maxThreads = Math.min(parseInt(e.target.value) || 3, 5); save(); });
    bind('ehd-retries', (e) => { settings.retryCount = parseInt(e.target.value) || 3; save(); });
    bind('ehd-delay', (e) => { settings.delayBetweenImages = Math.max(parseInt(e.target.value) || 800, 300); save(); });
    bind('ehd-maxdelay', (e) => { settings.maxDelay = parseInt(e.target.value) || 15000; save(); });
    bind('ehd-banpause', (e) => { settings.banPauseMinutes = parseInt(e.target.value) || 5; save(); });
    bind('ehd-separator', (e) => { settings.numberSeparator = e.target.value || ': '; save(); });
    bind('ehd-cbz-check', (e) => { settings.saveAsCbz = e.target.checked; save(); });
    bind('ehd-safefile-check', (e) => { settings.replaceDangerChars = e.target.checked; save(); });
    bind('ehd-infolist-check', (e) => { settings.savePageLinks = e.target.checked; save(); });
    bind('ehd-number-check', (e) => { settings.numberImages = e.target.checked; save(); });

    chrome.runtime.sendMessage({ type: 'GET_SETTINGS' }, (r) => {
      if (r) { settings = r; applyUI(); }
    });
  }

  function bind(id, fn, eventType) {
    const el = document.getElementById(id);
    if (el) el.addEventListener(eventType || 'change', fn);
  }

  function togglePanel() {
    const p = document.getElementById('ehd-settings-panel');
    if (p) p.style.display = p.style.display === 'block' ? 'none' : 'block';
  }

  function applyUI() {
    const g = (id) => document.getElementById(id);
    if (g('ehd-threads')) g('ehd-threads').value = settings.maxThreads;
    if (g('ehd-retries')) g('ehd-retries').value = settings.retryCount;
    if (g('ehd-delay')) g('ehd-delay').value = settings.delayBetweenImages;
    if (g('ehd-maxdelay')) g('ehd-maxdelay').value = settings.maxDelay;
    if (g('ehd-banpause')) g('ehd-banpause').value = settings.banPauseMinutes;
    if (g('ehd-separator')) g('ehd-separator').value = settings.numberSeparator;
    if (g('ehd-cbz-check')) g('ehd-cbz-check').checked = settings.saveAsCbz;
    if (g('ehd-safefile-check')) g('ehd-safefile-check').checked = settings.replaceDangerChars !== false;
    if (g('ehd-infolist-check')) g('ehd-infolist-check').checked = settings.savePageLinks !== false;
    if (g('ehd-number-check')) g('ehd-number-check').checked = settings.numberImages;
  }

  function save() { chrome.runtime.sendMessage({ type: 'SAVE_SETTINGS', settings }); }

  function getGalleryTitle() {
    const gn = document.getElementById('gn');
    const gj = document.getElementById('gj');
    if (gj && gj.textContent.trim()) return gj.textContent.trim();
    if (gn && gn.textContent.trim()) return gn.textContent.trim();
    return 'E-Hentai Gallery';
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', injectUI);
  else injectUI();
})();
