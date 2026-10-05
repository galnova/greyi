const modesEl = document.getElementById('modes');
const promptEl = document.getElementById('prompt');
const negativeEl = document.getElementById('negative');
const negativeSection = document.getElementById('negativeSection');
const lyricsEl = document.getElementById('lyrics');
const lyricsSection = document.getElementById('lyricsSection');
const durationEl = document.getElementById('duration');
const durationSection = document.getElementById('durationSection');
const modelSection = document.getElementById('modelSection');
const modelSelect = document.getElementById('modelSelect');
const imageSection = document.getElementById('imageSection');
const dropzone = document.getElementById('dropzone');
const dropzoneLabel = document.getElementById('dropzoneLabel');
const imageInput = document.getElementById('imageInput');
const generateBtn = document.getElementById('generateBtn');
const statusEl = document.getElementById('status');
const resultsEl = document.getElementById('results');
const toastContainer = document.getElementById('toastContainer');

let modes = {};
let activeMode = null;
let uploadedFilename = null;

// --- persist the current prompt text across refreshes ---
const PROMPT_STORAGE_KEY = 'studio_prompt_draft';
try {
  const saved = localStorage.getItem(PROMPT_STORAGE_KEY);
  if (saved) promptEl.value = saved;
} catch (e) { /* localStorage unavailable (private window, etc.) - fine, just skip persistence */ }

promptEl.addEventListener('input', () => {
  try { localStorage.setItem(PROMPT_STORAGE_KEY, promptEl.value); } catch (e) {}
});

const LYRICS_STORAGE_KEY = 'studio_lyrics_draft';
try {
  const savedLyrics = localStorage.getItem(LYRICS_STORAGE_KEY);
  if (savedLyrics) lyricsEl.value = savedLyrics;
} catch (e) {}

lyricsEl.addEventListener('input', () => {
  try { localStorage.setItem(LYRICS_STORAGE_KEY, lyricsEl.value); } catch (e) {}
});

const DURATION_STORAGE_KEY = 'studio_duration_draft';
try {
  const savedDuration = localStorage.getItem(DURATION_STORAGE_KEY);
  if (savedDuration) durationEl.value = savedDuration;
} catch (e) {}

durationEl.addEventListener('input', () => {
  try { localStorage.setItem(DURATION_STORAGE_KEY, durationEl.value); } catch (e) {}
});

async function loadModes() {
  const res = await fetch('/api/modes');
  modes = await res.json();
  const order = ['text2text', 'text2image', 'image2image', 'text2video', 'image2video', 'text2music'];
  modesEl.innerHTML = '';
  for (const key of order) {
    const cfg = modes[key];
    if (!cfg) continue;
    const pill = document.createElement('div');
    pill.className = 'mode-pill' + (cfg.disabled ? ' disabled' : '');
    pill.textContent = cfg.label;
    pill.title = cfg.disabled ? cfg.disabled_reason : '';
    pill.onclick = () => { if (!cfg.disabled) selectMode(key); };
    pill.dataset.mode = key;
    modesEl.appendChild(pill);
  }
  selectMode(order.find(k => modes[k] && !modes[k].disabled));
}

function selectMode(key) {
  activeMode = key;
  [...modesEl.children].forEach(p => p.classList.toggle('active', p.dataset.mode === key));
  const cfg = modes[key];
  imageSection.style.display = cfg.needs_image ? 'block' : 'none';
  negativeSection.style.display = cfg.output_kind === 'text' ? 'none' : 'block';
  lyricsSection.style.display = cfg.needs_lyrics ? 'block' : 'none';

  if (cfg.needs_duration) {
    durationSection.style.display = 'block';
    if (cfg.duration_max) durationEl.max = cfg.duration_max;
    if (!durationEl.value) durationEl.value = cfg.duration_default || 60;
  } else {
    durationSection.style.display = 'none';
  }
  promptEl.placeholder = cfg.output_kind === 'text'
    ? 'Ask anything - coding help, questions, writing...'
    : 'Describe what you want...';

  if (cfg.models && cfg.models.length) {
    modelSection.style.display = 'block';
    modelSelect.innerHTML = cfg.models.map(m => `<option value="${m}">${m}</option>`).join('');
  } else {
    modelSection.style.display = 'none';
  }

  statusEl.textContent = '';
  statusEl.className = 'status';
}

dropzone.onclick = (e) => { if (e.target !== imageInput) imageInput.click(); };
imageInput.onchange = async () => {
  const file = imageInput.files[0];
  if (!file) return;
  await uploadImage(file);
};
dropzone.ondragover = (e) => { e.preventDefault(); dropzone.style.borderColor = 'var(--accent)'; };
dropzone.ondragleave = () => { dropzone.style.borderColor = ''; };
dropzone.ondrop = async (e) => {
  e.preventDefault();
  dropzone.style.borderColor = '';
  const file = e.dataTransfer.files[0];
  if (file) await uploadImage(file);
};

async function uploadImage(file) {
  dropzoneLabel.textContent = 'Uploading...';
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/api/upload', { method: 'POST', body: fd });
  const data = await res.json();
  uploadedFilename = data.name;
  dropzone.classList.add('has-image');
  dropzone.innerHTML = `<img src="${URL.createObjectURL(file)}"><input type="file" id="imageInput" accept="image/*">`;
  document.getElementById('imageInput').onchange = imageInput.onchange;
}

generateBtn.onclick = async () => {
  const cfg = modes[activeMode];
  const promptText = promptEl.value.trim();
  if (!promptText) { setStatus('Enter a prompt first.', 'error'); return; }
  if (cfg.needs_image && !uploadedFilename) { setStatus('Upload a reference image first.', 'error'); return; }

  generateBtn.disabled = true;
  setStatus('Queuing...', '');

  const fd = new FormData();
  fd.append('mode', activeMode);
  fd.append('prompt', promptText);
  fd.append('negative', negativeEl.value.trim());
  if (uploadedFilename) fd.append('image_filename', uploadedFilename);
  if (cfg.models && cfg.models.length) fd.append('model', modelSelect.value);
  if (cfg.needs_lyrics) fd.append('lyrics', lyricsEl.value.trim());
  if (cfg.needs_duration) fd.append('duration', durationEl.value || cfg.duration_default || 60);

  try {
    const res = await fetch('/api/generate', { method: 'POST', body: fd });
    if (!res.ok) throw new Error(await res.text());
    const { job_id } = await res.json();
    poll(job_id, cfg.output_kind);
  } catch (e) {
    setStatus('Failed to queue: ' + e.message, 'error');
    showToast('Failed to queue: ' + e.message, 'error');
    generateBtn.disabled = false;
  }
};

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className = 'status' + (cls ? ' ' + cls : '');
}

function showToast(text, type) {
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.textContent = text;
  toastContainer.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

async function poll(jobId, kind) {
  setStatus(kind === 'text' ? 'Thinking...' : 'Generating... this can take a while, especially for video.', '');
  while (true) {
    await new Promise(r => setTimeout(r, kind === 'text' ? 800 : 3000));
    const res = await fetch(`/api/status/${jobId}`);
    const data = await res.json();
    if (data.status === 'success') {
      setStatus('Done.', 'ok');
      showToast('Done - generation succeeded.', 'ok');
      generateBtn.disabled = false;
      if (kind === 'text') addTextResult(data.text, data.tokens_used, data.tokens_remaining, data.num_ctx);
      else addResults(data.outputs, kind);
      return;
    }
    if (data.status === 'error') {
      const detail = (data.detail && (data.detail.detail || data.detail.status_str)) || '';
      setStatus('Generation failed - check the ComfyUI console.', 'error');
      showToast('Generation failed' + (detail ? ': ' + detail : '.'), 'error');
      generateBtn.disabled = false;
      return;
    }
    setStatus((data.status === 'running' ? 'Generating...' : 'Queued...'), '');
  }
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function addTextResult(text, tokensUsed, tokensRemaining, numCtx) {
  const card = document.createElement('div');
  card.className = 'result-card';
  let meta = '';
  if (typeof tokensUsed === 'number') {
    meta = `<div class="token-meta">Tokens used: ${tokensUsed} &middot; remaining: ${tokensRemaining} / ${numCtx} context</div>`;
  }
  card.innerHTML = `<pre class="text-result">${escapeHtml(text)}</pre>${meta}`;
  resultsEl.prepend(card);
}

function addResults(outputs, kind) {
  for (const o of outputs) {
    const card = document.createElement('div');
    card.className = 'result-card';
    let media;
    if (kind === 'image') media = `<img src="${o.url}">`;
    else if (kind === 'video') media = `<video src="${o.url}" controls autoplay loop muted></video>`;
    else media = `<audio src="${o.url}" controls></audio>`;
    card.innerHTML = media + `<div class="result-meta">${o.filename}</div>`;
    resultsEl.prepend(card);
  }
}

loadModes();
