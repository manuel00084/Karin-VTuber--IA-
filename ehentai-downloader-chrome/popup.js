document.addEventListener('DOMContentLoaded', () => {
  chrome.runtime.sendMessage({ type: 'GET_SETTINGS' }, (s) => {
    if (!s) return;
    document.getElementById('threads').value = s.maxThreads || 3;
    document.getElementById('retries').value = s.retryCount || 3;
    document.getElementById('delay').value = s.delayBetweenImages || 800;
    document.getElementById('numberImages').checked = s.numberImages || false;
    document.getElementById('saveAsCbz').checked = s.saveAsCbz || false;
    document.getElementById('savePageLinks').checked = s.savePageLinks !== false;
    document.getElementById('replaceChars').checked = s.replaceDangerChars !== false;
  });
  document.getElementById('saveBtn').addEventListener('click', () => {
    const s = {
      numberImages: document.getElementById('numberImages').checked,
      numberSeparator: ': ',
      maxThreads: Math.min(parseInt(document.getElementById('threads').value) || 3, 5),
      retryCount: parseInt(document.getElementById('retries').value) || 3,
      delayBetweenImages: Math.max(parseInt(document.getElementById('delay').value) || 800, 300),
      saveAsCbz: document.getElementById('saveAsCbz').checked,
      autoStart: false,
      replaceDangerChars: document.getElementById('replaceChars').checked,
      savePageLinks: document.getElementById('savePageLinks').checked,
      smartThrottle: true, maxDelay: 15000, banPauseMinutes: 5,
    };
    chrome.runtime.sendMessage({ type: 'SAVE_SETTINGS', settings: s }, (r) => {
      const st = document.getElementById('status');
      if (r && r.ok) { st.textContent = 'Saved!'; st.style.color = '#2e6e3a'; setTimeout(() => { st.textContent = ''; }, 2000); }
      else { st.textContent = 'Error saving'; st.style.color = '#8b2e2e'; }
    });
  });
});
