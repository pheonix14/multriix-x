/**
 * NeuralDesk — Modelfile Wizard
 * 5-step guided Modelfile creator
 */

const Wizard = (() => {
  let currentStep = 1;
  const TOTAL_STEPS = 5;
  let state = {
    baseModel: '',
    name: '',
    systemPrompt: '',
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    repeatPenalty: 1.1,
    maxTokens: 2048,
    contextWindow: 8192,
  };

  const PRESETS = {
    '[Pro] Professional': 'You are a professional assistant. Be formal, concise, and accurate. Avoid humor or informal language.',
    '[Fri] Friendly':     'You are a warm and friendly assistant. Be encouraging, use casual language, and make conversations enjoyable.',
    '[Cre] Creative':     'You are a creative and imaginative assistant. Think outside the box, use vivid language, and embrace unconventional ideas.',
    '[Tech] Technical':   'You are a technical expert. Provide precise, detailed technical answers with code examples when relevant.',
    '[Z] Concise':        'You are a concise assistant. Give short, direct answers. No filler words. Maximum clarity, minimum words.',
  };

  const DIRECTIVE_HELP = {
    'FROM':             'Which base model this AI is built on. Required.',
    'SYSTEM':           'Instructions that define how this AI behaves. The AI always follows these.',
    'PARAMETER temperature': 'Controls randomness. Higher = more creative, lower = more focused.',
    'PARAMETER top_p':       'Limits word choices to the most likely options.',
    'PARAMETER top_k':       'Maximum number of words considered at each step.',
    'PARAMETER num_ctx':     'How much conversation the AI remembers.',
    'PARAMETER num_predict': 'Maximum words the AI will write per response.',
    'PARAMETER repeat_penalty': 'Reduces repetition. Higher = less repetition.',
  };

  function open() {
    if (document.getElementById('wizard-overlay')) return;

    const allModels = (window._allModels || []).map(m =>
      `<option value="${m.name}">${m.name}</option>`
    ).join('') || '<option>No models installed</option>';

    const overlay = document.createElement('div');
    overlay.id = 'wizard-overlay';
    overlay.className = 'wizard-overlay';
    overlay.innerHTML = `
      <div class="wizard-box">
        <div class="wizard-header">
          <span style="font-size:24px; font-family:var(--font-mono)">[+]</span>
          <div class="wizard-title">Create New AI Personality</div>
          <span class="wizard-close" onclick="Wizard.close()">✕</span>
        </div>

        <!-- Step indicators -->
        <div class="wizard-steps" id="wizard-steps-bar">
          ${[1,2,3,4,5].map(n => `
            <div class="wizard-step-dot${n === 1 ? ' active' : ''}" data-step="${n}" onclick="Wizard.goStep(${n})">
              <div class="step-circle">${n}</div>
              <div class="step-label">${['Base','Personality','Style','Preview','Create'][n-1]}</div>
            </div>`).join('')}
        </div>

        <div class="wizard-body">
          <!-- Step 1: Base Model -->
          <div class="wizard-step-content active" data-step="1">
            <h3 style="font-weight:600; margin-bottom:var(--sp-2);">Which model is this based on?</h3>
            <p class="text-sm text-secondary" style="margin-bottom:var(--sp-4);">Choose the AI model that your new personality will be built on top of.</p>
            <select class="input" id="wiz-base-model" style="margin-bottom:var(--sp-3);">
              ${allModels}
            </select>
            <div id="wiz-model-info" class="card card-pad text-sm text-secondary" style="display:none;"></div>
          </div>

          <!-- Step 2: Name & Personality -->
          <div class="wizard-step-content" data-step="2">
            <h3 style="font-weight:600; margin-bottom:var(--sp-2);">Name & Personality</h3>
            <p class="text-sm text-secondary" style="margin-bottom:var(--sp-4);">Give your AI a name and tell it how to behave.</p>
            <label class="text-sm" style="font-weight:500; display:block; margin-bottom:6px;">AI Name (used as model tag)</label>
            <input class="input" id="wiz-name" placeholder="e.g. my-assistant, coding-helper" style="margin-bottom:var(--sp-4);">
            <label class="text-sm" style="font-weight:500; display:block; margin-bottom:6px;">Quick Presets</label>
            <div class="preset-grid" id="preset-grid">
              ${Object.entries(PRESETS).map(([label, _]) => `
                <div class="preset-btn" onclick="Wizard.selectPreset('${label}')">${label}</div>
              `).join('')}
            </div>
            <label class="text-sm" style="font-weight:500; display:block; margin-top:var(--sp-4); margin-bottom:6px;">Behavior Instructions (System Prompt)</label>
            <textarea class="input" id="wiz-system" rows="5" placeholder="Describe how your AI should behave..."
              style="font-family:var(--font-mono); font-size:13px;"></textarea>
          </div>

          <!-- Step 3: Response Style -->
          <div class="wizard-step-content" data-step="3">
            <h3 style="font-weight:600; margin-bottom:var(--sp-2);">Response Style</h3>
            <p class="text-sm text-secondary" style="margin-bottom:var(--sp-4);">Fine-tune how your AI generates responses.</p>
            ${wizSlider('wiz-temp', '🎨 Creativity Level', 'Higher = more creative/random', 0, 2, 0.05, 0.7)}
            ${wizSlider('wiz-top-p', '🎯 Answer Confidence', 'Lower = more focused word choices', 0.1, 1, 0.05, 0.9)}
            ${wizSlider('wiz-repeat', '🔄 Avoid Repetition', 'Higher = less repetition', 0.5, 2, 0.05, 1.1)}
            ${wizSlider('wiz-maxtok', '📏 Max Answer Length', 'Maximum tokens per response', 64, 8192, 64, 2048)}
            ${wizSlider('wiz-ctx', '📚 Memory Length', 'How much context the AI keeps', 1024, 32768, 1024, 8192)}
          </div>

          <!-- Step 4: Preview -->
          <div class="wizard-step-content" data-step="4">
            <h3 style="font-weight:600; margin-bottom:var(--sp-2);">Preview Modelfile</h3>
            <p class="text-sm text-secondary" style="margin-bottom:var(--sp-4);">This is the file that will be created. You can edit it directly.</p>
            <div class="modelfile-preview" id="wiz-preview"></div>
            <div style="margin-top:var(--sp-3);" id="wiz-directive-help">
              <div class="text-xs text-secondary">Each line explained:</div>
              <div id="directive-explanations" style="margin-top:var(--sp-2);"></div>
            </div>
          </div>

          <!-- Step 5: Create -->
          <div class="wizard-step-content" data-step="5">
            <h3 style="font-weight:600; margin-bottom:var(--sp-2);">Create Your AI</h3>
            <p class="text-sm text-secondary" style="margin-bottom:var(--sp-5);">Everything is ready. Click "Create AI" to build your new model.</p>
            <div class="card card-pad" id="wiz-summary" style="margin-bottom:var(--sp-5); background:var(--bg-subtle);"></div>
            <div id="wiz-create-progress" class="hidden">
              <div class="flex items-center gap-3" style="margin-bottom:var(--sp-3);">
                <div class="spinner"></div>
                <span id="wiz-progress-text">Creating model...</span>
              </div>
              <div class="progress-bar"><div class="progress-fill" id="wiz-progress-bar" style="width:10%"></div></div>
            </div>
            <div id="wiz-result" class="hidden"></div>
          </div>
        </div>

        <div class="wizard-footer">
          <button class="btn btn-secondary" id="wiz-back-btn" onclick="Wizard.prev()" disabled>← Back</button>
          <span class="text-sm text-secondary" id="wiz-step-label">Step 1 of 5</span>
          <button class="btn btn-primary" id="wiz-next-btn" onclick="Wizard.next()">Next →</button>
        </div>
      </div>`;

    document.body.appendChild(overlay);
    currentStep = 1;
    updateSliderListeners();

    // Load model info on change
    document.getElementById('wiz-base-model')?.addEventListener('change', (e) => {
      state.baseModel = e.target.value;
    });
  }

  function wizSlider(id, label, help, min, max, step, val) {
    return `
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">${label}
          <span class="help-btn tooltip-wrap">?<span class="tooltip-box">${help}</span></span>
        </div>
      </div>
      <div class="setting-control">
        <div class="slider-wrap">
          <input type="range" class="setting-slider" id="${id}" min="${min}" max="${max}" step="${step}" value="${val}">
        </div>
        <div class="slider-value" id="${id}_val">${val}</div>
      </div>
    </div>`;
  }

  function updateSliderListeners() {
    const sliders = [
      { id: 'wiz-temp',   key: 'temperature' },
      { id: 'wiz-top-p',  key: 'topP' },
      { id: 'wiz-repeat', key: 'repeatPenalty' },
      { id: 'wiz-maxtok', key: 'maxTokens' },
      { id: 'wiz-ctx',    key: 'contextWindow' },
    ];
    sliders.forEach(s => {
      const el = document.getElementById(s.id);
      const val = document.getElementById(s.id + '_val');
      if (el) {
        el.addEventListener('input', () => {
          state[s.key] = parseFloat(el.value);
          if (val) val.textContent = el.value;
        });
      }
    });
  }

  function selectPreset(label) {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('selected'));
    event?.target?.classList.add('selected');
    const prompt = PRESETS[label];
    if (prompt) {
      const ta = document.getElementById('wiz-system');
      if (ta) ta.value = prompt;
      state.systemPrompt = prompt;
    }
  }

  function goStep(n) {
    if (n < 1 || n > TOTAL_STEPS) return;
    collectState();
    currentStep = n;
    renderStep();
  }

  function next() {
    collectState();
    if (currentStep === 4) { generatePreview(); }
    if (currentStep === 5) { createModel(); return; }
    if (currentStep < TOTAL_STEPS) goStep(currentStep + 1);
  }

  function prev() {
    if (currentStep > 1) goStep(currentStep - 1);
  }

  function collectState() {
    state.baseModel    = document.getElementById('wiz-base-model')?.value || state.baseModel;
    state.name         = document.getElementById('wiz-name')?.value || state.name;
    state.systemPrompt = document.getElementById('wiz-system')?.value || state.systemPrompt;
  }

  function renderStep() {
    // Update step dots
    document.querySelectorAll('.wizard-step-dot').forEach(d => {
      const n = parseInt(d.dataset.step);
      d.className = 'wizard-step-dot' + (n === currentStep ? ' active' : n < currentStep ? ' done' : '');
    });

    // Show/hide content panels
    document.querySelectorAll('.wizard-step-content').forEach(p => {
      p.classList.toggle('active', parseInt(p.dataset.step) === currentStep);
    });

    // Update footer
    const backBtn = document.getElementById('wiz-back-btn');
    const nextBtn = document.getElementById('wiz-next-btn');
    const label   = document.getElementById('wiz-step-label');

    if (backBtn) backBtn.disabled = currentStep === 1;
    if (nextBtn) nextBtn.textContent = currentStep === TOTAL_STEPS ? '🚀 Create AI' : 'Next →';
    if (label)   label.textContent = `Step ${currentStep} of ${TOTAL_STEPS}`;

    if (currentStep === 4) generatePreview();
    if (currentStep === 5) renderSummary();
  }

  function generatePreview() {
    const mf = buildModelfile();
    const preview = document.getElementById('wiz-preview');
    if (preview) {
      // Syntax color
      let html = '';
      mf.split('\n').forEach(line => {
        if (line.startsWith('#') || line.trim() === '') {
          html += `<span class="mf-comment">${line}</span>\n`;
        } else if (line.startsWith('FROM')) {
          html += `<span class="mf-directive">FROM</span> <span class="mf-value">${line.slice(5)}</span>\n`;
        } else if (line.startsWith('SYSTEM')) {
          html += `<span class="mf-directive">SYSTEM</span> <span class="mf-value">${line.slice(7)}</span>\n`;
        } else if (line.startsWith('PARAMETER')) {
          const parts = line.split(' ');
          html += `<span class="mf-directive">PARAMETER</span> <span class="mf-param-key">${parts[1]}</span> <span class="mf-value">${parts.slice(2).join(' ')}</span>\n`;
        } else {
          html += line + '\n';
        }
      });
      preview.innerHTML = html;
    }

    // Directive explanations
    const exp = document.getElementById('directive-explanations');
    if (exp) {
      exp.innerHTML = Object.entries(DIRECTIVE_HELP).map(([dir, help]) => `
        <div class="flex gap-2 text-xs" style="padding:4px 0; border-bottom:1px solid var(--divider);">
          <span class="text-mono" style="color:var(--accent); min-width:180px; flex-shrink:0;">${dir}</span>
          <span class="text-secondary">${help}</span>
        </div>`).join('');
    }
  }

  function renderSummary() {
    const s = document.getElementById('wiz-summary');
    if (!s) return;
    s.innerHTML = `
      <div class="text-sm" style="display:flex; flex-direction:column; gap:8px;">
        <div class="flex justify-between"><span class="text-secondary">Name</span><span class="text-mono font-weight:600">${state.name || '(no name)'}</span></div>
        <div class="flex justify-between"><span class="text-secondary">Base Model</span><span class="text-mono">${state.baseModel}</span></div>
        <div class="flex justify-between"><span class="text-secondary">Creativity</span><span>${state.temperature}</span></div>
        <div class="flex justify-between"><span class="text-secondary">Max Length</span><span>${state.maxTokens} tokens</span></div>
      </div>`;
  }

  function buildModelfile() {
    const sys = state.systemPrompt.replace(/"""/g, "'''");
    return `FROM ${state.baseModel || 'llama3.2:3b'}

SYSTEM """
${sys || 'You are a helpful assistant.'}
"""

PARAMETER temperature ${state.temperature}
PARAMETER top_p ${state.topP}
PARAMETER top_k ${state.topK}
PARAMETER repeat_penalty ${state.repeatPenalty}
PARAMETER num_predict ${state.maxTokens}
PARAMETER num_ctx ${state.contextWindow}
`;
  }

  async function createModel() {
    const name = (state.name || '').trim().replace(/\s+/g, '-').toLowerCase();
    if (!name) { Utils.toast('Please enter a name for your AI (Step 2)', 'warning'); goStep(2); return; }
    if (!state.baseModel) { Utils.toast('Please select a base model (Step 1)', 'warning'); goStep(1); return; }

    Utils.show('wiz-create-progress');
    document.getElementById('wiz-next-btn').disabled = true;

    const modelfile = buildModelfile();

    try {
      const res = await API.post('/api/models/create', { name, modelfile });
      document.getElementById('wiz-progress-bar').style.width = '100%';
      Utils.setText('wiz-progress-text', `[+] ${name} created!`);

      const result = document.getElementById('wiz-result');
      result.innerHTML = `<div class="badge badge-success" style="font-size:14px; padding:8px 16px;">
        [+] AI "${name}" created successfully! Go to Models to use it.</div>`;
      Utils.show('wiz-result');

      Utils.toast(`"${name}" is ready to use!`, 'success');
      setTimeout(() => { close(); Models.refresh(); }, 2000);
    } catch (e) {
      Utils.setText('wiz-progress-text', '[x] Creation failed');
      Utils.toast('Create failed: ' + e.message, 'error');
      document.getElementById('wiz-next-btn').disabled = false;
    }
  }

  function close() {
    const el = document.getElementById('wizard-overlay');
    if (el) el.remove();
  }

  return { open, close, next, prev, goStep, selectPreset };
})();

window.Wizard = Wizard;
