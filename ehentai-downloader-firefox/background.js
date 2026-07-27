chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'FETCH_HTML') {
    handleFetchHtml(message, sender, sendResponse);
    return true;
  }
  if (message.type === 'FETCH_IMAGE') {
    handleFetchImage(message, sender, sendResponse);
    return true;
  }
  if (message.type === 'DOWNLOAD_ZIP') {
    handleDownloadZip(message, sender, sendResponse);
    return true;
  }
  if (message.type === 'GET_SETTINGS') {
    chrome.storage.sync.get('settings', (data) => {
      sendResponse(data.settings || getDefaultSettings());
    });
    return true;
  }
  if (message.type === 'SAVE_SETTINGS') {
    chrome.storage.sync.set({ settings: message.settings }, () => {
      sendResponse({ ok: true });
    });
    return true;
  }
});

function getDefaultSettings() {
  return {
    numberImages: false, numberSeparator: ': ', maxThreads: 3,
    retryCount: 3, delayBetweenImages: 800, saveAsCbz: false,
    autoStart: false, replaceDangerChars: true, savePageLinks: true,
    smartThrottle: true, maxDelay: 15000, banPauseMinutes: 5,
  };
}

async function handleFetchHtml(message, sender, sendResponse) {
  try {
    const resp = await fetch(message.url, { credentials: 'same-origin' });
    const text = await resp.text();
    sendResponse({ ok: true, html: text, status: resp.status });
  } catch (err) {
    sendResponse({ ok: false, error: err.message });
  }
}

async function handleFetchImage(message, sender, sendResponse) {
  try {
    const resp = await fetch(message.url, {
      credentials: 'same-origin',
      headers: { 'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8' }
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const buffer = await resp.arrayBuffer();
    const b64 = arrayBufferToBase64(buffer);
    const ct = resp.headers.get('content-type') || '';
    let ext = '.jpg';
    if (ct.includes('png')) ext = '.png';
    else if (ct.includes('webp')) ext = '.webp';
    else if (ct.includes('gif')) ext = '.gif';
    else if (ct.includes('jpeg')) ext = '.jpg';

    sendResponse({ ok: true, data: b64, ext: ext });
  } catch (err) {
    sendResponse({ ok: false, error: err.message });
  }
}

async function handleDownloadZip(message, sender, sendResponse) {
  try {
    const binaryStr = atob(message.zipBase64);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
    const blob = new Blob([bytes], { type: 'application/zip' });
    const url = URL.createObjectURL(blob);
    const ext = message.saveAsCbz ? '.cbz' : '.zip';
    await chrome.downloads.download({ url: url, filename: message.fileName + ext, saveAs: false });
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    sendResponse({ ok: true });
  } catch (err) {
    sendResponse({ ok: false, error: err.message });
  }
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  const chunkSize = 8192;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}
