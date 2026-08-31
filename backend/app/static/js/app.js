// ==================== 状态管理 ====================
const state = {
  currentCourseId: null,
  currentCourseName: '',
  currentCourseMajor: '',
  currentCourseDesc: '',
  currentCourseSubject: '',  // 当前课程的学科标识(影响AI生成)
  currentLessonId: null,
  currentChapter: '',
  currentChapterId: null,  // 选中的章节树节点 ID
  knowledgePoints: [],
  pendingFiles: [],
  isProcessing: false,
  materialType: null,      // 选中的教材类型（D 项 + H5 项）
  activeTemplateId: null,  // 当前激活模板 ID（H4 + I 项）
  templates: [],           // 教案模板库缓存
  pptTemplates: [],        // PPT模板库缓存
  lastFailureCtx: null,    // 最近失败上下文（H1）
};

// 学科标识 -> 中文名映射(与后端 prompt_loader._SUBJECT_CN_MAP 对齐)
const SUBJECT_CN_MAP = {
  math: '数学', chinese: '语文', english: '英语', physics: '物理',
  chemistry: '化学', biology: '生物', history: '历史', geography: '地理',
  politics: '政治', it: '信息技术',
  // 理学
  applied_math: '应用数学', statistics: '统计学', psychology: '心理学', ecology: '生态学',
  // 工学
  cs: '计算机科学与技术', software_eng: '软件工程', ai: '人工智能', data_science: '数据科学',
  electronic_info: '电子信息工程', communication: '通信工程', automation: '自动化',
  mechanical: '机械工程', civil_eng: '土木工程', architecture: '建筑学',
  materials_sci: '材料科学与工程', electrical_eng: '电气工程', environmental_eng: '环境工程',
  biomedical_eng: '生物医学工程', cybersecurity: '网络安全',
  // 医学
  clinical_med: '临床医学', basic_med: '基础医学', pharmacy: '药学', nursing: '护理学',
  stomatology: '口腔医学', tcm: '中医学', public_health: '公共卫生',
  // 法学
  law: '法学', sociology: '社会学', political_sci: '政治学与行政学',
  // 经济学
  economics: '经济学', finance: '金融学', fiscal: '财政学', intl_trade: '国际经济与贸易', insurance: '保险学',
  // 管理学
  business_admin: '工商管理', accounting: '会计学', financial_mgmt: '财务管理', marketing: '市场营销',
  public_admin: '公共管理', info_mgmt: '信息管理与信息系统', ecommerce: '电子商务', logistics: '物流管理',
  // 文学
  chinese_lit: '中国语言文学', foreign_lit: '外国语言文学', journalism: '新闻传播学', advertising: '广告学', japanese: '日语',
  // 教育学
  education: '教育学', preschool_edu: '学前教育', edtech: '教育技术学', pe: '体育教育',
  // 艺术学
  art_design: '艺术设计', music: '音乐学', fine_arts: '美术学', dance: '舞蹈学', digital_media: '数字媒体艺术',
  // 农学
  agriculture: '农学', forestry: '林学', horticulture: '园艺学', animal_sci: '动物科学',
  // 历史学
  archaeology: '考古学', museology: '文物与博物馆学',
  // 哲学
  philosophy: '哲学', logic: '逻辑学',
  default: '通用', other: '其他',
};

// 学科分类分组（用于下拉框分组展示）
const SUBJECT_GROUPS = [
  {
    label: '中小学', items: [
      { value: 'chinese', label: '语文' }, { value: 'math', label: '数学' },
      { value: 'english', label: '英语' }, { value: 'physics', label: '物理' },
      { value: 'chemistry', label: '化学' }, { value: 'biology', label: '生物' },
      { value: 'history', label: '历史' }, { value: 'geography', label: '地理' },
      { value: 'politics', label: '政治' }, { value: 'it', label: '信息技术' },
    ]
  },
  {
    label: '理学', items: [
      { value: 'applied_math', label: '应用数学' }, { value: 'statistics', label: '统计学' },
      { value: 'psychology', label: '心理学' }, { value: 'ecology', label: '生态学' },
    ]
  },
  {
    label: '工学', items: [
      { value: 'cs', label: '计算机科学与技术' }, { value: 'software_eng', label: '软件工程' },
      { value: 'ai', label: '人工智能' }, { value: 'data_science', label: '数据科学' },
      { value: 'electronic_info', label: '电子信息工程' }, { value: 'communication', label: '通信工程' },
      { value: 'automation', label: '自动化' }, { value: 'mechanical', label: '机械工程' },
      { value: 'civil_eng', label: '土木工程' }, { value: 'architecture', label: '建筑学' },
      { value: 'materials_sci', label: '材料科学与工程' }, { value: 'electrical_eng', label: '电气工程' },
      { value: 'environmental_eng', label: '环境工程' }, { value: 'biomedical_eng', label: '生物医学工程' },
      { value: 'cybersecurity', label: '网络安全' },
    ]
  },
  {
    label: '医学', items: [
      { value: 'clinical_med', label: '临床医学' }, { value: 'basic_med', label: '基础医学' },
      { value: 'pharmacy', label: '药学' }, { value: 'nursing', label: '护理学' },
      { value: 'stomatology', label: '口腔医学' }, { value: 'tcm', label: '中医学' },
      { value: 'public_health', label: '公共卫生' },
    ]
  },
  {
    label: '法学', items: [
      { value: 'law', label: '法学' }, { value: 'sociology', label: '社会学' },
      { value: 'political_sci', label: '政治学与行政学' },
    ]
  },
  {
    label: '经济学', items: [
      { value: 'economics', label: '经济学' }, { value: 'finance', label: '金融学' },
      { value: 'fiscal', label: '财政学' }, { value: 'intl_trade', label: '国际经济与贸易' },
      { value: 'insurance', label: '保险学' },
    ]
  },
  {
    label: '管理学', items: [
      { value: 'business_admin', label: '工商管理' }, { value: 'accounting', label: '会计学' },
      { value: 'financial_mgmt', label: '财务管理' }, { value: 'marketing', label: '市场营销' },
      { value: 'public_admin', label: '公共管理' }, { value: 'info_mgmt', label: '信息管理与信息系统' },
      { value: 'ecommerce', label: '电子商务' }, { value: 'logistics', label: '物流管理' },
    ]
  },
  {
    label: '文学', items: [
      { value: 'chinese_lit', label: '中国语言文学' }, { value: 'foreign_lit', label: '外国语言文学' },
      { value: 'journalism', label: '新闻传播学' }, { value: 'advertising', label: '广告学' },
      { value: 'japanese', label: '日语' },
    ]
  },
  {
    label: '教育学', items: [
      { value: 'education', label: '教育学' }, { value: 'preschool_edu', label: '学前教育' },
      { value: 'edtech', label: '教育技术学' }, { value: 'pe', label: '体育教育' },
    ]
  },
  {
    label: '艺术学', items: [
      { value: 'art_design', label: '艺术设计' }, { value: 'music', label: '音乐学' },
      { value: 'fine_arts', label: '美术学' }, { value: 'dance', label: '舞蹈学' },
      { value: 'digital_media', label: '数字媒体艺术' },
    ]
  },
  {
    label: '农学', items: [
      { value: 'agriculture', label: '农学' }, { value: 'forestry', label: '林学' },
      { value: 'horticulture', label: '园艺学' }, { value: 'animal_sci', label: '动物科学' },
    ]
  },
  {
    label: '历史学', items: [
      { value: 'archaeology', label: '考古学' }, { value: 'museology', label: '文物与博物馆学' },
    ]
  },
  {
    label: '哲学', items: [
      { value: 'philosophy', label: '哲学' }, { value: 'logic', label: '逻辑学' },
    ]
  },
];

// ==================== 工具函数 ====================
async function api(url, options = {}) {
  const opts = { headers: {}, ...options };
  if (!(opts.body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(url, opts);
  const data = await res.json();
  if (!res.ok || data.success === false) {
    throw new Error(data.detail || data.message || `请求失败 (${res.status})`);
  }
  return data;
}

function toast(msg, duration = 2500) {
  const t = document.getElementById('toast');
  document.getElementById('toastBody').textContent = msg;
  t.classList.remove('hidden');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add('hidden'), duration);
}

// ==================== 通用模态框（替代原生 prompt/confirm）====================
// 显示输入框，返回 Promise<string|null>（null 表示取消）
function showPrompt(title, defaultValue = '') {
  return new Promise(resolve => {
    const modal = document.getElementById('promptModal');
    const input = document.getElementById('promptInput');
    document.getElementById('promptTitle').textContent = title;
    input.value = defaultValue;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => { input.focus(); input.select(); }, 50);

    const cleanup = () => {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      input.onkeydown = null;
      document.getElementById('promptOk').onclick = null;
      document.getElementById('promptCancel').onclick = null;
    };
    const ok = () => { const v = input.value; cleanup(); resolve(v); };
    const cancel = () => { cleanup(); resolve(null); };
    input.onkeydown = (e) => {
      if (e.key === 'Enter') { e.preventDefault(); ok(); }
      else if (e.key === 'Escape') { e.preventDefault(); cancel(); }
    };
    document.getElementById('promptOk').onclick = ok;
    document.getElementById('promptCancel').onclick = cancel;
  });
}

// 显示确认框，返回 Promise<boolean>
function showConfirm(title, message) {
  return new Promise(resolve => {
    const modal = document.getElementById('confirmModal');
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    const cleanup = () => {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      document.getElementById('confirmOk').onclick = null;
      document.getElementById('confirmCancel').onclick = null;
    };
    document.getElementById('confirmOk').onclick = () => { cleanup(); resolve(true); };
    document.getElementById('confirmCancel').onclick = () => { cleanup(); resolve(false); };
  });
}

// 学科选择框（下拉选择代替手动输入，含大学学科分类）
function showSubjectPicker(currentValue) {
  return new Promise(resolve => {
    const modal = document.getElementById('subjectPickerModal');
    const select = document.getElementById('subjectPickerSelect');
    select.innerHTML = '';

    // 通用选项
    const optGeneral = document.createElement('option');
    optGeneral.value = ''; optGeneral.textContent = '通用（不指定学科）';
    select.appendChild(optGeneral);

    // 按分组渲染
    SUBJECT_GROUPS.forEach(group => {
      const optg = document.createElement('optgroup');
      optg.label = group.label;
      group.items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.value; opt.textContent = item.label;
        optg.appendChild(opt);
      });
      select.appendChild(optg);
    });

    // 其他
    const optOther = document.createElement('option');
    optOther.value = 'other'; optOther.textContent = '其他';
    select.appendChild(optOther);

    // 预选当前值
    if (currentValue) {
      for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value === currentValue) {
          select.selectedIndex = i; break;
        }
      }
      // 滚动到选中项
      setTimeout(() => {
        const idx = select.selectedIndex;
        if (idx >= 0) select.options[idx].scrollIntoView({ block: 'center' });
      }, 50);
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => select.focus(), 50);

    const cleanup = () => {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      document.getElementById('subjectPickerOk').onclick = null;
      document.getElementById('subjectPickerCancel').onclick = null;
      select.onkeydown = null;
    };
    const ok = () => { const v = select.value; cleanup(); resolve(v); };
    const cancel = () => { cleanup(); resolve(undefined); };
    select.onkeydown = (e) => {
      if (e.key === 'Enter') { e.preventDefault(); ok(); }
      else if (e.key === 'Escape') { e.preventDefault(); cancel(); }
    };
    select.ondblclick = (e) => { e.preventDefault(); ok(); };
    document.getElementById('subjectPickerOk').onclick = ok;
    document.getElementById('subjectPickerCancel').onclick = cancel;
  });
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ==================== API 状态检查 ====================
async function checkApiStatus() {
  const el = document.getElementById('apiStatus');
  try {
    const data = await api('/api/llm-test');
    el.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-teal-500"></span><span class="text-teal-700">${data.message}</span>`;
    updateModelBadge(data.data);
  } catch (e) {
    el.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-red-500"></span><span class="text-red-600">API未配置</span>`;
    console.error('API test failed:', e);
  }
}

function updateModelBadge(info) {
  const badge = document.getElementById('modelBadge');
  if (info && info.model) {
    const providerLabel = (PROVIDER_LABELS[info.provider] || info.provider || '').split('（')[0];
    badge.innerHTML = `模型: <span class="text-teal-600 font-medium" title="${escapeHtml(info.base_url)}">${escapeHtml(info.model)} · ${escapeHtml(providerLabel)}</span>`;
  } else {
    badge.innerHTML = `模型: <span class="text-red-500 font-medium">未配置</span>`;
  }
}

// ==================== LLM 设置 ====================
let PROVIDER_LABELS = {};
let PROVIDERS_DATA = {};

async function loadLlmSettings() {
  try {
    const data = await api('/api/settings/llm');
    const current = data.data.current || {};
    PROVIDERS_DATA = data.data.providers || {};
    PROVIDER_LABELS = {};
    Object.entries(PROVIDERS_DATA).forEach(([k, v]) => PROVIDER_LABELS[k] = v.label);

    // 填充供应商下拉
    const sel = document.getElementById('llmProvider');
    sel.innerHTML = Object.entries(PROVIDERS_DATA).map(([k, v]) =>
      `<option value="${k}">${escapeHtml(v.label)}</option>`
    ).join('');
    sel.value = current.provider || 'qwen';

    // 填充当前值
    document.getElementById('llmApiKey').value = current.api_key || '';
    document.getElementById('llmBaseUrl').value = current.base_url || '';
    document.getElementById('llmModel').value = current.model || '';
    document.getElementById('llmTemperature').value = current.temperature ?? 0.7;
    document.getElementById('llmMaxTokens').value = current.max_tokens ?? 4096;

    // API Key 状态
    const statusEl = document.getElementById('apiKeyStatus');
    if (current.has_api_key) {
      statusEl.innerHTML = '<span class="text-teal-600">已配置</span>';
    } else {
      statusEl.innerHTML = '<span class="text-red-500">未配置</span>';
    }

    updateProviderHint();
    updateModelBadge(current);
  } catch (e) {
    toast('加载设置失败: ' + e.message);
  }
}

function updateProviderHint() {
  const provider = document.getElementById('llmProvider').value;
  const info = PROVIDERS_DATA[provider] || {};
  document.getElementById('apiKeyHint').textContent = info.api_key_hint ? `格式: ${info.api_key_hint}` : '';

  // 模型建议列表
  const datalist = document.getElementById('llmModelList');
  datalist.innerHTML = (info.models || []).map(m => `<option value="${escapeHtml(m)}">`).join('');

  // 文档链接
  const docsLink = document.getElementById('settingsDocsLink');
  if (info.docs_url) {
    docsLink.href = info.docs_url;
    docsLink.classList.remove('hidden');
  } else {
    docsLink.classList.add('hidden');
  }
}

function openSettingsModal() {
  document.getElementById('settingsModal').classList.remove('hidden');
  document.getElementById('settingsModal').classList.add('flex');
  document.getElementById('testResult').classList.add('hidden');
  loadLlmSettings();
}

function closeSettingsModal() {
  document.getElementById('settingsModal').classList.add('hidden');
  document.getElementById('settingsModal').classList.remove('flex');
}

function collectSettingsPayload() {
  return {
    provider: document.getElementById('llmProvider').value,
    api_key: document.getElementById('llmApiKey').value || null,
    base_url: document.getElementById('llmBaseUrl').value || null,
    model: document.getElementById('llmModel').value || null,
    temperature: parseFloat(document.getElementById('llmTemperature').value) || null,
    max_tokens: parseInt(document.getElementById('llmMaxTokens').value) || null,
  };
}

async function saveLlmSettings() {
  const payload = collectSettingsPayload();
  if (!payload.api_key && !document.getElementById('apiKeyStatus').textContent.includes('已配置')) {
    toast('请填写 API Key');
    return;
  }
  if (!payload.base_url) { toast('请填写 Base URL'); return; }
  if (!payload.model) { toast('请填写模型名称'); return; }

  const btn = document.getElementById('saveSettings');
  const oldText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '保存中...';
  try {
    const data = await api('/api/settings/llm', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    toast(data.message || '设置已保存', 2500);
    closeSettingsModal();
    checkApiStatus();
  } catch (e) {
    toast('保存失败: ' + e.message, 3500);
  } finally {
    btn.disabled = false;
    btn.textContent = oldText;
  }
}

async function testLlmConnection() {
  const payload = collectSettingsPayload();
  const resultEl = document.getElementById('testResult');
  const btn = document.getElementById('testLlmBtn');

  if (!payload.base_url) { toast('请填写 Base URL'); return; }
  if (!payload.model) { toast('请填写模型名称'); return; }
  if (!payload.api_key && !document.getElementById('apiKeyStatus').textContent.includes('已配置')) {
    toast('请填写 API Key');
    return;
  }

  btn.disabled = true;
  resultEl.classList.remove('hidden');
  resultEl.className = 'mt-3 px-3 py-2 rounded-md text-xs bg-teal-50 text-teal-700';
  resultEl.textContent = '⏳ 正在测试连接...';

  try {
    const data = await api('/api/settings/llm/test', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    resultEl.className = 'mt-3 px-3 py-2 rounded-md text-xs bg-teal-50 text-teal-700';
    resultEl.innerHTML = `✓ ${data.message}<br><span class="text-muted">回复: ${escapeHtml(data.data.response || '')}</span><br><span class="text-muted">模型: ${escapeHtml(data.data.model)}</span>`;
    toast('连接测试成功');
  } catch (e) {
    resultEl.className = 'mt-3 px-3 py-2 rounded-md text-xs bg-red-50 text-red-700';
    resultEl.textContent = '✗ ' + e.message;
  } finally {
    btn.disabled = false;
  }
}

// 供应商切换：自动填充 Base URL 和默认模型
document.addEventListener('change', (e) => {
  if (e.target.id === 'llmProvider') {
    const provider = e.target.value;
    const info = PROVIDERS_DATA[provider] || {};
    if (info.base_url) document.getElementById('llmBaseUrl').value = info.base_url;
    if (info.default_model) document.getElementById('llmModel').value = info.default_model;
    updateProviderHint();
  }
});

document.getElementById('settingsBtn').onclick = openSettingsModal;
document.getElementById('cancelSettings').onclick = closeSettingsModal;
document.getElementById('saveSettings').onclick = saveLlmSettings;
document.getElementById('testLlmBtn').onclick = testLlmConnection;
document.getElementById('toggleApiKeyVisibility').onclick = () => {
  const input = document.getElementById('llmApiKey');
  input.type = input.type === 'password' ? 'text' : 'password';
};

// ==================== 课程管理 ====================
async function loadCourses() {
  try {
    const data = await api('/api/courses');
    const list = document.getElementById('courseList');
    if (!data.data || data.data.length === 0) {
      list.innerHTML = '<div class="text-xs text-muted text-center py-3">点击 + 创建课程</div>';
      return;
    }
    list.innerHTML = data.data.map(c => `
      <div class="course-item p-2 rounded-md cursor-pointer hover:bg-teal-50 ${c.id === state.currentCourseId ? 'bg-teal-100 border-l-2 border-teal-500' : ''}"
           data-id="${c.id}" data-name="${escapeHtml(c.name)}" data-major="${escapeHtml(c.major || '')}" data-description="${escapeHtml(c.description || '')}" data-subject="${escapeHtml(c.subject || '')}">
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium text-ink truncate flex-1">${escapeHtml(c.name)}</div>
          <button class="course-menu-btn text-muted hover:text-ochre p-0.5" data-course-id="${c.id}" title="更多">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/></svg>
          </button>
        </div>
        ${c.major ? `<div class="text-[10px] text-muted truncate">${escapeHtml(c.major)}</div>` : ''}
        ${c.subject ? `<div class="text-[10px] text-teal-600 truncate">📖 ${escapeHtml(SUBJECT_CN_MAP[c.subject] || c.subject)}</div>` : ''}
      </div>
    `).join('');
    list.querySelectorAll('.course-item').forEach(el => {
      el.onclick = (e) => {
        if (e.target.closest('.course-menu-btn')) return;
        selectCourse(parseInt(el.dataset.id), el.dataset.name, el.dataset.major, el.dataset.description, el.dataset.subject);
      };
    });
    list.querySelectorAll('.course-menu-btn').forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const courseId = parseInt(btn.dataset.courseId);
        const courseName = btn.closest('.course-item').dataset.name;
        showCourseContextMenu(e, courseId, courseName);
      };
    });
  } catch (e) {
    toast('加载课程失败: ' + e.message);
  }
}

async function selectCourse(id, name, major, description, subject) {
  state.currentCourseId = id;
  state.currentCourseName = name;
  state.currentCourseMajor = major || '';
  state.currentCourseDesc = description || '';
  state.currentCourseSubject = subject || '';
  state.currentLessonId = null;
  state.currentChapterId = null;
  state.knowledgePoints = [];

  document.getElementById('currentCourseName').textContent = name;
  document.getElementById('courseInfo').classList.remove('hidden');
  // 更新课程元信息
  const metaEl = document.getElementById('currentCourseMeta');
  const parts = [];
  if (major) parts.push(`专业：${major}`);
  if (subject) parts.push(`学科：${SUBJECT_CN_MAP[subject] || subject}`);
  if (description) parts.push(description);
  metaEl.textContent = parts.join(' | ');
  document.getElementById('uploadBtn').disabled = false;
  document.getElementById('uploadLessonBtn').disabled = false;
  document.getElementById('uploadPptBtn').disabled = false;
  document.getElementById('extractBtn').disabled = false;
  const smartBtn = document.getElementById('smartExtractBtn');
  if (smartBtn) smartBtn.disabled = false;
  document.getElementById('genLessonBtn').disabled = state.knowledgePoints.length === 0;
  document.getElementById('sendBtn').disabled = true;
  document.getElementById('exportMdBtn').disabled = true;
  document.getElementById('exportDocxBtn').disabled = true;
  document.getElementById('genPptBtn').disabled = true;
  document.getElementById('evaluateLessonBtn').disabled = true;
  document.getElementById('chapterInput').value = '';

  document.getElementById('previewContent').innerHTML = `
    <div class="text-center text-xs text-muted py-10">
      <div class="font-serif text-base text-teal-700 mb-2">${escapeHtml(name)} · 教案预览</div>
      <div>完成 ① 提取知识点 → ② 生成教案 后<br>这里会显示完整六阶段教案</div>
    </div>`;
  // 重置PPT预览区
  document.getElementById('pptPreviewContent').innerHTML = '<div class="text-center text-xs text-muted py-10"><div class="font-serif text-base text-teal-700 mb-2">PPT预览区</div><div>点击左侧PPT记录或生成PPT后<br>这里会显示幻灯片预览</div></div>';
  // 重置元信息
  document.getElementById('previewMeta').textContent = '';
  // 重置PPT面板状态
  _pptPanelRecordId = null;
  _pptPanelRecordData = null;
  // 确保在教案预览标签
  const lessonTab = document.getElementById('previewTabLesson');
  const pptTab = document.getElementById('previewTabPpt');
  if (pptTab && pptTab.classList.contains('active')) { switchPreviewTab('lesson'); }
  // 隐藏PPT按钮栏
  document.getElementById('pptSaveBtn')?.classList.add('hidden');
  document.getElementById('pptExportFileBtn')?.classList.add('hidden');

  await loadMaterials(id);
  await loadLessonsList(id, null, null);
  await loadChapters(id);
  await loadPptRecords(id, null, null);
  await loadCourses(); // 刷新高亮
  // F3: 切换课程时加载历史聊天记录（按课程保留）
  await loadChatHistory(id);
}

async function createCourse() {
  const name = document.getElementById('newCourseName').value.trim();
  const major = document.getElementById('newCourseMajor').value.trim();
  const desc = document.getElementById('newCourseDesc').value.trim();
  const subject = document.getElementById('newCourseSubject').value;
  if (!name) { toast('请输入课程名称'); return; }
  try {
    await api('/api/courses', {
      method: 'POST',
      body: JSON.stringify({ name, major: major || null, description: desc || null, subject: subject || '' }),
    });
    toast('课程创建成功');
    document.getElementById('courseModal').classList.add('hidden');
    document.getElementById('courseModal').classList.remove('flex');
    document.getElementById('newCourseName').value = '';
    document.getElementById('newCourseMajor').value = '';
    document.getElementById('newCourseDesc').value = '';
    document.getElementById('newCourseSubject').value = '';
    await loadCourses();
  } catch (e) {
    toast('创建失败: ' + e.message);
  }
}

// ==================== 章节树管理 ====================
const chapterState = {
  expanded: new Set(),  // 展开的节点 id 集合
};

// 加载章节树
async function loadChapters(courseId) {
  try {
    const data = await api(`/api/courses/${courseId}/chapters`);
    const tree = document.getElementById('chapterTree');
    const roots = data.data || [];
    if (roots.length === 0) {
      tree.innerHTML = '<div class="text-xs text-muted text-center py-3">点击 + 新建第一章</div>';
      return;
    }
    // 首次加载默认展开第一级
    if (chapterState.expanded.size === 0) {
      roots.forEach(r => chapterState.expanded.add(r.id));
    }
    tree.innerHTML = roots.map(ch => renderChapterNode(ch, 0)).join('');
    bindChapterEvents();
    // 思维导图联动：课程结构变化时刷新
    refreshMindmapIfOpen();
  } catch (e) {
    toast('加载章节失败: ' + e.message);
  }
}

// 渲染单个章节节点（递归）
function renderChapterNode(ch, depth) {
  const hasChildren = ch.children && ch.children.length > 0;
  const isExpanded = chapterState.expanded.has(ch.id);
  const isActive = state.currentChapterId === ch.id;
  const toggleClass = hasChildren ? (isExpanded ? 'expanded' : '') : 'leaf';
  const iconColor = depth === 0 ? '#2e7d6e' : '#4a9d8f';

  // 图标：顶级用书📕、子级用文档📄
  const iconSvg = depth === 0
    ? `<svg class="chapter-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>`
    : `<svg class="chapter-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`;

  const childrenHtml = hasChildren ? `
    <div class="chapter-children ${isExpanded ? '' : 'collapsed'}">
      ${ch.children.map(c => renderChapterNode(c, depth + 1)).join('')}
    </div>
  ` : '';

  return `
    <div class="chapter-node" data-id="${ch.id}">
      <div class="chapter-row ${isActive ? 'active' : ''}" data-id="${ch.id}" data-name="${escapeHtml(ch.name)}">
        <span class="chapter-toggle ${toggleClass}">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
        </span>
        ${iconSvg}
        <span class="chapter-name">${escapeHtml(ch.name)}</span>
        <button class="chapter-menu-btn" data-id="${ch.id}" data-name="${escapeHtml(ch.name)}" data-depth="${depth}" title="更多">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/></svg>
        </button>
      </div>
      ${childrenHtml}
    </div>
  `;
}

// 绑定章节树事件
function bindChapterEvents() {
  // 点击章节行 = 选中章节 + 切换展开
  document.querySelectorAll('#chapterTree .chapter-row').forEach(row => {
    row.onclick = (e) => {
      if (e.target.closest('.chapter-menu-btn')) return;
      const id = parseInt(row.dataset.id);
      const name = row.dataset.name;
      selectChapter(id, name);
      // 切换展开（如果有子节点）
      const toggle = row.querySelector('.chapter-toggle');
      if (!toggle.classList.contains('leaf')) {
        if (chapterState.expanded.has(id)) chapterState.expanded.delete(id);
        else chapterState.expanded.add(id);
        loadChapters(state.currentCourseId);
      }
    };
  });

  // 三点菜单
  document.querySelectorAll('#chapterTree .chapter-menu-btn').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const id = parseInt(btn.dataset.id);
      const name = btn.dataset.name;
      const depth = parseInt(btn.dataset.depth);
      showChapterContextMenu(e, id, name, depth);
    };
  });
}

// 选中章节 - 填充章节输入框 + 加载该章节的教案 + 加载知识点
function selectChapter(id, name) {
  state.currentChapterId = id;
  state.currentChapter = name;
  document.getElementById('chapterInput').value = name;
  document.querySelectorAll('#chapterTree .chapter-row').forEach(r => r.classList.remove('active'));
  const row = document.querySelector(`#chapterTree .chapter-row[data-id="${id}"]`);
  if (row) row.classList.add('active');
  loadLessonsList(state.currentCourseId, id, name);
  loadPptRecords(state.currentCourseId, id, name);
  // 加载该章节的知识点
  loadChapterKnowledgePoints(id);
}

// 加载章节知识点
async function loadChapterKnowledgePoints(chapterId) {
  if (!chapterId || !state.currentCourseId) return;
  try {
    const data = await api(`/api/courses/${state.currentCourseId}/knowledge-points?chapter_id=${chapterId}`);
    const kps = data.data || [];
    if (kps.length > 0) {
      state.knowledgePoints = kps;
      document.getElementById('kpCount').textContent = `(${kps.length}个)`;
      document.getElementById('knowledgePanel').classList.remove('hidden');
      renderKnowledgePoints();
      document.getElementById('genLessonBtn').disabled = false;
    }
  } catch (e) {
    // 静默失败，不影响选择章节
  }
}

// 加载教案列表
async function loadLessonsList(courseId, chapterId, chapterName) {
  try {
    const data = await api(`/api/courses/${courseId}/lessons`);
    let lessons = data.data || [];
    if (chapterId !== null && chapterName) {
      lessons = lessons.filter(l => l.chapter === chapterName);
    }
    renderLessonList(lessons);
  } catch (e) {
    console.error('加载教案失败:', e);
    document.getElementById('lessonFileList').innerHTML = '<div class="text-xs text-muted text-center py-2">加载失败</div>';
  }
}

// 渲染教案列表
function renderLessonList(lessons) {
  const list = document.getElementById('lessonFileList');
  if (!list) return;
  if (lessons.length === 0) {
    list.innerHTML = '<div class="text-xs text-muted text-center py-2">暂无教案</div>';
    return;
  }
  list.innerHTML = lessons.map(l => `
    <div class="lesson-item ${state.currentLessonId === l.id ? 'active' : ''}" data-id="${l.id}" data-title="${escapeHtml(l.title || l.chapter)}">
      <svg class="lesson-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      <span class="lesson-name">${escapeHtml(l.title || l.chapter)}</span>
      <span class="lesson-date">${l.created_at ? formatDate(l.created_at) : ''}</span>
      <button class="del-lesson text-red-400 hover:text-red-600 text-xs ml-auto flex-shrink-0" data-id="${l.id}" title="删除教案">×</button>
    </div>
  `).join('');
  list.querySelectorAll('.lesson-item').forEach(item => {
    item.onclick = (e) => {
      if (e.target.closest('.del-lesson')) return;
      selectLesson(parseInt(item.dataset.id), item.dataset.title);
    };
  });
  list.querySelectorAll('.del-lesson').forEach(b => {
    b.onclick = async (e) => {
      e.stopPropagation();
      if (!(await showConfirm('删除教案', '确认删除此教案？'))) return;
      try {
        await api(`/api/lessons/${b.dataset.id}`, { method: 'DELETE' });
        toast('教案已删除');
        if (state.currentLessonId === parseInt(b.dataset.id)) {
          state.currentLessonId = null;
          document.getElementById('lessonPreview').classList.add('hidden');
        }
        const courseId = state.currentCourseId;
        if (courseId) {
          const data = await api(`/api/courses/${courseId}/lessons`);
          renderLessonList(data.data || []);
        }
      } catch (e) { toast('删除失败: ' + e.message); }
    };
  });
}

// 选中教案 - 预览
async function selectLesson(lessonId, title) {
  state.currentLessonId = lessonId;
  document.querySelectorAll('.lesson-item').forEach(i => i.classList.remove('active'));
  const item = document.querySelector(`.lesson-item[data-id="${lessonId}"]`);
  if (item) item.classList.add('active');
  try {
    const data = await api(`/api/lessons/${lessonId}`);
    if (data.data && data.data.plan) {
      renderLessonPreview(data.data.plan);
      document.getElementById('previewMeta').textContent = data.data.plan.total_minutes ? `${data.data.plan.total_minutes} 分钟` : '';
      document.getElementById('sendBtn').disabled = false;
    document.getElementById('exportMdBtn').disabled = false;
    document.getElementById('exportDocxBtn').disabled = false;
    document.getElementById('genPptBtn').disabled = false;
    document.getElementById('evaluateLessonBtn').disabled = false;
  }
  } catch (e) {
    toast('加载教案失败: ' + e.message);
  }
}

// 格式化日期
function formatDate(dateStr) {
  try {
    const d = new Date(dateStr);
    return `${d.getMonth()+1}/${d.getDate()}`;
  } catch {
    return '';
  }
}

// 章节三点菜单
function showChapterContextMenu(e, chapterId, chapterName, depth) {
  closeAnyMenu();
  const menu = document.createElement('div');
  menu.className = 'chapter-context-menu';
  menu.id = '_chapterMenu';

  const items = [];
  items.push({ icon: 'edit', label: '重命名', action: () => renameChapter(chapterId, chapterName) });
  items.push({ icon: 'plus', label: depth === 0 ? '新建节' : '新建子节', action: () => createChapter(chapterId, depth) });
  items.push({ icon: 'kp', label: '管理知识点', action: () => manageChapterKnowledgePoints(chapterId, chapterName) });
  items.push({ divider: true });
  items.push({ icon: 'trash', label: '删除', danger: true, action: () => deleteChapter(chapterId, chapterName) });

  menu.innerHTML = items.map(it => {
    if (it.divider) return '<div class="menu-divider"></div>';
    const iconMap = {
      edit: '<svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>',
      plus: '<svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>',
      kp: '<svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
      trash: '<svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>',
    };
    return `<div class="menu-item ${it.danger ? 'danger' : ''}" data-action="${it.label}">${iconMap[it.icon]}<span>${it.label}</span></div>`;
  }).join('');

  document.body.appendChild(menu);
  // 定位（点击处下方）
  const rect = e.currentTarget.getBoundingClientRect();
  let left = rect.left;
  let top = rect.bottom + 4;
  // 边界检查
  const menuRect = menu.getBoundingClientRect();
  if (left + menuRect.width > window.innerWidth - 8) left = window.innerWidth - menuRect.width - 8;
  if (top + menuRect.height > window.innerHeight - 8) top = rect.top - menuRect.height - 4;
  menu.style.left = left + 'px';
  menu.style.top = top + 'px';

  // 绑定菜单项点击（按 data-action 精确匹配，避免闭包 index 错位）
  const menuItems = items.filter(i => !i.divider);
  menu.querySelectorAll('.menu-item').forEach((el, i) => {
    el.onclick = () => {
      const item = menuItems[i];
      if (item && typeof item.action === 'function') item.action();
      closeAnyMenu();
    };
  });
}

// 课程三点菜单
function showCourseContextMenu(e, courseId, courseName) {
  closeAnyMenu();
  const menu = document.createElement('div');
  menu.className = 'chapter-context-menu';
  menu.id = '_chapterMenu';
  menu.innerHTML = `
    <div class="menu-item" data-action="rename">
      <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
      <span>重命名</span>
    </div>
    <div class="menu-item" data-action="edit-info">
      <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span>编辑课程信息</span>
    </div>
    <div class="menu-item" data-action="set-subject">
      <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.247 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.753 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.753 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.747 0-3.332.477-4.5 1.253"/></svg>
      <span>设置学科领域</span>
    </div>
    <div class="menu-item" data-action="knowledge-graph">
      <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
      <span>知识图谱</span>
    </div>
    <div class="menu-divider"></div>
    <div class="menu-item danger" data-action="delete">
      <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
      <span>删除课程</span>
    </div>
  `;
  document.body.appendChild(menu);
  const rect = e.currentTarget.getBoundingClientRect();
  let left = rect.left;
  let top = rect.bottom + 4;
  const menuRect = menu.getBoundingClientRect();
  if (left + menuRect.width > window.innerWidth - 8) left = window.innerWidth - menuRect.width - 8;
  if (top + menuRect.height > window.innerHeight - 8) top = rect.top - menuRect.height - 4;
  menu.style.left = left + 'px';
  menu.style.top = top + 'px';

  menu.querySelector('[data-action="rename"]').onclick = async () => {
    const newName = await showPrompt('课程新名称', courseName);
    if (newName && newName.trim() && newName !== courseName) {
      try {
        await api(`/api/courses/${courseId}`, {
          method: 'PUT',
          body: JSON.stringify({ name: newName.trim() }),
        });
        toast('已重命名');
        await loadCourses();
        if (state.currentCourseId === courseId) {
          state.currentCourseName = newName.trim();
          document.getElementById('currentCourseName').textContent = newName.trim();
        }
      } catch (e) { toast('重命名失败: ' + e.message); }
    }
    closeAnyMenu();
  };
  menu.querySelector('[data-action="edit-info"]').onclick = async () => {
    const currentMajor = state.currentCourseMajor || '';
    const currentDesc = state.currentCourseDesc || '';
    const newMajor = await showPrompt('编辑专业（留空则不填）', currentMajor);
    if (newMajor === null) { closeAnyMenu(); return; }
    const newDesc = await showPrompt('编辑课程描述（留空则不填）', currentDesc);
    if (newDesc === null) { closeAnyMenu(); return; }
    try {
      const payload = {};
      if (newMajor.trim() !== currentMajor) payload.major = newMajor.trim() || null;
      if (newDesc.trim() !== currentDesc) payload.description = newDesc.trim() || null;
      if (Object.keys(payload).length === 0) { closeAnyMenu(); return; }
      await api(`/api/courses/${courseId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      toast('课程信息已更新');
      state.currentCourseMajor = newMajor.trim();
      state.currentCourseDesc = newDesc.trim();
      const metaEl = document.getElementById('currentCourseMeta');
      const parts = [];
      if (newMajor.trim()) parts.push(`专业：${newMajor.trim()}`);
      if (state.currentCourseSubject) parts.push(`学科：${SUBJECT_CN_MAP[state.currentCourseSubject] || state.currentCourseSubject}`);
      if (newDesc.trim()) parts.push(newDesc.trim());
      metaEl.textContent = parts.join(' | ');
      await loadCourses();
    } catch (e) { toast('更新失败: ' + e.message); }
    closeAnyMenu();
  };
  menu.querySelector('[data-action="set-subject"]').onclick = async () => {
    // 设置课程学科领域(影响AI生成教案/PPT/知识点的学科规范)
    const currentSubject = state.currentCourseSubject || '';
    const newSubject = await showSubjectPicker(currentSubject);
    if (newSubject === undefined) { closeAnyMenu(); return; }
    if (newSubject === currentSubject) { closeAnyMenu(); return; }
    try {
      await api(`/api/courses/${courseId}`, {
        method: 'PUT',
        body: JSON.stringify({ subject: newSubject }),
      });
      toast('学科领域已更新');
      state.currentCourseSubject = newSubject;
      await loadCourses();
    } catch (e) { toast('更新失败: ' + e.message); }
    closeAnyMenu();
  };
  menu.querySelector('[data-action="knowledge-graph"]').onclick = () => {
    closeAnyMenu();
    openKnowledgeGraph();
  };
  menu.querySelector('[data-action="delete"]').onclick = async () => {
    if (!(await showConfirm('删除课程', `确认删除课程「${courseName}」？\n该课程下所有章节、教材、教案将一并删除。`))) {
      closeAnyMenu();
      return;
    }
    try {
      await api(`/api/courses/${courseId}`, { method: 'DELETE' });
      toast('课程已删除');
      if (state.currentCourseId === courseId) {
        state.currentCourseId = null;
        state.currentCourseName = '';
        state.currentChapterId = null;
        document.getElementById('courseInfo').classList.add('hidden');
        document.getElementById('uploadBtn').disabled = true;
        document.getElementById('uploadLessonBtn').disabled = true;
        document.getElementById('uploadPptBtn').disabled = true;
      }
      await loadCourses();
    } catch (e) { toast('删除失败: ' + e.message); }
    closeAnyMenu();
  };
}

// 关闭任意浮层菜单
function closeAnyMenu() {
  const m = document.getElementById('_chapterMenu');
  if (m) m.remove();
}
document.addEventListener('click', (e) => {
  if (!e.target.closest('.chapter-context-menu') && !e.target.closest('.chapter-menu-btn') && !e.target.closest('.course-menu-btn')) {
    closeAnyMenu();
  }
});

// 创建章节（parent_id 为 null 表示顶级，否则为子节）
async function createChapter(parentId, parentDepth) {
  const label = parentId === null ? '新章名称' : (parentDepth === 0 ? '新节名称' : '新子节名称');
  const defaultName = parentId === null ? '第一章 ' : (parentDepth === 0 ? '第一节 ' : '第1节 ');
  const name = await showPrompt(`请输入${label}`, defaultName);
  if (!name || !name.trim()) return;
  try {
    const body = { name: name.trim() };
    if (parentId !== null) body.parent_id = parentId;
    await api(`/api/courses/${state.currentCourseId}/chapters`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
    toast('章节已创建');
    if (parentId !== null) chapterState.expanded.add(parentId);
    await loadChapters(state.currentCourseId);
  } catch (e) { toast('创建失败: ' + e.message); }
}

// 重命名章节
async function renameChapter(chapterId, oldName) {
  const newName = await showPrompt('章节新名称', oldName);
  if (!newName || !newName.trim() || newName === oldName) return;
  try {
    await api(`/api/chapters/${chapterId}`, {
      method: 'PUT',
      body: JSON.stringify({ name: newName.trim() }),
    });
    toast('已重命名');
    await loadChapters(state.currentCourseId);
    if (state.currentChapterId === chapterId) {
      state.currentChapter = newName.trim();
      document.getElementById('chapterInput').value = newName.trim();
    }
  } catch (e) { toast('重命名失败: ' + e.message); }
}

// 管理章节知识点
async function manageChapterKnowledgePoints(chapterId, chapterName) {
  if (!state.currentCourseId) return;
  // 选中该章节
  selectChapter(chapterId, chapterName);
  try {
    const data = await api(`/api/courses/${state.currentCourseId}/knowledge-points?chapter_id=${chapterId}`);
    state.knowledgePoints = data.data || [];
    document.getElementById('kpCount').textContent = `(${state.knowledgePoints.length}个)`;
    document.getElementById('knowledgePanel').classList.remove('hidden');
    renderKnowledgePoints();
    document.getElementById('genLessonBtn').disabled = state.knowledgePoints.length === 0;
    toast(`章节「${chapterName}」有 ${state.knowledgePoints.length} 个知识点`);
  } catch (e) {
    toast('加载知识点失败: ' + e.message);
  }
}

// 删除章节
async function deleteChapter(chapterId, chapterName) {
  if (!(await showConfirm('删除章节', `确认删除「${chapterName}」？\n其下所有子节将一并删除。关联的教案会被保留但解除关联。`))) return;
  try {
    await api(`/api/chapters/${chapterId}`, { method: 'DELETE' });
    toast('章节已删除');
    if (state.currentChapterId === chapterId) {
      state.currentChapterId = null;
      state.currentChapter = '';
      document.getElementById('chapterInput').value = '';
      loadPptRecords(state.currentCourseId, null, null);
    }
    await loadChapters(state.currentCourseId);
  } catch (e) { toast('删除失败: ' + e.message); }
}

// ==================== 教材管理 ====================
async function loadMaterials(courseId) {
  try {
    const data = await api(`/api/courses/${courseId}/materials`);
    const list = document.getElementById('materialList');
    if (!data.data || data.data.length === 0) {
      list.innerHTML = '<div class="text-xs text-muted text-center py-3">点击 ↑ 上传教材</div>';
      return;
    }
    list.innerHTML = data.data.map(m => `
      <div class="material-item p-2 rounded-md bg-white/60 border border-rule ${m.is_primary ? 'ring-1 ring-teal-400 bg-teal-50/40' : ''}">
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium text-ink truncate">
              ${m.is_primary ? '<span class="text-teal-600 mr-0.5" title="主教材">★</span>' : ''}${escapeHtml(m.filename)}
            </div>
            <div class="text-[10px] text-muted mt-0.5 flex items-center gap-1.5 flex-wrap">
              ${renderMaterialBadge(m)}
              ${m.version_label ? `<span class="px-1.5 py-0.5 rounded border border-indigo-200 bg-indigo-50 text-indigo-700 text-[10px] whitespace-nowrap">${escapeHtml(m.version_label)}</span>` : ''}
              ${m.is_primary ? '<span class="px-1.5 py-0.5 rounded border border-teal-200 bg-teal-50 text-teal-700 text-[10px] font-medium whitespace-nowrap">主教材</span>' : ''}
              <span>·</span>
              <span>${formatSize(m.file_size)}</span>
              <span>·</span>
              <span>${m.char_count ?? 0}字</span>
            </div>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0">
            ${m.is_primary ? '' : `<button class="set-primary-mat text-amber-500 hover:text-amber-700 text-xs" data-id="${m.id}" title="设为主教材">★</button>`}
            <button class="reupload-mat text-teal-500 hover:text-teal-700 text-xs" data-id="${m.id}" title="替换文件">↻</button>
            <button class="del-mat text-red-400 hover:text-red-600 text-xs" data-id="${m.id}">×</button>
          </div>
        </div>
        <input type="file" class="hidden reupload-input" data-id="${m.id}" accept=".pdf,.docx,.txt,.md">
      </div>
    `).join('');
    list.querySelectorAll('.del-mat').forEach(b => {
      b.onclick = async () => {
        if (!(await showConfirm('删除材料', '确认删除此材料？'))) return;
        try {
          await api(`/api/materials/${b.dataset.id}`, { method: 'DELETE' });
          await loadMaterials(state.currentCourseId);
        } catch (e) { toast('删除失败: ' + e.message); }
      };
    });
    list.querySelectorAll('.set-primary-mat').forEach(b => {
      b.onclick = async () => {
        try {
          const r = await api(`/api/materials/${b.dataset.id}/set-primary`, { method: 'PUT' });
          toast(r.message || '已设为主教材');
          await loadMaterials(state.currentCourseId);
        } catch (e) { toast('设置失败: ' + e.message); }
      };
    });
    list.querySelectorAll('.reupload-mat').forEach(b => {
      b.onclick = () => {
        const input = b.closest('.material-item').querySelector('.reupload-input');
        if (input) input.click();
      };
    });
    list.querySelectorAll('.reupload-input').forEach(input => {
      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('file', file);
        try {
          await api(`/api/materials/${input.dataset.id}/reupload`, { method: 'PUT', body: fd });
          toast('文件已替换');
          await loadMaterials(state.currentCourseId);
        } catch (e) { toast('替换失败: ' + e.message); }
        input.value = '';
      };
    });
  } catch (e) {
    toast('加载教材失败: ' + e.message);
  }
}

async function uploadFiles() {
  if (state.pendingFiles.length === 0) return;
  // H5: 读取教材类型单选
  const radio = document.querySelector('input[name="mat_type"]:checked');
  state.materialType = radio && radio.value && radio.value !== 'other' ? radio.value : null;
  // 多教材版本管理：读取版本标签 + 主教材勾选（仅作用于首个文件，其余文件忽略主教材标记避免重复设置）
  const versionLabel = (document.getElementById('versionLabelInput').value || '').trim();
  const isPrimaryChecked = document.getElementById('isPrimaryCheckbox').checked;
  const btn = document.getElementById('confirmUpload');
  btn.disabled = true;
  btn.textContent = '上传中...';
  try {
    for (let i = 0; i < state.pendingFiles.length; i++) {
      const f = state.pendingFiles[i];
      const fd = new FormData();
      fd.append('file', f);
      if (state.materialType) fd.append('material_type', state.materialType);
      if (versionLabel) fd.append('version_label', versionLabel);
      // 主教材标记仅附加到本次上传的第一个文件（同课程仅一本主教材）
      if (isPrimaryChecked && i === 0) fd.append('is_primary', 'true');
      await api(`/api/courses/${state.currentCourseId}/materials`, { method: 'POST', body: fd });
    }
    toast(`已上传 ${state.pendingFiles.length} 个文件` + (isPrimaryChecked ? '（已设主教材）' : ''));
    state.pendingFiles = [];
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('confirmUpload').disabled = true;
    document.getElementById('uploadModal').classList.add('hidden');
    document.getElementById('uploadModal').classList.remove('flex');
    // 重置默认项（恢复自动识别默认 + 清空版本标签/主教材勾选）
    const radios = document.querySelectorAll('input[name="mat_type"]');
    radios.forEach(r => { r.checked = (r.value === 'other'); });
    document.getElementById('versionLabelInput').value = '';
    document.getElementById('isPrimaryCheckbox').checked = false;
    state.materialType = null;
    await loadMaterials(state.currentCourseId);
  } catch (e) {
    toast('上传失败: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '开始上传';
  }
}

// ==================== 知识点提取 ====================
async function extractKnowledge() {
  const chapter = document.getElementById('chapterInput').value.trim();
  if (!chapter) { toast('请先填写章节名称'); return; }
  if (!state.currentCourseId) { toast('请先选择课程'); return; }

  state.currentChapter = chapter;
  const btn = document.getElementById('extractBtn');
  btn.disabled = true;
  btn.textContent = '提取中...';
  appendAiMessage(`正在为章节「${chapter}」提取知识点...`);

  try {
    const fd = new FormData();
    fd.append('chapter', chapter);
    const data = await api(`/api/courses/${state.currentCourseId}/extract-knowledge`, { method: 'POST', body: fd });
    state.knowledgePoints = data.data.points || [];

    document.getElementById('kpCount').textContent = `(${state.knowledgePoints.length}个)`;
    document.getElementById('knowledgePanel').classList.remove('hidden');
    renderKnowledgePoints();
    document.getElementById('genLessonBtn').disabled = state.knowledgePoints.length === 0;

    appendAiMessage(`已提取 <b class="text-teal-600">${state.knowledgePoints.length}</b> 个知识点，章节概要：${escapeHtml(data.data.summary || '')}<br><span class="text-xs text-muted">点击 ② 生成教案 继续下一步</span>`);
  } catch (e) {
    appendAiMessage(`<span class="text-red-600">提取失败：</span>${escapeHtml(e.message)}`);
    // K: 使用 showOperationFailure
    const retryFn = () => extractKnowledge();
    const lowerParamsFn = () => {
      try {
        const cur = parseFloat(document.getElementById('llmTemperature').value);
        const max = parseInt(document.getElementById('llmMaxTokens').value);
        if (!isNaN(cur)) document.getElementById('llmTemperature').value = (cur / 2).toFixed(2);
        if (!isNaN(max)) document.getElementById('llmMaxTokens').value = Math.round(max * 1.5);
      } catch(_) {}
      extractKnowledge();
    };
    showOperationFailure('章节知识点提取失败', e, {
      retryFn,
      lowerParamsFn,
      draftData: { course_id: state.currentCourseId, chapter, points: state.knowledgePoints },
      onHelp: openTutorial,
    });
  } finally {
    btn.disabled = false;
    btn.textContent = '① 提取知识点';
  }
}

// ==================== 智能章节提取（一键知识点提取） ====================
async function smartExtractKnowledge() {
  if (!state.currentCourseId) { toast('请先选择课程'); return; }

  const courseName = state.currentCourseName;
  if (!(await showConfirm('一键知识点提取', `将从教材中自动识别章节结构并提取知识点，\n创建完整的章节目录。\n\n课程：${courseName}\n\n确定开始？`))) return;

  const btn = document.getElementById('courseMenuSmartExtract');
  const origText = btn.innerHTML;
  btn.innerHTML = '提取中...';
  btn.style.pointerEvents = 'none';

  appendAiMessage(`正在对课程「${courseName}」进行智能章节提取，请稍候...`);

  try {
    const data = await api(`/api/courses/${state.currentCourseId}/smart-extract`, { method: 'POST' });
    const msg = data.message || '提取完成';
    appendAiMessage(`<span class="text-teal-600 font-medium">✅ ${msg}</span>`);

    // 刷新章节树
    await loadChapters(state.currentCourseId);
    // 清空旧知识点，加载新知识点
    state.knowledgePoints = [];
    document.getElementById('kpCount').textContent = '';
    document.getElementById('knowledgePanel').classList.add('hidden');
    renderKnowledgePoints();
    toast(msg);
  } catch (e) {
    appendAiMessage(`<span class="text-red-600">提取失败：</span>${escapeHtml(e.message)}`);
    toast('提取失败: ' + e.message);
  } finally {
    btn.innerHTML = origText;
    btn.style.pointerEvents = '';
  }
}

function renderKnowledgePoints() {
  const container = document.getElementById('kpContainer');
  container.innerHTML = state.knowledgePoints.map((p, i) => {
    const layerTag = p.layer === 'basic' ? '基础' : (p.layer === 'core' ? '核心' : '拓展');
    const layerClass = p.layer === 'basic' ? 'tag-basic' : (p.layer === 'core' ? 'tag-core' : 'tag-ext');
    const kpId = p.id || '';
    return `
      <div class="bg-white/70 rounded-md p-2 border border-rule text-xs fade-in" data-kp-id="${kpId}">
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="font-medium text-ink">${i+1}. ${escapeHtml(p.name)}</span>
              <button class="tag ${layerClass} kp-layer-btn" data-id="${kpId}" data-layer="${p.layer}" title="点击切换层级">${layerTag}</button>
              <button class="tag tag-key ${p.is_key_point ? '' : 'opacity-30'} kp-toggle-btn" data-id="${kpId}" data-field="is_key_point" title="点击切换">重点</button>
              <button class="tag tag-diff ${p.is_difficult ? '' : 'opacity-30'} kp-toggle-btn" data-id="${kpId}" data-field="is_difficult" title="点击切换">难点</button>
              <button class="tag tag-exam ${p.is_exam_point ? '' : 'opacity-30'} kp-toggle-btn" data-id="${kpId}" data-field="is_exam_point" title="点击切换">考点</button>
            </div>
            ${p.definition ? `<div class="text-muted mt-1 leading-snug">${escapeHtml(p.definition)}</div>` : ''}
            ${p.source_pages ? `<div class="text-[10px] text-teal-500 mt-0.5 flex items-center gap-1"><svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg> 教材出处：${escapeHtml(p.source_pages)}</div>` : ''}
          </div>
          <div class="flex items-center gap-1 flex-shrink-0">
            <button class="kp-edit-btn text-teal-600 hover:bg-teal-100 rounded p-1" data-id="${kpId}" data-idx="${i}" title="编辑">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            </button>
            <button class="kp-del-btn text-red-400 hover:bg-red-50 rounded p-1" data-id="${kpId}" data-idx="${i}" title="删除">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // 绑定标签切换（层级/重点/难点/考点）
  container.querySelectorAll('.kp-layer-btn').forEach(btn => {
    btn.onclick = async () => {
      const id = btn.dataset.id;
      if (!id) return;
      const cur = btn.dataset.layer;
      const next = cur === 'basic' ? 'core' : (cur === 'core' ? 'extension' : 'basic');
      try {
        await api(`/api/knowledge-points/${id}`, { method: 'PUT', body: JSON.stringify({ layer: next }) });
        const p = state.knowledgePoints.find(p => p.id == id);
        if (p) { p.layer = next; renderKnowledgePoints(); }
      } catch (e) { toast('切换失败: ' + e.message); }
    };
  });
  container.querySelectorAll('.kp-toggle-btn').forEach(btn => {
    btn.onclick = async () => {
      const id = btn.dataset.id;
      const field = btn.dataset.field;
      if (!id || !field) return;
      const p = state.knowledgePoints.find(p => p.id == id);
      if (!p) return;
      const newVal = !p[field];
      try {
        await api(`/api/knowledge-points/${id}`, { method: 'PUT', body: JSON.stringify({ [field]: newVal }) });
        p[field] = newVal;
        renderKnowledgePoints();
      } catch (e) { toast('切换失败: ' + e.message); }
    };
  });
  // 绑定编辑
  container.querySelectorAll('.kp-edit-btn').forEach(btn => {
    btn.onclick = async () => {
      const id = btn.dataset.id;
      const idx = parseInt(btn.dataset.idx);
      const p = state.knowledgePoints[idx];
      if (!p) return;
      const name = await showPrompt('知识点名称', p.name);
      if (name === null) return;
      const definition = await showPrompt('知识点定义（可空）', p.definition || '');
      if (definition === null) return;
      const sourcePages = await showPrompt('教材页码（如 P23-P25）', p.source_pages || '');
      if (sourcePages === null) return;
      try {
        const updates = { name: name.trim() };
        if (definition.trim() !== (p.definition || '')) updates.definition = definition.trim();
        if (sourcePages.trim() !== (p.source_pages || '')) updates.source_pages = sourcePages.trim();
        if (id) {
          await api(`/api/knowledge-points/${id}`, { method: 'PUT', body: JSON.stringify(updates) });
        }
        Object.assign(p, updates);
        renderKnowledgePoints();
        toast('已更新');
      } catch (e) { toast('更新失败: ' + e.message); }
    };
  });
  // 绑定删除
  container.querySelectorAll('.kp-del-btn').forEach(btn => {
    btn.onclick = async () => {
      const id = btn.dataset.id;
      const idx = parseInt(btn.dataset.idx);
      const p = state.knowledgePoints[idx];
      if (!p) return;
      if (!(await showConfirm('删除知识点', `确认删除「${p.name}」？`))) return;
      try {
        if (id) await api(`/api/knowledge-points/${id}`, { method: 'DELETE' });
        state.knowledgePoints.splice(idx, 1);
        document.getElementById('kpCount').textContent = `(${state.knowledgePoints.length}个)`;
        document.getElementById('genLessonBtn').disabled = state.knowledgePoints.length === 0;
        renderKnowledgePoints();
        toast('已删除');
      } catch (e) { toast('删除失败: ' + e.message); }
    };
  });
}

// 新增知识点
async function addKnowledgePoint() {
  if (!state.currentCourseId) { toast('请先选择课程'); return; }
  const name = await showPrompt('知识点名称', '');
  if (!name || !name.trim()) return;
  const definition = await showPrompt('知识点定义（可空）', '');
  if (definition === null) return;
  const sourcePages = await showPrompt('教材页码（如 P23-P25，可空）', '');
  if (sourcePages === null) return;
  try {
    const payload = {
      name: name.trim(),
      definition: definition.trim(),
      source_pages: sourcePages.trim(),
      chapter: state.currentChapter || '',
      chapter_id: state.currentChapterId || null,
      layer: 'basic',
    };
    const data = await api(`/api/courses/${state.currentCourseId}/knowledge-points`, {
      method: 'POST', body: JSON.stringify(payload),
    });
    state.knowledgePoints.push(data.data);
    document.getElementById('kpCount').textContent = `(${state.knowledgePoints.length}个)`;
    document.getElementById('genLessonBtn').disabled = state.knowledgePoints.length === 0;
    renderKnowledgePoints();
    toast('已新增知识点');
  } catch (e) { toast('新增失败: ' + e.message); }
}

// ==================== 教案生成 ====================
// 收集教案参数面板配置
function collectLessonParams() {
  const get = (id) => {
    const el = document.getElementById(id);
    return el ? el.value : null;
  };
  const totalMinutes = parseInt(get('paramTotalMinutes')) || 90;
  const introStyle = get('paramIntroStyle') || 'auto';
  const languageStyle = get('paramLanguageStyle') || 'plain';
  const caseDensity = get('paramCaseDensity') || 'medium';
  const interactFreq = get('paramInteractFreq') || 'medium';
  const difficulty = get('paramDifficulty') || 'match';
  const homeworkLayers = parseInt(get('paramHomeworkLayers'));
  const includeBoard = (get('paramBoardDesign') === 'true');

  // 根据时长自动调整导入/互动比例
  let introRatio = 0.10;
  let interactRatio = 0.15;
  if (totalMinutes <= 30) { introRatio = 0.15; interactRatio = 0.20; }
  else if (totalMinutes >= 120) { introRatio = 0.08; interactRatio = 0.12; }

  // 互动频率影响占比
  if (interactFreq === 'high') interactRatio = Math.min(0.30, interactRatio + 0.05);
  else if (interactFreq === 'low') interactRatio = Math.max(0.05, interactRatio - 0.05);

  return {
    total_minutes: totalMinutes,
    intro_ratio: introRatio,
    interact_ratio: interactRatio,
    intro_style: introStyle,
    language_style: languageStyle,
    case_density: caseDensity,
    interact_frequency: interactFreq,
    difficulty_level: difficulty,
    homework_layers: homeworkLayers,
    include_board_design: includeBoard,
  };
}

// 恢复默认参数
function resetLessonParams() {
  const defaults = {
    paramTotalMinutes: '90',
    paramIntroStyle: 'auto',
    paramLanguageStyle: 'plain',
    paramCaseDensity: 'medium',
    paramInteractFreq: 'medium',
    paramDifficulty: 'match',
    paramHomeworkLayers: '3',
    paramBoardDesign: 'true',
  };
  Object.entries(defaults).forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  });
  toast('已恢复默认参数');
}

async function generateLesson() {
  if (state.knowledgePoints.length === 0) { toast('请先提取知识点'); return; }
  const btn = document.getElementById('genLessonBtn');
  const addieChecked = document.getElementById('addieModeCheckbox')?.checked;
  btn.disabled = true;
  btn.textContent = addieChecked ? 'ADDIE审议中...' : '生成中...';
  appendAiMessage(addieChecked
    ? '已启用 ADDIE 多智能体审议：学情分析 → 教案生成 → 自评 → 精修，预计 1-2 分钟...'
    : '正在按六阶段结构生成教案，请稍候（约30-60秒）...');

  try {
    const fd = new FormData();
    fd.append('chapter', state.currentChapter);
    fd.append('knowledge_points', JSON.stringify(state.knowledgePoints));
    // 从参数面板读取配置
    const params = collectLessonParams();
    fd.append('params', JSON.stringify(params));
    // 关联到当前选中的章节（若有）
    if (state.currentChapterId !== null) {
      fd.append('chapter_id', state.currentChapterId);
    }
    // 模板 ID（H4：activeTemplateId）
    if (state.activeTemplateId) {
      fd.append('template_id', String(state.activeTemplateId));
    }
    // ADDIE 多智能体审议模式
    if (addieChecked) fd.append('mode', 'addie');

    const data = await api(`/api/courses/${state.currentCourseId}/generate-lesson`, { method: 'POST', body: fd });
    state.currentLessonId = data.data.id;
    renderLessonPreview(data.data.plan);
    document.getElementById('previewMeta').textContent = `${data.data.plan.total_minutes} 分钟`;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('exportMdBtn').disabled = false;
    document.getElementById('exportDocxBtn').disabled = false;
    document.getElementById('evaluateLessonBtn').disabled = false;

    // 渲染 ADDIE 审议过程卡片(若启用)
    let addieCard = '';
    if (addieChecked && data.data.addie_meta) {
      const m = data.data.addie_meta;
      const la = m.learner_analysis || {};
      const ev = m.evaluation || {};
      const issues = (ev.issues || []).slice(0, 4);
      const score = typeof ev.overall_score === 'number' ? (ev.overall_score >= 0 ? `${ev.overall_score}/100` : '审议失败') : '-';
      const issuesHtml = issues.length
        ? issues.map(i => `<li><span class="px-1 rounded ${i.severity==='error'?'bg-red-50 text-red-700':'bg-amber-50 text-amber-700'} text-[10px]">${i.severity==='error'?'错误':'警告'}</span> <span class="text-muted">[${escapeHtml(i.dimension||'')}]</span> ${escapeHtml(i.description||'')}</li>`).join('')
        : '<li class="text-muted">未发现问题</li>';
      addieCard = `
        <details class="mt-2 border border-teal-200 bg-teal-50/40 rounded-md p-2 text-xs">
          <summary class="cursor-pointer text-teal-700 font-medium select-none">🔍 ADDIE 多智能体审议过程${m.refined ? '（已精修）' : ''} · 自评 ${score}</summary>
          <div class="mt-2 space-y-2">
            <div><b class="text-ink">学情摘要：</b>${escapeHtml(la.learner_summary || '-')}</div>
            ${la.cognitive_obstacles && la.cognitive_obstacles.length ? `<div><b class="text-ink">认知障碍点：</b>${la.cognitive_obstacles.map(o=>escapeHtml(o)).join('；')}</div>` : ''}
            ${la.key_strategies && la.key_strategies.length ? `<div><b class="text-ink">关键策略：</b>${la.key_strategies.map(o=>escapeHtml(o)).join('；')}</div>` : ''}
            <div><b class="text-ink">自评问题清单：</b><ul class="list-disc pl-4 space-y-0.5 mt-0.5">${issuesHtml}</ul></div>
            ${m.refine_error ? `<div class="text-red-600">精修失败：${escapeHtml(m.refine_error)}</div>` : ''}
          </div>
        </details>`;
    }

    appendAiMessage(`<b class="text-teal-600">教案生成完成 ✓</b>${addieChecked ? ' <span class="text-[10px] text-teal-700">(ADDIE 多智能体审议)</span>' : ''}<br><span class="text-xs text-muted">六阶段已编排：${data.data.plan.stages.map(s => s.name).join(' / ')}</span>${addieCard}<br><span class="text-xs">现在可以在下方对话框输入修改意见，或点击 ③ 生成PPT 按钮制作教学课件，也可导出教案（Markdown / DOCX）</span>`);
    // 思维导图联动：教案生成后刷新
    await refreshMindmapIfOpen();
  } catch (e) {
    appendAiMessage(`<span class="text-red-600">生成失败：</span>${escapeHtml(e.message)}`);
    // I: 改使用 showOperationFailure
    const retryFn = () => generateLesson();
    const lowerParamsFn = () => {
      try {
        const cur = parseFloat(document.getElementById('llmTemperature').value);
        const max = parseInt(document.getElementById('llmMaxTokens').value);
        if (!isNaN(cur)) document.getElementById('llmTemperature').value = (cur / 2).toFixed(2);
        if (!isNaN(max)) document.getElementById('llmMaxTokens').value = Math.round(max * 1.5);
      } catch(_) {}
      generateLesson();
    };
    const tplFillFn = async () => {
      try {
        if (state.currentLessonId) {
          const res = await api(`/api/lessons/${state.currentLessonId}/fallback-template`, { method: 'POST' });
          if (res && res.data && res.data.plan) {
            state.currentLessonId = res.data.id || state.currentLessonId;
            renderLessonPreview(res.data.plan);
            toast('已使用模板快速填充');
            closeOperationFailure();
            return;
          }
        }
        // 兜底：调用教案模板库默认模板拼接
        toast('当前无教案ID，已打开模板库供手动选用');
        openTemplateLibrary();
      } catch (err) {
        toast('模板填充失败：' + err.message);
      }
    };
    showOperationFailure('教案生成失败', e, {
      retryFn,
      lowerParamsFn,
      templateId: state.activeTemplateId,
      fallbackFn: tplFillFn,
      draftData: {
        course_id: state.currentCourseId,
        chapter: state.currentChapter,
        chapter_id: state.currentChapterId,
        knowledge_points: state.knowledgePoints,
        params: collectLessonParams(),
        template_id: state.activeTemplateId,
      },
      onHelp: openTutorial,
    });
  } finally {
    btn.disabled = false;
    btn.textContent = '② 生成教案';
  }
}

// ==================== 教案预览渲染 ====================
function renderLessonPreview(plan) {
  const el = document.getElementById('previewContent');
  if (!plan) {
    el.innerHTML = '<div class="text-center text-xs text-muted py-10">教案为空</div>';
    return;
  }

  // 标题表格
  const titleTable = `
    <table class="title-table">
      <tr><td colspan="2"><h1>${escapeHtml(plan.course_name)} · ${escapeHtml(plan.chapter)} 教案</h1></td></tr>
      <tr><td colspan="2" style="font-size:0.75rem;color:#8a7968;font-style:italic">总课时：${plan.total_minutes} 分钟</td></tr>
    </table>
  `;

  // 基本信息表格
  const infoRows = [];
  infoRows.push(`<tr><td>课程名称</td><td>${escapeHtml(plan.course_name || '')}</td></tr>`);
  infoRows.push(`<tr><td>授课章节</td><td>${escapeHtml(plan.chapter || '')}</td></tr>`);
  if (plan.teaching_object) infoRows.push(`<tr><td>授课对象</td><td>${escapeHtml(plan.teaching_object)}</td></tr>`);
  if (plan.teacher_name) infoRows.push(`<tr><td>授课教师</td><td>${escapeHtml(plan.teacher_name)}</td></tr>`);
  infoRows.push(`<tr><td>课时安排</td><td>${plan.total_minutes} 分钟</td></tr>`);
  const infoTable = `<table class="info-table"><tbody>${infoRows.join('')}</tbody></table>`;

  // 教学目标表格（三行，每行两列）
  const goalTable = `
    <table class="goal-table">
      <tr><td class="goal-knowledge">知识目标</td><td>${escapeHtml(plan.knowledge_goal || '')}</td></tr>
      <tr><td class="goal-ability">能力目标</td><td>${escapeHtml(plan.ability_goal || '')}</td></tr>
      <tr><td class="goal-value">素质/思政目标</td><td>${escapeHtml(plan.value_goal || '')}</td></tr>
    </table>
  `;

  // 教学重难点表格
  const keyDiffRows = [];
  if ((plan.key_points || []).length > 0) {
    keyDiffRows.push(`<tr><td class="td-key">教学重点</td><td><ul>${(plan.key_points || []).map(k => `<li>${escapeHtml(k)}</li>`).join('')}</ul></td></tr>`);
  }
  if ((plan.difficult_points || []).length > 0) {
    keyDiffRows.push(`<tr><td class="td-diff">教学难点</td><td><ul>${(plan.difficult_points || []).map(d => `<li>${escapeHtml(d)}</li>`).join('')}</ul></td></tr>`);
  }
  if (plan.difficult_strategy) {
    keyDiffRows.push(`<tr><td style="background:rgba(46,125,110,0.08);color:#2e7d6e">突破策略</td><td>${escapeHtml(plan.difficult_strategy)}</td></tr>`);
  }
  const keyDiffTable = keyDiffRows.length ? `<table class="key-diff-table"><tbody>${keyDiffRows.join('')}</tbody></table>` : '';

  // 教学过程表格
  const stagesTable = (() => {
    if (!plan.stages || plan.stages.length === 0) {
      return '<table class="stages-table"><tr><td colspan="5" style="text-align:center;color:#8a7968">暂无教学过程</td></tr></table>';
    }
    const rows = plan.stages.map((s, i) => `
      <tr>
        <td class="stage-name">${i+1}. ${escapeHtml(s.name)}<br><span class="text-muted text-[10px]">${s.duration_min}分钟</span></td>
        <td>${escapeHtml(s.teacher_activity || '')}</td>
        <td>${escapeHtml(s.student_activity || '')}</td>
        <td>${escapeHtml(s.design_intent || '')}</td>
        <td>${s.content ? escapeHtml(s.content) : '<span class="text-muted">-</span>'}</td>
      </tr>
    `).join('');
    return `
      <table class="stages-table">
        <thead>
          <tr>
            <th>阶段/时长</th>
            <th>教师行为</th>
            <th>学生行为</th>
            <th>设计意图</th>
            <th>教学内容</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  })();

  // 板书设计表格
  const boardTable = plan.board_design ? `
    <table class="board-table">
      <tr><td>板书设计</td><td style="font-family:monospace;font-size:0.8rem;white-space:pre-wrap">${escapeHtml(plan.board_design)}</td></tr>
    </table>
  ` : '';

  // 课后作业表格
  const hwRows = (plan.homework || []).map((h, i) => `<tr><td>${i+1}</td><td>${escapeHtml(h)}</td></tr>`).join('');
  const homeworkTable = hwRows ? `<table class="homework-table"><tbody>${hwRows}</tbody></table>` : '';

  // 教学反思表格
  const reflectionTable = `
    <table class="reflection-table">
      <tr><td style="width:80px;background:rgba(46,125,110,0.06);font-weight:500">教学反思</td><td>${escapeHtml(plan.reflection || '（课后填写）')}</td></tr>
    </table>
  `;

  // 知识点出处表格（取自 state.knowledgePoints）
  const kpPages = (state.knowledgePoints || [])
    .filter(kp => kp.source_pages)
    .map((kp, i) => `<tr><td style="width:40%;font-weight:500">${escapeHtml(kp.name)}</td><td style="width:30%;color:#2e7d6e"><svg class="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg> ${escapeHtml(kp.source_pages)}</td><td style="width:30%;color:#8a7968;font-size:0.7rem">${escapeHtml(kp.definition ? kp.definition.slice(0, 60) + (kp.definition.length > 60 ? '...' : '') : '')}</td></tr>`)
    .join('');
  const textbookRefTable = kpPages ? `
    <table class="textbook-ref-table" style="width:100%;border-collapse:collapse;font-size:0.75rem">
      <thead><tr style="background:rgba(46,125,110,0.08)"><th style="padding:6px 8px;text-align:left;border:1px solid #d4c9b8">知识点</th><th style="padding:6px 8px;text-align:left;border:1px solid #d4c9b8">教材出处</th><th style="padding:6px 8px;text-align:left;border:1px solid #d4c9b8">简述</th></tr></thead>
      <tbody>${kpPages}</tbody>
    </table>
  ` : '';

  // 组装完整 HTML
  const hasRef = !!textbookRefTable;
  const hasSrc = !!plan.source_text;
  const hasBoard = !!plan.board_design;
  const hasHw = !!homeworkTable;
  const nums = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  let n = 4; // 从四开始（一、二、三已用）
  el.innerHTML = `
    ${titleTable}

    <h2>一、教学基本信息</h2>
    ${infoTable}

    <h2>二、教学目标</h2>
    ${goalTable}

    <h2>三、教学重难点</h2>
    ${keyDiffTable || '<table><tr><td colspan="2" style="text-align:center;color:#8a7968">暂无</td></tr></table>'}

    ${hasRef ? `<h2>${nums[n++]}、知识点出处</h2>${textbookRefTable}` : ''}

    ${hasSrc ? `
    <h2>${nums[n++]}、教案原文</h2>
    <table class="source-text-table">
      <tr><td style="padding:10px;font-size:0.8rem;line-height:1.7;white-space:pre-wrap">${escapeHtml(plan.source_text)}</td></tr>
    </table>
    ` : ''}

    <h2>${nums[n++]}、教学过程设计</h2>
    ${hasSrc ? '<table class="stages-table"><tr><td colspan="5" style="text-align:center;color:#8a7968;font-size:0.8rem">已上传教案，请查看上方"教案原文"</td></tr></table>' : stagesTable}

    ${hasBoard ? `<h2>${nums[n++]}、板书设计</h2>${boardTable}` : ''}

    ${hasHw ? `<h2>${nums[n++]}、课后作业</h2>${homeworkTable}` : ''}

    <h2>${nums[n]}、教学反思</h2>
    ${reflectionTable}
  `;
  el.scrollTop = 0;
}

// ==================== 历史教案（按章节查看）====================
async function loadLessonsByChapter(courseId, chapterId) {
  // 加载该课程的所有教案，过滤出当前章节的（通过 chapter 名匹配，或显示全部）
  try {
    const data = await api(`/api/courses/${courseId}/lessons`);
    let lessons = data.data || [];
    // 如果选了具体章节，按章节名过滤
    if (chapterId !== null && state.currentChapter) {
      lessons = lessons.filter(l => l.chapter === state.currentChapter);
    }
    return lessons;
  } catch (e) {
    console.error(e);
    return [];
  }
}

// ==================== 预览标签切换 ====================
function switchPreviewTab(tab) {
  const lessonTab = document.getElementById('previewTabLesson');
  const pptTab = document.getElementById('previewTabPpt');
  const lessonContent = document.getElementById('previewContent');
  const pptContent = document.getElementById('pptPreviewContent');
  const lessonBar = document.getElementById('lessonActionBar');
  const pptBar = document.getElementById('pptActionBar');
  const lessonFileList = document.getElementById('lessonFileList');
  const pptFileList = document.getElementById('pptFileList');

  if (tab === 'ppt') {
    lessonTab?.classList.remove('active');
    pptTab?.classList.add('active');
    lessonContent?.classList.remove('fade-switch');
    lessonContent?.classList.add('fade-hide');
    pptContent?.classList.remove('fade-hide');
    pptContent?.classList.add('fade-switch');
    if (lessonBar) lessonBar.style.display = 'none';
    if (pptBar) pptBar.style.display = 'flex';
    if (lessonFileList) lessonFileList.classList.add('hidden');
    if (pptFileList) pptFileList.classList.remove('hidden');
  } else {
    pptTab?.classList.remove('active');
    lessonTab?.classList.add('active');
    pptContent?.classList.remove('fade-switch');
    pptContent?.classList.add('fade-hide');
    lessonContent?.classList.remove('fade-hide');
    lessonContent?.classList.add('fade-switch');
    if (pptBar) pptBar.style.display = 'none';
    if (lessonBar) lessonBar.style.display = 'flex';
    if (pptFileList) pptFileList.classList.add('hidden');
    if (lessonFileList) lessonFileList.classList.remove('hidden');
  }
}

// ==================== 功能提示（可关闭） ====================
function showTip(key, msg) {
  if (localStorage.getItem('tip_' + key)) return;
  const container = document.getElementById('tipContainer');
  if (!container) return;
  const tip = document.createElement('div');
  tip.className = 'tip-item flex items-center gap-1 bg-yellow-50 border border-yellow-200 text-xs text-yellow-800 px-2 py-1 rounded mb-1 pointer-events-auto';
  tip.innerHTML = '<span class="flex-1">' + msg + '</span><button class="tip-dismiss text-yellow-400 hover:text-yellow-600 font-bold leading-none" onclick="this.parentElement.remove();localStorage.setItem(\'tip_' + key + '\',\'1\')">&times;</button>';
  container.appendChild(tip);
}

// ==================== PPT记录管理 ====================
async function loadPptRecords(courseId, chapterId, chapterName) {
  try {
    const data = await api(`/api/courses/${courseId}/ppt-records`);
    let records = data.data || [];
    if (chapterId !== null && chapterId !== undefined && chapterName) {
      records = records.filter(r => r.chapter === chapterName);
    }
    renderPptRecordList(records);
  } catch (e) {
    console.error('加载PPT记录失败:', e);
    document.getElementById('pptFileList').innerHTML = '<div class="text-xs text-muted text-center py-2">加载失败</div>';
  }
}

// ==================== 本地上传 ====================
// 教案上传
document.getElementById('uploadLessonBtn').onclick = () => {
  document.getElementById('uploadLessonInput').click();
};
document.getElementById('uploadLessonInput').onchange = async (e) => {
  const file = e.target.files?.[0];
  if (!file || !state.currentCourseId) return;
  const formData = new FormData();
  formData.append('file', file);
  const btn = document.getElementById('uploadLessonBtn');
  btn.disabled = true; btn.innerHTML = '<span class="w-3.5 h-3.5 inline-block animate-spin border-2 border-teal-600 border-t-transparent rounded-full"></span>';
  try {
    const res = await fetch(`/api/courses/${state.currentCourseId}/upload-lesson`, { method: 'POST', body: formData });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || '上传失败');
    toast('教案上传成功');
    await loadLessonsList(state.currentCourseId, null, null);
  } catch (err) {
    toast('上传失败: ' + err.message);
  }
  btn.disabled = false; btn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>';
  e.target.value = '';
};
// PPT上传
document.getElementById('uploadPptBtn').onclick = () => {
  document.getElementById('uploadPptInput').click();
};
document.getElementById('uploadPptInput').onchange = async (e) => {
  const file = e.target.files?.[0];
  if (!file || !state.currentCourseId) return;
  const formData = new FormData();
  formData.append('file', file);
  const btn = document.getElementById('uploadPptBtn');
  btn.disabled = true; btn.innerHTML = '<span class="w-3.5 h-3.5 inline-block animate-spin border-2 border-teal-600 border-t-transparent rounded-full"></span>';
  try {
    const res = await fetch(`/api/courses/${state.currentCourseId}/upload-ppt`, { method: 'POST', body: formData });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || '上传失败');
    toast('PPT上传成功');
    await loadPptRecords(state.currentCourseId, state.currentChapterId, state.currentChapter);
  } catch (err) {
    toast('上传失败: ' + err.message);
  }
  btn.disabled = false; btn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>';
  e.target.value = '';
};

// ==================== 侧栏排序（拖拽调整上下顺序） ====================
function initSidebarSort() {
  const container = document.getElementById('leftPanel');
  const sections = container.querySelectorAll('.sidebar-section');
  let dragEl = null, dragSrcY = 0, dragOffsetY = 0;

  sections.forEach(s => {
    const handle = s.querySelector('.drag-handle');
    if (!handle) return;
    handle.addEventListener('mousedown', (e) => {
      e.preventDefault();
      dragEl = s;
      dragSrcY = e.clientY;
      dragOffsetY = 0;
      s.style.transition = 'none';
      s.style.opacity = '0.6';
      s.style.transform = 'scale(0.98)';
      document.body.style.cursor = 'grabbing';
      document.addEventListener('mousemove', onDragMove);
      document.addEventListener('mouseup', onDragUp);
    });
  });

  function onDragMove(e) {
    if (!dragEl) return;
    dragOffsetY = e.clientY - dragSrcY;
    const siblings = [...container.querySelectorAll('.sidebar-section')];
    const idx = siblings.indexOf(dragEl);
    if (idx < 0) return;
    // 向上移
    if (dragOffsetY < -15 && idx > 0) {
      const prev = siblings[idx - 1];
      container.insertBefore(dragEl, prev);
      dragSrcY = e.clientY;
      dragOffsetY = 0;
      saveSectionOrder();
    }
    // 向下移
    if (dragOffsetY > 15 && idx < siblings.length - 1) {
      const next = siblings[idx + 1];
      container.insertBefore(next, dragEl);
      dragSrcY = e.clientY;
      dragOffsetY = 0;
      saveSectionOrder();
    }
  }
  function onDragUp() {
    if (!dragEl) return;
    dragEl.style.transition = '';
    dragEl.style.opacity = '1';
    dragEl.style.transform = '';
    document.body.style.cursor = '';
    dragEl = null;
    document.removeEventListener('mousemove', onDragMove);
    document.removeEventListener('mouseup', onDragUp);
  }
}

function saveSectionOrder() {
  const container = document.getElementById('leftPanel');
  const sections = container.querySelectorAll('.sidebar-section');
  const order = [...sections].map(s => s.dataset.section || '');
  try { localStorage.setItem('sidebar_section_order', JSON.stringify(order)); } catch {}
}

function loadSectionOrder() {
  try {
    const order = JSON.parse(localStorage.getItem('sidebar_section_order'));
    if (!Array.isArray(order) || order.length === 0) return;
    const container = document.getElementById('leftPanel');
    const sections = container.querySelectorAll('.sidebar-section');
    const map = {};
    sections.forEach(s => { const k = s.dataset.section; if (k) map[k] = s; });
    // 按保存的顺序重新排列
    const parent = container;
    order.forEach(key => {
      const el = map[key];
      if (el && el.parentNode === parent) parent.appendChild(el);
    });
  } catch {}
}

// 初始化侧栏排序
initSidebarSort();
loadSectionOrder();

// 倒三角折叠/展开功能
document.querySelectorAll('.collapse-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const section = btn.closest('.sidebar-section');
    if (section) {
      section.classList.toggle('collapsed');
    }
  });
});

function renderPptRecordList(records) {
  const list = document.getElementById('pptFileList');
  if (!list) return;
  if (records.length === 0) {
    list.innerHTML = '<div class="text-xs text-muted text-center py-2">暂无PPT</div>';
    return;
  }
  const styleLabels = {
    'academic': '学术简约',
    'cyan_ink': '青绿水墨',
    'cute_cartoon': '清新卡通',
    'formal': '商务正式',
    'minimal': '极简黑白',
  };
  list.innerHTML = records.map(r => {
    const isUpload = r.source === 'upload';
    const subText = isUpload ? '本地上传' : (styleLabels[r.style] || r.style) + ' · ' + r.slide_count + '页';
    return `
    <div class="ppt-item" data-id="${r.id}" data-title="${escapeHtml(r.title || r.chapter)}" data-source="${r.source}" data-hasfile="${r.has_file}">
      <svg class="ppt-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
      <span class="ppt-name">${escapeHtml(r.title || r.chapter)} <span class="text-muted text-[10px]">${subText}</span></span>
      <span class="ppt-date">${r.created_at ? formatDate(r.created_at) : ''}</span>
      ${isUpload && r.has_file ? '<span class="ppt-dl-btn" title="下载PPT">⬇</span>' : ''}
    </div>`;}).join('');
  list.querySelectorAll('.ppt-item').forEach(item => {
    const dlBtn = item.querySelector('.ppt-dl-btn');
    if (dlBtn) {
      dlBtn.onclick = async (e) => {
        e.stopPropagation();
        const id = parseInt(item.dataset.id);
        const source = item.dataset.source;
        try {
          const fetchUrl = source === 'upload' ? `/api/ppt/${id}/download` : `/api/ppt-records/${id}/download`;
          const res = await fetch(fetchUrl, source === 'upload' ? {} : { method: 'POST' });
          if (!res.ok) throw new Error('下载失败');
          const blob = await res.blob();
          const disposition = res.headers.get('Content-Disposition') || '';
          let filename = '教学PPT.pptx';
          const starMatch = disposition.match(/filename\*=UTF-8''([^;]+)/);
          if (starMatch) filename = decodeURIComponent(starMatch[1]);
          else { const m = disposition.match(/filename="([^"]+)"/); if (m) filename = m[1]; }
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = filename;
          document.body.appendChild(a); a.click(); a.remove();
          URL.revokeObjectURL(url);
        } catch (e) {
          toast('下载失败: ' + e.message);
        }
      };
    }
    // 点击PPT记录项，右侧显示详情
    item.onclick = async () => {
      const source = item.dataset.source;
      const hasFile = item.dataset.hasfile === 'true';
      // 上传的PPT直接跳下载
      if (source === 'upload' && hasFile) {
        const id = parseInt(item.dataset.id);
        try {
          const res = await fetch(`/api/ppt/${id}/download`);
          if (!res.ok) throw new Error('下载失败');
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = item.dataset.title + '.pptx';
          document.body.appendChild(a); a.click(); a.remove();
          URL.revokeObjectURL(url);
        } catch (e) {
          toast('下载失败: ' + e.message);
        }
        return;
      }
      try {
        const data = await api(`/api/ppt-records/${item.dataset.id}`);
        const r = data.data;
        const styleLabels = { 'academic': '学术简约', 'cyan_ink': '青绿水墨', 'cute_cartoon': '清新卡通', 'formal': '商务正式', 'minimal': '极简黑白' };
        const densityLabels = { 'detailed': '详细', 'moderate': '适中', 'concise': '精简' };
        const imageLabels = { 'none': '纯文字', 'icons': '图标装饰', 'rich': '丰富布局' };
        const slides = (r.slide_data && r.slide_data.slides) || [];
        let slidesHtml = '';
        if (slides.length > 0) {
          slidesHtml = slides.map((s, i) => `
            <div class="bg-white/60 border border-rule rounded p-2 mb-1 text-xs">
              <div class="font-medium text-teal-700">第${i+1}页：${escapeHtml(s.title || '')}</div>
              <div class="text-muted mt-1">${escapeHtml((s.content || '').slice(0, 200))}</div>
            </div>
          `).join('');
        }
        // 知识点教材出处
        const kpPagesHtml = (state.knowledgePoints || [])
          .filter(kp => kp.source_pages)
          .map(kp => `<div class="flex items-center gap-1.5 text-[11px] py-0.5"><span class="text-ink font-medium">${escapeHtml(kp.name)}</span><span class="text-teal-600">${escapeHtml(kp.source_pages)}</span></div>`)
          .join('');
        const kpPagesSection = kpPagesHtml ? `
          <div class="mt-3">
            <div class="text-xs font-semibold text-muted mb-1">📖 知识点教材出处</div>
            <div class="bg-teal-50/50 border border-teal-200 rounded p-2">${kpPagesHtml}</div>
          </div>
        ` : '';

        document.getElementById('previewContent').innerHTML = `
          <div class="text-xs">
            <div class="font-serif font-bold text-base text-teal-700 mb-3">📊 PPT详情</div>
            <table class="info-table">
              <tr><td>标题</td><td>${escapeHtml(r.title)}</td></tr>
              <tr><td>章节</td><td>${escapeHtml(r.chapter)}</td></tr>
              <tr><td>风格</td><td>${styleLabels[r.style] || r.style}</td></tr>
              <tr><td>内容密度</td><td>${densityLabels[r.content_density] || r.content_density}</td></tr>
              <tr><td>视觉元素</td><td>${imageLabels[r.image_style] || r.image_style}</td></tr>
              <tr><td>幻灯片数</td><td>${r.slide_count} 页</td></tr>
              <tr><td>生成时间</td><td>${r.created_at ? new Date(r.created_at).toLocaleString() : ''}</td></tr>
            </table>
            ${kpPagesSection}
            ${slidesHtml ? `<div class="mt-3"><div class="text-xs font-semibold text-muted mb-1">幻灯片预览</div>${slidesHtml}</div>` : ''}
            <div class="mt-3 flex gap-2">
              <button class="btn-primary px-3 py-1 rounded text-xs" onclick="(async()=>{try{const res=await fetch('/api/ppt-records/${r.id}/download',{method:'POST'});if(!res.ok)throw new Error('下载失败');const blob=await res.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='${escapeHtml(r.title || 'ppt')}.pptx';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);toast('下载成功');}catch(e){toast('下载失败: '+e.message);}})()">⬇ 下载PPT</button>
              <button class="btn-ghost px-3 py-1 rounded text-xs" onclick="(async()=>{if(!await showConfirm('删除PPT记录','确认删除此PPT记录？'))return;try{await api('/api/ppt-records/${r.id}',{method:'DELETE'});toast('已删除');loadPptRecords(${state.currentCourseId},${state.currentChapterId ? state.currentChapterId : 'null'},'${(state.currentChapter || '').replace(/'/g, "\\'")}');document.getElementById('previewContent').innerHTML='<div class=\\'text-center text-xs text-muted py-10\\'><div class=\\'font-serif text-base text-teal-700 mb-2\\'>教案预览区</div></div>';}catch(e){toast('删除失败: '+e.message)}})()">🗑 删除</button>
            </div>
          </div>
        `;
        document.getElementById('previewMeta').textContent = `${r.slide_count} 页 · ${styleLabels[r.style] || r.style}`;
      } catch (e) {
        toast('加载PPT详情失败: ' + e.message);
      }
    };
  });
}

// ==================== PPT 幻灯片预览（WPS 式轮播）====================
let _pptPanelRecordId = null;
let _pptPanelRecordData = null;

function renderPptPreviewInPanel(recordData) {
 if (!recordData) return;
 _pptPanelRecordId = recordData.id;
 _pptPanelRecordData = recordData;
 const container = document.getElementById('pptPreviewContent');
 const slideData = recordData.slide_data;
 if (!slideData || !slideData.slides || !slideData.slides.length) {
  container.innerHTML = '<div class="text-center text-xs text-muted py-10">暂无幻灯片数据</div>';
  document.getElementById('pptSaveBtn')?.classList.add('hidden');
  document.getElementById('pptFullscreenBtn')?.setAttribute('disabled', 'disabled');
  return;
 }
 const slides = slideData.slides;
 document.getElementById('pptSaveBtn')?.classList.remove('hidden');
 document.getElementById('pptFullscreenBtn')?.removeAttribute('disabled');
 const stageColors = ['#0891b2', '#7c3aed', '#059669', '#d97706', '#dc2626', '#2563eb'];
 const stageLabels = ['导入', '新授', '互动', '练习', '小结', '拓展'];
 let currentIdx = 0;
 function renderSlideContent(idx) {
  const s = slides[idx];
  if (!s) return '';
  const stageName = s.stage || '';
  const stageIdx = stageLabels.indexOf(stageName);
  const color = stageIdx >= 0 ? stageColors[stageIdx] : '#6b7280';
  let contentHtml = '';
  if (s.title) contentHtml += `<div class="text-base font-bold mb-2" style="color:${color}">${escapeHtml(s.title)}</div>`;
  if (s.subtitle) contentHtml += `<div class="text-sm text-gray-600 mb-2">${escapeHtml(s.subtitle)}</div>`;
  if (s.content) contentHtml += `<div class="text-sm leading-relaxed mb-2">${escapeHtml(s.content)}</div>`;
  if (s.teacher_activity) contentHtml += `<div class="text-xs text-gray-500 mb-1"><span class="font-medium">教师活动：</span>${escapeHtml(s.teacher_activity)}</div>`;
  if (s.student_activity) contentHtml += `<div class="text-xs text-gray-500 mb-1"><span class="font-medium">学生活动：</span>${escapeHtml(s.student_activity)}</div>`;
  if (s.duration) contentHtml += `<div class="text-xs text-gray-400 mt-1">⏱ ${escapeHtml(s.duration)}</div>`;
  if (s.bullet_points && s.bullet_points.length) {
   contentHtml += '<ul class="list-disc pl-4 mt-1 text-xs space-y-0.5">';
   s.bullet_points.forEach(bp => { contentHtml += `<li>${escapeHtml(bp)}</li>`; });
   contentHtml += '</ul>';
  }
  if (!contentHtml) contentHtml = '<div class="text-xs text-gray-400">（空幻灯片）</div>';
  return contentHtml;
 }
 function navigateTo(idx) {
  if (idx < 0 || idx >= slides.length) return;
  currentIdx = idx;
  const slideContent = document.getElementById('pptSlideContent');
  const slideCounter = document.getElementById('pptSlideCounter');
  const prevBtn = document.getElementById('pptPrevBtn');
  const nextBtn = document.getElementById('pptNextBtn');
  const thumbs = document.querySelectorAll('.ppt-thumb');
  if (slideContent) slideContent.innerHTML = renderSlideContent(idx);
  if (slideCounter) slideCounter.textContent = `${idx + 1} / ${slides.length}`;
  if (prevBtn) prevBtn.disabled = idx === 0;
  if (nextBtn) nextBtn.disabled = idx >= slides.length - 1;
  thumbs.forEach((t, i) => {
   t.classList.toggle('border-teal-500', i === idx);
   t.classList.toggle('border-gray-200', i !== idx);
  });
 }
 let thumbsHtml = '';
 slides.forEach((s, i) => {
  const title = s.title || `幻灯片 ${i + 1}`;
  const stageName = s.stage || '';
  const stageIdx = stageLabels.indexOf(stageName);
  const color = stageIdx >= 0 ? stageColors[stageIdx] : '#6b7280';
  thumbsHtml += `<div class="ppt-thumb flex-shrink-0 w-16 h-10 rounded border-2 ${i === 0 ? 'border-teal-500' : 'border-gray-200'} bg-white overflow-hidden cursor-pointer flex flex-col items-center justify-center text-center p-0.5" data-index="${i}" style="min-width:4rem" title="${escapeHtml(title)}"><div class="text-xs font-bold leading-tight truncate w-full" style="color:${color};font-size:9px">${escapeHtml(title)}</div></div>`;
 });
 container.innerHTML = `
<div class="ppt-carousel flex flex-col h-full" style="user-select:none">
 <div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 bg-white flex-shrink-0">
  <div class="flex items-center gap-2">
   <span class="text-xs font-bold text-gray-700">PPT预览</span>
   <span class="text-xs text-gray-400">${slides.length} 页</span>
  </div>
  <div class="flex items-center gap-1">
   <button onclick="event.stopPropagation();renderPptFullscreen()" class="text-xs text-gray-400 hover:text-gray-600 px-1.5 py-0.5 rounded hover:bg-gray-100" title="全屏播放">⛶ 全屏</button>
  </div>
 </div>
 <div class="flex-1 flex items-center justify-center p-4 bg-gray-50 overflow-hidden">
  <div class="ppt-slide-card w-full max-w-lg bg-white rounded-lg shadow-md p-6" style="aspect-ratio:4/3;overflow-y:auto">
   <div id="pptSlideContent" class="text-sm">${renderSlideContent(0)}</div>
  </div>
 </div>
 <div class="flex items-center justify-between px-3 py-2 border-t border-gray-200 bg-white flex-shrink-0">
  <button id="pptPrevBtn" class="ppt-nav-btn text-xs px-3 py-1 rounded border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed" ${slides.length <= 1 ? 'disabled' : ''}>‹ 上一页</button>
  <span id="pptSlideCounter" class="text-xs text-gray-500">1 / ${slides.length}</span>
  <button id="pptNextBtn" class="ppt-nav-btn text-xs px-3 py-1 rounded border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed" ${slides.length <= 1 ? 'disabled' : ''}>下一页 ›</button>
 </div>
 <div class="flex gap-1.5 px-3 py-2 border-t border-gray-100 bg-gray-50 overflow-x-auto flex-shrink-0" style="scrollbar-width:thin">
  ${thumbsHtml}
 </div>
</div>`;
 document.getElementById('pptPrevBtn')?.addEventListener('click', () => navigateTo(currentIdx - 1));
 document.getElementById('pptNextBtn')?.addEventListener('click', () => navigateTo(currentIdx + 1));
 document.querySelectorAll('.ppt-thumb').forEach(el => {
  el.addEventListener('click', () => navigateTo(parseInt(el.dataset.index)));
 });
 document.addEventListener('keydown', function pptKeyNav(e) {
  if (!document.getElementById('pptPreviewContent')?.querySelector('.ppt-carousel')) return;
  if (e.key === 'ArrowLeft') { navigateTo(currentIdx - 1); e.preventDefault(); }
  else if (e.key === 'ArrowRight') { navigateTo(currentIdx + 1); e.preventDefault(); }
 });
}

// 全屏播放PPT
function renderPptFullscreen() {
  if (!_pptPanelRecordData || !_pptPanelRecordData.slide_data || !_pptPanelRecordData.slide_data.slides) return;
  const slides = _pptPanelRecordData.slide_data.slides;
  let idx = 0;
  const win = window.open('', '_blank', 'width=1200,height=800,toolbar=no,menubar=no');
  if (!win) return;
  win.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>PPT全屏播放</title><style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body { background:#1a1a2e; display:flex; align-items:center; justify-content:center; height:100vh; font-family:"Noto Sans SC",sans-serif; }
    .slide-wrapper { width:80vw; max-width:960px; background:#fff; border-radius:12px; padding:48px 64px; box-shadow:0 20px 60px rgba(0,0,0,0.5); min-height:60vh; max-height:80vh; overflow-y:auto; position:relative; }
    .nav { position:fixed; bottom:40px; left:50%; transform:translateX(-50%); display:flex; gap:24px; align-items:center; }
    .nav button { background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.3); padding:10px 28px; border-radius:8px; cursor:pointer; font-size:15px; }
    .nav button:hover { background:rgba(255,255,255,0.25); }
    .nav button:disabled { opacity:0.3; cursor:default; }
    .nav .counter { color:rgba(255,255,255,0.6); font-size:14px; }
    .close-btn { position:fixed; top:20px; right:20px; background:rgba(255,255,255,0.1); color:#fff; border:none; width:36px; height:36px; border-radius:50%; cursor:pointer; font-size:18px; }
    .close-btn:hover { background:rgba(255,255,255,0.2); }
  </style></head><body>
    <button class="close-btn" onclick="window.close()">&times;</button>
    <div class="slide-wrapper" id="slideContent"></div>
    <div class="nav">
      <button id="prevBtn" disabled>‹ 上一页</button>
      <span class="counter" id="counter">1 / ${slides.length}</span>
      <button id="nextBtn">下一页 ›</button>
    </div>
    <script>
      const slides = ${JSON.stringify(slides)};
      let idx = 0;
      const content = document.getElementById('slideContent');
      const counter = document.getElementById('counter');
      const prev = document.getElementById('prevBtn');
      const next = document.getElementById('nextBtn');
      function render(i) {
        const s = slides[i];
        if (!s) return;
        let html = '';
        if (s.title) html += '<h2 style="color:#2e7d6e;margin-bottom:12px">' + s.title + '</h2>';
        if (s.subtitle) html += '<h4 style="color:#666;margin-bottom:8px;font-weight:400">' + s.subtitle + '</h4>';
        if (s.content) html += '<p style="line-height:1.8;font-size:15px;margin-bottom:12px">' + s.content + '</p>';
        if (s.teacher_activity) html += '<p style="font-size:13px;color:#555;margin-bottom:4px"><strong>教师活动：</strong>' + s.teacher_activity + '</p>';
        if (s.student_activity) html += '<p style="font-size:13px;color:#555;margin-bottom:4px"><strong>学生活动：</strong>' + s.student_activity + '</p>';
        if (s.duration) html += '<p style="font-size:12px;color:#999;margin-top:8px">⏱ ' + s.duration + '</p>';
        if (s.bullet_points && s.bullet_points.length) {
          html += '<ul style="margin-top:8px;padding-left:20px">';
          s.bullet_points.forEach(b => { html += '<li style="font-size:13px;line-height:1.6">' + b + '</li>'; });
          html += '</ul>';
        }
        content.innerHTML = html || '<p style="color:#999">（空幻灯片）</p>';
        counter.textContent = (i + 1) + ' / ' + slides.length;
        prev.disabled = i === 0;
        next.disabled = i >= slides.length - 1;
      }
      render(0);
      prev.onclick = () => { if (idx > 0) { idx--; render(idx); } };
      next.onclick = () => { if (idx < slides.length - 1) { idx++; render(idx); } };
      document.addEventListener('keydown', e => {
        if (e.key === 'ArrowLeft') { if (idx > 0) { idx--; render(idx); } }
        else if (e.key === 'ArrowRight') { if (idx < slides.length - 1) { idx++; render(idx); } }
        else if (e.key === 'Escape') { window.close(); }
      });
    <\/script>
  </body></html>`);
  win.document.close();
}

// 保存PPT幻灯片（从 _pptPanelRecordData 读取，保留DOM回退）
async function savePptSlides(btn) {
 const recordId = parseInt(btn.dataset.recordId);
 let slides = [];
 if (_pptPanelRecordData && _pptPanelRecordData.slide_data && _pptPanelRecordData.slide_data.slides) {
  slides = _pptPanelRecordData.slide_data.slides;
 } else {
  const container = document.getElementById('pptPreviewContent');
  const slideCards = container.querySelectorAll('.slide-edit-card');
  slideCards.forEach(card => {
   const titleEl = card.querySelector('.slide-edit-title');
   const textEls = card.querySelectorAll('.slide-edit-text');
   const bulletsEl = card.querySelector('.slide-edit-bullets');
   const slide = {};
   if (titleEl) slide.title = titleEl.innerText.trim();
   textEls.forEach(el => { const field = el.dataset.field; if (field) slide[field] = el.innerText.trim(); });
   if (bulletsEl) { const raw = bulletsEl.innerText.trim(); slide.bullet_points = raw ? raw.split('\n').map(l => l.replace(/^▸\s*/, '').trim()).filter(Boolean) : []; }
   slides.push(slide);
  });
 }
 const originalBtnText = btn.textContent;
 btn.textContent = '保存中...';
 btn.disabled = true;
 try {
  await api(`/api/ppt-records/${recordId}/slides`, { method: 'PUT', body: JSON.stringify({ slide_data: { slides } }) });
  toast('PPT已保存');
 } catch (e) { toast('保存失败: ' + e.message, 'error'); } finally { btn.textContent = originalBtnText; btn.disabled = false; }
}

// 刷新思维导图（如果模态框打开则重新生成）
async function refreshMindmapIfOpen() {
  const modal = document.getElementById('mindmapModal');
  if (!modal.classList.contains('hidden') && state.currentCourseId && state.knowledgePoints.length > 0) {
    await generateMindmap();
  }
}

// ==================== 聊天记录本地存储 ====================
function getChatStorageKey(courseId) {
  return `chat_history_${courseId}`;
}

function saveChatToLocalStorage(courseId, messages) {
  try {
    const key = getChatStorageKey(courseId);
    const existing = loadChatFromLocalStorage(courseId);
    const merged = mergeChatMessages(existing, messages);
    localStorage.setItem(key, JSON.stringify(merged));
  } catch (e) {
    console.warn('saveChatToLocalStorage failed:', e.message);
  }
}

function loadChatFromLocalStorage(courseId) {
  try {
    const key = getChatStorageKey(courseId);
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.warn('loadChatFromLocalStorage failed:', e.message);
    return [];
  }
}

function clearChatLocalStorage(courseId) {
  try {
    localStorage.removeItem(getChatStorageKey(courseId));
  } catch (e) {
    console.warn('clearChatLocalStorage failed:', e.message);
  }
}

function mergeChatMessages(local, remote) {
  const seen = new Set();
  const result = [];
  const all = [...local, ...remote];
  for (const m of all) {
    const key = m.id ? `${m.role}_${m.id}` : `${m.role}_${m.content}_${m.created_at || ''}`;
    if (!seen.has(key)) {
      seen.add(key);
      result.push(m);
    }
  }
  result.sort((a, b) => {
    if (a.created_at && b.created_at) return new Date(a.created_at) - new Date(b.created_at);
    return 0;
  });
  return result;
}

// ==================== 对话修改 ====================
function appendMessage(role, html, isHtml = false) {
  const stream = document.getElementById('chatStream');
  const div = document.createElement('div');
  div.className = `fade-in flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
  const bubble = document.createElement('div');
  bubble.className = `max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm ${role === 'user' ? 'bubble-user' : 'bubble-ai'}`;
  if (isHtml) bubble.innerHTML = html;
  else bubble.textContent = html;
  div.appendChild(bubble);
  stream.appendChild(div);
  stream.scrollTop = stream.scrollHeight;
}

function appendAiMessage(html) { appendMessage('assistant', html, true); }
function appendUserMessage(text) { appendMessage('user', text, false); }

async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;
  if (!state.currentLessonId) { toast('请先生成教案'); return; }

  appendUserMessage(msg);
  input.value = '';

  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  btn.textContent = '思考中...';
  appendAiMessage('<span class="text-muted">正在修改教案...</span><span class="breathing">●</span>');

  try {
    const data = await api(`/api/lessons/${state.currentLessonId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ course_id: state.currentCourseId, message: msg }),
    });

    // 移除"正在修改..."占位
    document.querySelectorAll('#chatStream .bubble-ai').forEach(b => {
      if (b.innerHTML.includes('正在修改教案')) b.parentElement.remove();
    });

    if (data.data.type === 'modified') {
      renderLessonPreview(data.data.plan);
      appendAiMessage(`<b class="text-teal-600">✓ ${escapeHtml(data.data.response)}</b>`);
    } else if (data.data.type === 'clarify') {
      appendAiMessage(`<b class="text-ochre">需澄清：</b>${escapeHtml(data.data.response)}`);
    } else {
      appendAiMessage(escapeHtml(data.data.response));
    }

    if (state.currentCourseId) {
      const localMsgs = [
        { id: Date.now(), role: 'user', content: msg, created_at: new Date().toISOString() },
        { id: Date.now() + 1, role: 'assistant', content: data.data.response || '', created_at: new Date().toISOString() },
      ];
      saveChatToLocalStorage(state.currentCourseId, localMsgs);
    }
  } catch (e) {
    document.querySelectorAll('#chatStream .bubble-ai').forEach(b => {
      if (b.innerHTML.includes('正在修改教案')) b.parentElement.remove();
    });
    appendAiMessage(`<span class="text-red-600">修改失败：</span>${escapeHtml(e.message)}`);
  } finally {
    btn.disabled = false;
    btn.textContent = '发送';
  }
}

// ==================== 思维导图 ====================
let _mindmapInstance = null;

// 打开思维导图模态框
async function openMindmap() {
  const modal = document.getElementById('mindmapModal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  await generateMindmap();
}

function closeMindmap() {
  const modal = document.getElementById('mindmapModal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  // 销毁实例避免内存泄漏
  if (_mindmapInstance) { try { _mindmapInstance.destroy(); } catch(e) {} _mindmapInstance = null; }
}

// 生成并渲染思维导图
async function generateMindmap() {
  if (!state.currentCourseId || state.knowledgePoints.length === 0) {
    toast('请先提取知识点');
    return;
  }
  const svgEl = document.getElementById('mindmapSvg');
  document.getElementById('mindmapCount').textContent = `(${state.knowledgePoints.length}个知识点)`;

  // 销毁旧实例
  if (_mindmapInstance) { try { _mindmapInstance.destroy(); } catch(e) {} _mindmapInstance = null; }

  try {
    const data = await api(`/api/courses/${state.currentCourseId}/mindmap`, {
      method: 'POST',
      body: JSON.stringify({
        chapter: state.currentChapter,
        knowledge_points: state.knowledgePoints,
      }),
    });

    const markdown = data.data.markdown;
    if (!markdown) { toast('生成思维导图失败：内容为空'); return; }

    // 使用 markmap 渲染
    const { Transformer } = window.markmap;
    const transformer = new Transformer();
    const { root } = transformer.transform(markdown);

    // 清空 SVG
    svgEl.innerHTML = '';

    const { Markmap } = window.markmap;
    _mindmapInstance = Markmap.create(svgEl, {
      duration: 300,
      zoom: true,
      pan: true,
      zoomOnMaxHeight: true,
      fitView: true,
      colorFreezeLevel: 1,
      maxWidth: 300,
      spacingHorizontal: 80,
      spacingVertical: 12,
      nodeMinHeight: 24,
      style: {
        fontFamily: '"Noto Sans SC", "PingFang SC", sans-serif',
      },
    }, root);
  } catch (e) {
    toast('生成思维导图失败: ' + e.message);
    svgEl.innerHTML = `<div class="flex items-center justify-center h-full text-sm text-red-500">生成失败: ${escapeHtml(e.message)}</div>`;
  }
}

// ==================== 导出 ====================
async function exportLesson(fmt) {
  if (!state.currentLessonId) return;
  const btnMap = {
    'markdown': 'exportMdBtn',
    'docx': 'exportDocxBtn',
  };
  const btn = document.getElementById(btnMap[fmt] || 'exportMdBtn');
  const oldText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '导出中...';
  try {
    const res = await fetch(`/api/lessons/${state.currentLessonId}/export/${fmt}`);
    if (!res.ok) {
      // 尝试解析错误信息
      let errMsg = `导出失败 (${res.status})`;
      try {
        const errData = await res.json();
        errMsg = errData.detail || errData.message || errMsg;
      } catch (_) {}
      throw new Error(errMsg);
    }
    const blob = await res.blob();
    if (blob.size === 0) throw new Error('导出内容为空');

    // 从 Content-Disposition 提取文件名（支持 filename*=UTF-8''编码格式）
    const disposition = res.headers.get('Content-Disposition') || '';
    let filename = '';
    const starMatch = disposition.match(/filename\*=UTF-8''([^;]+)/);
    if (starMatch) {
      filename = decodeURIComponent(starMatch[1]);
    } else {
      const m = disposition.match(/filename="([^"]+)"/);
      const extMap = { 'markdown': 'md', 'docx': 'docx', 'pptx': 'pptx' };
      filename = m ? m[1] : `教案.${extMap[fmt] || 'bin'}`;
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    toast(`已导出 ${filename}`);
  } catch (e) {
    toast('导出失败: ' + e.message, 3500);
    console.error('Export failed:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = oldText;
  }
}

// ==================== 教案质量评估（借鉴 instructional_agents：多指标打分 + 双视角评审） ====================
let _lastEvalReport = null; // 缓存最近一次评估报告，供复制使用

async function evaluateLesson() {
  if (!state.currentLessonId) { toast('请先生成或加载教案'); return; }
  const btn = document.getElementById('evaluateLessonBtn');
  const oldText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '评估中...';
  try {
    const data = await api(`/api/lessons/${state.currentLessonId}/evaluate`, { method: 'POST' });
    if (data.success === false) {
      // 结构化失败提示
      const errCode = data.data?.error_code || 'UNKNOWN';
      const fb = data.data?.fallbacks || [];
      appendAiMessage(`<span class="text-red-600">评估失败 [${errCode}]：</span>${escapeHtml(data.message || '')}${fb.length ? '<br><span class="text-xs text-muted">可选操作：' + fb.map((f,i)=>`<button class="underline text-teal-700" onclick="retryEvaluate()">${f}</button>`).join(' / ') + '</span>' : ''}`);
      return;
    }
    const report = data.data || {};
    _lastEvalReport = report;
    renderLessonEvaluation(report, data.message || '');
    // 同时在对话区简要提示
    const overall = typeof report.overall_score === 'number' ? report.overall_score.toFixed(2) : '-';
    appendAiMessage(`<b class="text-teal-600">教案评估完成 ✓</b> 综合得分 <b>${overall}/5.0</b>，<span class="text-xs text-muted">详细报告已弹出，含 6 维度打分与教务专家/学生代表双视角评审</span>`);
  } catch (e) {
    toast('评估失败: ' + e.message, 3500);
    console.error('Evaluate failed:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = oldText;
  }
}
function retryEvaluate() { evaluateLesson(); }

function closeLessonEvalModal() {
  const m = document.getElementById('lessonEvalModal');
  if (!m) return;
  m.classList.add('hidden');
  m.classList.remove('flex');
}

// 评分→颜色等级
function _scoreColor(score) {
  if (score >= 4.5) return '#16a34a'; // 优秀 深绿
  if (score >= 3.5) return '#0d9488'; // 良好 青绿
  if (score >= 2.5) return '#d97706'; // 合格 橙
  return '#dc2626'; // 不合格 红
}
function _scoreLabel(score) {
  if (score >= 4.5) return '优秀';
  if (score >= 3.5) return '良好';
  if (score >= 2.5) return '合格';
  return '需改进';
}
function _starLevel(level) {
  // level: 1-5
  const n = Math.max(0, Math.min(5, parseInt(level) || 0));
  return '★'.repeat(n) + '☆'.repeat(5 - n);
}

function renderLessonEvaluation(report, msg) {
  const body = document.getElementById('evalModalBody');
  const subtitle = document.getElementById('evalModalSubtitle');
  if (!body) return;

  const scores = Array.isArray(report.scores) ? report.scores : [];
  const overall = typeof report.overall_score === 'number' ? report.overall_score : 0;
  const topIssues = Array.isArray(report.top_issues) ? report.top_issues : [];
  const chair = report.chair_validation || {};
  const student = report.student_validation || {};
  const errMsg = report.error;

  subtitle.textContent = msg || `综合得分 ${overall.toFixed(2)}/5.0`;

  if (errMsg) {
    body.innerHTML = `<div class="text-center text-red-600 py-8">评估失败：${escapeHtml(errMsg)}</div>`;
    openEvalModal();
    return;
  }

  // ---- 顶部：综合得分环 ----
  const overallColor = _scoreColor(overall);
  const overallLabel = _scoreLabel(overall);
  const circumference = 2 * Math.PI * 52;
  const dashOffset = circumference * (1 - overall / 5);

  // ---- 多指标打分卡片 ----
  const scoreCards = scores.map(s => {
    const sc = typeof s.score === 'number' ? s.score : 0;
    const col = _scoreColor(sc);
    const pct = (sc / 5) * 100;
    return `
      <div class="border border-rule rounded-lg p-3 bg-white">
        <div class="flex items-center justify-between gap-2 mb-1.5">
          <div class="font-medium text-ink text-sm">${escapeHtml(s.metric || '-')}</div>
          <div class="text-sm font-bold" style="color:${col}">${sc.toFixed(1)}<span class="text-[10px] text-muted">/5.0</span></div>
        </div>
        <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div class="h-full rounded-full" style="width:${pct}%; background:${col}"></div>
        </div>
        ${s.thought ? `<div class="text-[11px] text-muted mt-1.5 leading-relaxed">${escapeHtml(s.thought)}</div>` : ''}
      </div>`;
  }).join('');

  // ---- 主要问题清单 ----
  const issuesHtml = topIssues.length
    ? topIssues.map((t, i) => `<li class="text-xs text-ink-2 leading-relaxed"><span class="text-red-500 mr-1">▸</span>${escapeHtml(t)}</li>`).join('')
    : '<li class="text-xs text-muted">未识别重大问题</li>';

  // ---- 双视角评审 ----
  function perspectiveCard(p, accentColor, title) {
    if (!p || typeof p !== 'object') return '';
    const rating = p.星级 || p.rating || p.stars || 0;
    const overall = p.总体评价 || p.overall_assessment || p.overall || '';
    const strengths = p.优点 || p.strengths || '';
    const improve = p.改进 || p.areas_for_improvement || p.improvements || '';
    const suggest = p.建议 || p.recommendations || p.suggestions || '';
    const summary = p.总结 || p.summary || '';
    function block(label, content) {
      if (!content) return '';
      const text = Array.isArray(content) ? content.map(x => `• ${escapeHtml(typeof x === 'string' ? x : JSON.stringify(x))}`).join('<br>') : escapeHtml(String(content));
      return `<div class="mb-1.5"><div class="text-[11px] font-semibold text-ink mb-0.5">${label}</div><div class="text-[11px] text-ink-2 leading-relaxed">${text}</div></div>`;
    }
    return `
      <div class="border-l-4 bg-white rounded-r-lg p-3" style="border-color:${accentColor}">
        <div class="flex items-center justify-between mb-2">
          <div class="font-semibold text-ink text-sm">${title}</div>
          ${rating ? `<div class="text-amber-500 text-sm" title="星级">${_starLevel(rating)} <span class="text-[10px] text-muted">(${rating}/5)</span></div>` : ''}
        </div>
        ${block('总体评价', overall)}
        ${block('优点', strengths)}
        ${block('待改进', improve)}
        ${block('建议', suggest)}
        ${summary ? block('总结', summary) : ''}
      </div>`;
  }

  body.innerHTML = `
    <!-- 综合得分区 -->
    <div class="flex items-center gap-6 p-4 bg-gradient-to-r from-teal-50/60 to-white rounded-lg border border-teal-100">
      <div class="relative w-32 h-32 flex-shrink-0">
        <svg class="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="52" stroke="#e5e7eb" stroke-width="8" fill="none"/>
          <circle cx="60" cy="60" r="52" stroke="${overallColor}" stroke-width="8" fill="none"
                  stroke-dasharray="${circumference}" stroke-dashoffset="${dashOffset}" stroke-linecap="round"/>
        </svg>
        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <div class="text-2xl font-bold" style="color:${overallColor}">${overall.toFixed(2)}</div>
          <div class="text-[10px] text-muted">/ 5.0</div>
          <div class="text-[11px] mt-0.5" style="color:${overallColor}">${overallLabel}</div>
        </div>
      </div>
      <div class="flex-1">
        <div class="text-sm font-semibold text-ink mb-1">综合质量评估</div>
        <div class="text-xs text-muted leading-relaxed">基于 6 维度多指标打分聚合，并经教务专家 / 学生代表双视角复核。点击下方各卡片可查看具体评议细节。</div>
        ${topIssues.length ? `<div class="mt-2 text-[11px] text-red-600">⚠ 识别到 ${topIssues.length} 项主要问题</div>` : ''}
      </div>
    </div>

    <!-- 6 维度指标打分 -->
    <div>
      <div class="text-sm font-semibold text-ink mb-2 border-l-4 border-teal-600 pl-2">📊 多维度指标打分（${scores.length} 项）</div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        ${scoreCards || '<div class="text-xs text-muted col-span-full">无打分数据</div>'}
      </div>
    </div>

    <!-- 主要问题清单 -->
    <div>
      <div class="text-sm font-semibold text-ink mb-2 border-l-4 border-red-500 pl-2">⚠ 主要问题清单</div>
      <ul class="space-y-1 pl-2">${issuesHtml}</ul>
    </div>

    <!-- 双视角评审 -->
    <div>
      <div class="text-sm font-semibold text-ink mb-2 border-l-4 border-amber-500 pl-2">👥 双视角评审</div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
        ${perspectiveCard(chair, '#0d9488', '🎓 教务专家视角') || '<div class="text-xs text-muted">无教务专家评审</div>'}
        ${perspectiveCard(student, '#7c3aed', '🎒 学生代表视角') || '<div class="text-xs text-muted">无学生代表评审</div>'}
      </div>
    </div>
  `;

  openEvalModal();
}

function openEvalModal() {
  const m = document.getElementById('lessonEvalModal');
  if (!m) return;
  m.classList.remove('hidden');
  m.classList.add('flex');
}

function copyLessonEvalReport() {
  if (!_lastEvalReport) { toast('暂无评估报告可复制'); return; }
  const r = _lastEvalReport;
  const lines = [];
  lines.push('# 教案质量评估报告');
  lines.push('');
  lines.push(`**综合得分：** ${typeof r.overall_score === 'number' ? r.overall_score.toFixed(2) : '-'} / 5.0`);
  lines.push('');
  lines.push('## 多维度指标打分');
  if (Array.isArray(r.scores) && r.scores.length) {
    lines.push('| 指标 | 得分 | 评语 |');
    lines.push('|------|------|------|');
    r.scores.forEach(s => {
      const sc = typeof s.score === 'number' ? s.score.toFixed(1) : '-';
      lines.push(`| ${s.metric || '-'} | ${sc}/5.0 | ${(s.thought || '').replace(/\|/g, '\\|')} |`);
    });
  } else { lines.push('_无打分数据_'); }
  lines.push('');
  lines.push('## 主要问题清单');
  if (Array.isArray(r.top_issues) && r.top_issues.length) {
    r.top_issues.forEach(t => lines.push(`- ${t}`));
  } else { lines.push('_未识别重大问题_'); }
  lines.push('');
  function perspectiveMd(p, title) {
    if (!p) return '';
    lines.push(`## ${title}`);
    if (p.星级 || p.rating) lines.push(`**星级：** ${_starLevel(p.星级 || p.rating)} (${p.星级 || p.rating}/5)`);
    [['总体评价','总体评价'],['overall_assessment','总体评价'],['overall','总体评价']].forEach(([k,l])=>{ if(p[k]) lines.push(`**${l}：** ${p[k]}`); });
    [['优点','优点'],['strengths','优点']].forEach(([k,l])=>{ if(p[k]) lines.push(`**${l}：** ${Array.isArray(p[k])?p[k].map(x=>'• '+x).join(' '):p[k]}`); });
    [['改进','待改进'],['areas_for_improvement','待改进'],['improvements','待改进']].forEach(([k,l])=>{ if(p[k]) lines.push(`**${l}：** ${Array.isArray(p[k])?p[k].map(x=>'• '+x).join(' '):p[k]}`); });
    [['建议','建议'],['recommendations','建议'],['suggestions','建议']].forEach(([k,l])=>{ if(p[k]) lines.push(`**${l}：** ${Array.isArray(p[k])?p[k].map(x=>'• '+x).join(' '):p[k]}`); });
    [['总结','总结'],['summary','总结']].forEach(([k,l])=>{ if(p[k]) lines.push(`**${l}：** ${p[k]}`); });
    lines.push('');
  }
  perspectiveMd(r.chair_validation, '教务专家视角');
  perspectiveMd(r.student_validation, '学生代表视角');
  if (r.error) lines.push(`\n> 评估异常：${r.error}`);
  const md = lines.join('\n');
  try {
    navigator.clipboard.writeText(md);
    toast('评估报告已复制到剪贴板');
  } catch (e) {
    // 兜底：创建 textarea 选区复制
    const ta = document.createElement('textarea');
    ta.value = md; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); toast('评估报告已复制到剪贴板'); }
    catch (_) { toast('复制失败，请手动选择'); }
    ta.remove();
  }
}

// ==================== PPT 导出设置 ====================
function openPptModal() {
  if (!state.currentLessonId) { toast('请先选择教案'); return; }
  document.getElementById('pptModal').classList.remove('hidden');
  document.getElementById('pptModal').classList.add('flex');
  document.getElementById('pptStatus').classList.add('hidden');
  document.getElementById('pptGenerateBtn').disabled = false;
  document.getElementById('pptGenerateBtn').textContent = '生成并导出';
}

function closePptModal() {
  document.getElementById('pptModal').classList.add('hidden');
  document.getElementById('pptModal').classList.remove('flex');
}

// PPT 风格选择高亮
document.querySelectorAll('#pptStyleGroup .ppt-style-option').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('#pptStyleGroup .ppt-style-option').forEach(e => {
      e.querySelector('div').className = 'border-2 border-rule rounded-lg p-2 hover:border-teal-400 transition-colors';
    });
    el.querySelector('div').className = 'border-2 border-teal-600 rounded-lg p-2';
    el.querySelector('input').checked = true;
  });
});
document.querySelectorAll('#pptDensityGroup .density-option').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('#pptDensityGroup .density-option').forEach(e => {
      e.querySelector('div').className = 'border-2 border-rule rounded-lg p-2 hover:border-teal-400 transition-colors';
    });
    el.querySelector('div').className = 'border-2 border-teal-600 rounded-lg p-2';
    el.querySelector('input').checked = true;
  });
});
document.querySelectorAll('#pptImageGroup .image-option').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('#pptImageGroup .image-option').forEach(e => {
      e.querySelector('div').className = 'border-2 border-rule rounded-lg p-2 hover:border-teal-400 transition-colors';
    });
    el.querySelector('div').className = 'border-2 border-teal-600 rounded-lg p-2';
    el.querySelector('input').checked = true;
  });
});

async function generatePpt() {
  const btn = document.getElementById('pptGenerateBtn');
  const status = document.getElementById('pptStatus');
  btn.disabled = true;
  btn.textContent = '生成中...';
  status.classList.remove('hidden');

  try {
    // 获取选中的参数
    const style = document.querySelector('input[name="pptStyle"]:checked')?.value || 'cyan_ink';
    const density = document.querySelector('input[name="pptDensity"]:checked')?.value || 'moderate';
    const imageStyle = document.querySelector('input[name="pptImage"]:checked')?.value || 'icons';
    const styleCustom = document.getElementById('pptStyleCustom').value.trim();

    const res = await fetch(`/api/lessons/${state.currentLessonId}/export-ppt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        style: style,
        content_density: density,
        image_style: imageStyle,
        style_custom: styleCustom,
      }),
    });

    if (!res.ok) {
      let errMsg = `PPT生成失败 (${res.status})`;
      try { const errData = await res.json(); errMsg = errData.detail || errData.message || errMsg; } catch (_) {}
      throw new Error(errMsg);
    }

    const blob = await res.blob();
    if (blob.size === 0) throw new Error('生成内容为空');

    // 解析文件名
    const disposition = res.headers.get('Content-Disposition') || '';
    let filename = '教学PPT.pptx';
    const starMatch = disposition.match(/filename\*=UTF-8''([^;]+)/);
    if (starMatch) {
      filename = decodeURIComponent(starMatch[1]);
    } else {
      const m = disposition.match(/filename="([^"]+)"/);
      if (m) filename = m[1];
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);

    closePptModal();
    toast(`✅ PPT已生成：${filename}`);
    // 刷新PPT记录列表
    await loadPptRecords(state.currentCourseId, state.currentChapterId, state.currentChapter);
    await refreshMindmapIfOpen();
  } catch (e) {
    toast('PPT生成失败: ' + e.message, 5000);
    console.error('PPT generation failed:', e);
    // J: 改使用 showOperationFailure
    const retryFn = () => generatePpt();
    const lowerParamsFn = () => {
      try {
        const cur = parseFloat(document.getElementById('llmTemperature').value);
        const max = parseInt(document.getElementById('llmMaxTokens').value);
        if (!isNaN(cur)) document.getElementById('llmTemperature').value = (cur / 2).toFixed(2);
        if (!isNaN(max)) document.getElementById('llmMaxTokens').value = Math.round(max * 1.5);
      } catch(_) {}
      // 同时降密度
      try {
        const mod = document.querySelector('input[name="pptDensity"][value="sparse"]');
        if (mod) mod.checked = true;
      } catch(_) {}
      generatePpt();
    };
    showOperationFailure('PPT 导出失败', e, {
      retryFn,
      lowerParamsFn,
      draftData: {
        lesson_id: state.currentLessonId,
        style: document.querySelector('input[name="pptStyle"]:checked')?.value,
        content_density: document.querySelector('input[name="pptDensity"]:checked')?.value,
        image_style: document.querySelector('input[name="pptImage"]:checked')?.value,
      },
      onHelp: openTutorial,
    });
  } finally {
    btn.disabled = false;
    btn.textContent = '生成并导出';
    status.classList.add('hidden');
  }
}

// ==================== 事件绑定 ====================
document.getElementById('newCourseBtn').onclick = () => {
  document.getElementById('courseModal').classList.remove('hidden');
  document.getElementById('courseModal').classList.add('flex');
  document.getElementById('newCourseName').focus();
};
document.getElementById('cancelCourse').onclick = () => {
  document.getElementById('courseModal').classList.add('hidden');
  document.getElementById('courseModal').classList.remove('flex');
};
document.getElementById('confirmCourse').onclick = createCourse;

// 预览标签切换绑定
document.getElementById('previewTabLesson')?.addEventListener('click', () => switchPreviewTab('lesson'));
document.getElementById('previewTabPpt')?.addEventListener('click', () => switchPreviewTab('ppt'));

// ==================== 当前课程加号按钮（新建章） ====================
document.getElementById('courseMenuBtn').onclick = () => {
  if (!state.currentCourseId) { toast('请先选择课程'); return; }
  createChapter(null, -1);
};

document.getElementById('uploadBtn').onclick = () => {
  if (!state.currentCourseId) { toast('请先选择课程'); return; }
  state.pendingFiles = [];
  document.getElementById('fileList').innerHTML = '';
  document.getElementById('confirmUpload').disabled = true;
  document.getElementById('uploadModal').classList.remove('hidden');
  document.getElementById('uploadModal').classList.add('flex');
};
document.getElementById('cancelUpload').onclick = () => {
  document.getElementById('uploadModal').classList.add('hidden');
  document.getElementById('uploadModal').classList.remove('flex');
};
document.getElementById('confirmUpload').onclick = uploadFiles;

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
dropZone.onclick = () => fileInput.click();
fileInput.onchange = (e) => {
  state.pendingFiles = Array.from(e.target.files);
  renderFileList();
};
dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('dragover'); };
dropZone.ondragleave = () => dropZone.classList.remove('dragover');
dropZone.ondrop = (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  state.pendingFiles = Array.from(e.dataTransfer.files);
  renderFileList();
};
function renderFileList() {
  const el = document.getElementById('fileList');
  el.innerHTML = state.pendingFiles.map((f, i) => `
    <div class="flex items-center justify-between text-xs bg-teal-50/50 px-2 py-1 rounded">
      <span class="truncate">${escapeHtml(f.name)}</span>
      <span class="text-muted ml-2">${formatSize(f.size)}</span>
    </div>
  `).join('');
  document.getElementById('confirmUpload').disabled = state.pendingFiles.length === 0;
}

document.getElementById('extractBtn').onclick = extractKnowledge;
document.getElementById('genLessonBtn').onclick = generateLesson;

// ③ 生成PPT按钮：直接打开PPT设置模态框
document.getElementById('genPptBtn').onclick = () => {
  if (!state.currentLessonId) { toast('请先生成教案'); return; }
  openPptModal();
};

// 思维导图（关闭/刷新按钮保留）
document.getElementById('mindmapClose').onclick = closeMindmap;
document.getElementById('mindmapRefreshBtn').onclick = generateMindmap;
document.getElementById('closeKp').onclick = () => document.getElementById('knowledgePanel').classList.add('hidden');
document.getElementById('addKpBtn').onclick = addKnowledgePoint;

// 教案参数面板控制
document.getElementById('lessonParamsBtn')?.addEventListener('click', () => {
  document.getElementById('lessonParamsPanel')?.classList.toggle('hidden');
});
document.getElementById('closeParamsBtn')?.addEventListener('click', () => {
  document.getElementById('lessonParamsPanel')?.classList.add('hidden');
});
document.getElementById('resetParamsBtn')?.addEventListener('click', resetLessonParams);

const chatInput = document.getElementById('chatInput');
chatInput.onkeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
};
document.getElementById('sendBtn').onclick = sendChat;
document.getElementById('exportMdBtn')?.addEventListener('click', () => exportLesson('markdown'));
document.getElementById('exportDocxBtn')?.addEventListener('click', () => exportLesson('docx'));
document.getElementById('evaluateLessonBtn')?.addEventListener('click', evaluateLesson);
document.getElementById('closeEvalModalBtn')?.addEventListener('click', closeLessonEvalModal);
document.getElementById('evalCopyBtn')?.addEventListener('click', copyLessonEvalReport);
document.getElementById('lessonEvalModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'lessonEvalModal') closeLessonEvalModal();
});

// PPT 导出设置
document.getElementById('pptClose').onclick = closePptModal;
document.getElementById('pptCancel').onclick = closePptModal;
document.getElementById('pptGenerateBtn').onclick = generatePpt;

// PPT 预览面板保存按钮
document.getElementById('pptSaveBtn')?.addEventListener('click', () => {
 if (_pptPanelRecordId) {
  const fakeBtn = document.createElement('div');
  fakeBtn.dataset.recordId = _pptPanelRecordId;
  savePptSlides(fakeBtn);
 }
});

document.getElementById('togglePreview').onclick = () => {
  const p = document.getElementById('previewPanel');
  const r2 = document.getElementById('resizer2');
  p.classList.toggle('hidden');
  r2.classList.toggle('hidden');
};

// ==================== 三栏拖动调整宽度（流畅版）====================
function setupResizer(resizerId, resizablePanelId, neighborPanelId, options = {}) {
  // options: { storageKey, resizeRight: false, defaultSize, minSize, maxSize }
  const resizer = document.getElementById(resizerId);
  const resizable = document.getElementById(resizablePanelId);
  const neighbor = document.getElementById(neighborPanelId);
  if (!resizer || !resizable || !neighbor) return;

  const storageKey = options.storageKey;
  const resizeRight = options.resizeRight || false;
  const defaultSize = options.defaultSize || 256;
  const minSize = options.minSize || 180;

  // 恢复保存的宽度
  if (storageKey) {
    const savedW = localStorage.getItem(storageKey);
    if (savedW) {
      const w = parseInt(savedW);
      if (!isNaN(w) && w > 100) {
        resizable.style.flex = `0 0 ${w}px`;
      }
    }
  }

  let isDragging = false;
  let startX = 0;
  let startW = 0;
  let rafId = null;
  let pendingDx = 0;
  let currentMin = minSize;
  let currentMax = options.maxSize || 9999;

  function getPanelWidth(el) {
    const style = window.getComputedStyle(el);
    const flexBasis = style.flexBasis;
    if (flexBasis && flexBasis !== 'auto' && flexBasis !== '0%' && flexBasis !== '0px') {
      return parseInt(flexBasis) || el.offsetWidth;
    }
    return el.offsetWidth;
  }

  function applyResize(dx) {
    if (rafId) return;
    pendingDx = dx;
    rafId = requestAnimationFrame(() => {
      const delta = resizeRight ? -pendingDx : pendingDx;
      const newW = Math.max(currentMin, Math.min(currentMax, startW + delta));
      resizable.style.flex = `0 0 ${newW}px`;
      rafId = null;
    });
  }

  resizer.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startW = getPanelWidth(resizable);

    // 计算约束
    const resizableStyle = window.getComputedStyle(resizable);
    const neighborStyle = window.getComputedStyle(neighbor);
    currentMin = parseInt(resizableStyle.minWidth) || minSize;
    currentMax = parseInt(resizableStyle.maxWidth) || 9999;

    const containerW = resizable.parentElement.offsetWidth - 24; // 减去两个resizer + padding
    const neighborMinW = parseInt(neighborStyle.minWidth) || 200;
    const neighborFlexGrow = parseInt(neighborStyle.flexGrow) || 0;

    if (neighborFlexGrow > 0) {
      // 邻居面板是弹性的，只需保证邻居最小宽度
      currentMax = Math.min(currentMax, containerW - neighborMinW - 50);
    } else {
      // 邻居也是固定宽度
      const neighborStartW = getPanelWidth(neighbor);
      currentMax = Math.min(currentMax, containerW - neighborMinW);
      currentMin = Math.max(currentMin, containerW - (parseInt(neighborStyle.maxWidth) || 9999));
    }

    resizer.classList.add('active');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.body.classList.add('resizing');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    applyResize(dx);
  });

  document.addEventListener('mouseup', () => {
    if (!isDragging) return;
    isDragging = false;
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    resizer.classList.remove('active');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    document.body.classList.remove('resizing');
    if (storageKey) {
      localStorage.setItem(storageKey, String(getPanelWidth(resizable)));
    }
  });

  // 双击重置
  resizer.addEventListener('dblclick', (e) => {
    e.preventDefault();
    resizable.style.flex = `0 0 ${defaultSize}px`;
    if (storageKey) {
      localStorage.setItem(storageKey, String(defaultSize));
    }
  });
}

// resizer1: 调整左栏(leftPanel)宽度，中栏弹性
setupResizer('resizer1', 'leftPanel', 'middlePanel', {
  storageKey: 'panel_left_w',
  defaultSize: 256,
  minSize: 180,
  maxSize: 500,
});
// resizer2: 调整右栏(previewPanel)宽度（拖左缩、拖右放），中栏弹性
setupResizer('resizer2', 'previewPanel', 'middlePanel', {
  storageKey: 'panel_preview_w',
  resizeRight: true,
  defaultSize: 420,
  minSize: 260,
  maxSize: 800,
});

// ==================== 左侧栏垂直拖拽调整区域高度 ====================
function setupVerticalResizer(resizerId, aboveListId, belowSectionId, options = {}) {
  // options: { storageKey, defaultAboveH, minAboveH, minBelowH, belowListId }
  // aboveListId: 上方可调整高度的列表容器（如 lessonList）
  // belowSectionId: 下方 section（用于计算最小高度约束）
  // belowListId: 下方列表容器ID，不传则自动寻找 section 内第一个 overflow-y 元素
  const resizer = document.getElementById(resizerId);
  const aboveList = document.getElementById(aboveListId);
  const belowSection = document.getElementById(belowSectionId);
  if (!resizer || !aboveList) return;

  const storageKey = options.storageKey;
  const defaultAboveH = options.defaultAboveH || 160;
  const minAboveH = options.minAboveH || 40;
  const minBelowH = options.minBelowH || 60;

  // 寻找下方列表容器
  const belowList = options.belowListId
    ? document.getElementById(options.belowListId)
    : belowSection
      ? belowSection.querySelector('.overflow-y-auto, [class*="max-h-"]') || belowSection.querySelector(':scope > div:last-child')
      : null;

  // 恢复保存的高度
  if (storageKey) {
    const savedH = localStorage.getItem(storageKey);
    if (savedH) {
      const h = parseInt(savedH);
      if (!isNaN(h) && h > 30) {
        aboveList.style.maxHeight = h + 'px';
        aboveList.style.flex = 'none';
      }
    }
  }

  let isDragging = false;
  let startY = 0;
  let startAboveH = 0;
  let startBelowH = 0;

  function getHeight(el) {
    return el.getBoundingClientRect().height;
  }

  function getSectionHeaderH(section) {
    if (!section) return 0;
    const header = section.querySelector(':scope > div:first-child');
    return header ? header.getBoundingClientRect().height : 0;
  }

  resizer.addEventListener('mousedown', (e) => {
    isDragging = true;
    startY = e.clientY;
    startAboveH = getHeight(aboveList);
    startBelowH = belowList ? getHeight(belowList) : minBelowH;

    resizer.classList.add('active');
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
    document.body.classList.add('resizing-v');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dy = e.clientY - startY;
    const aboveSection = aboveList.closest('.sidebar-section');
    const container = aboveSection ? aboveSection.parentElement : aboveList.parentElement;

    // 上方 section header 高度 + 下方 section header 高度
    const aboveHeaderH = getSectionHeaderH(aboveSection);
    const belowHeaderH = getSectionHeaderH(belowSection);

    // 计算上下列表分别的 min/max 约束
    const maxAboveH = startAboveH + startBelowH - minBelowH;
    let newAboveH = Math.max(minAboveH, Math.min(maxAboveH, startAboveH + dy));
    let newBelowH = startAboveH + startBelowH - newAboveH;

    aboveList.style.maxHeight = newAboveH + 'px';
    aboveList.style.flex = 'none';
    if (belowList && newBelowH > 0) {
      belowList.style.maxHeight = newBelowH + 'px';
      belowList.style.flex = 'none';
    }
  });

  document.addEventListener('mouseup', () => {
    if (!isDragging) return;
    isDragging = false;
    resizer.classList.remove('active');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    document.body.classList.remove('resizing-v');
    if (storageKey) {
      localStorage.setItem(storageKey, String(Math.round(getHeight(aboveList))));
    }
  });

  // 双击重置：恢复默认高度，下方列表也重置
  resizer.addEventListener('dblclick', (e) => {
    e.preventDefault();
    aboveList.style.maxHeight = defaultAboveH + 'px';
    aboveList.style.flex = 'none';
    if (belowList) {
      belowList.style.maxHeight = '';
      belowList.style.flex = '';
    }
    if (storageKey) {
      localStorage.setItem(storageKey, String(defaultAboveH));
    }
  });
}

// 初始化左侧栏垂直拖拽
// vResizer1: 章节树区域(上) vs 下方整体(下)
// 下方整体已包裹在 #belowChapters (flex-1) 中，章节树固定高度时下方自然延伸填充
(function() {
  const resizer = document.getElementById('vResizer1');
  const aboveSection = document.getElementById('chapterTreeSection');
  const belowChapters = document.getElementById('belowChapters');
  if (!resizer || !aboveSection || !belowChapters) return;

  const storageKey = 'v_resizer1_h';
  const defaultH = 220;
  const minAboveH = 80;
  // 下方最小总高度：确保下方三块内容+分隔条不被挤没
  const minBelowH = 260;

  // 恢复保存的高度
  if (storageKey) {
    const savedH = localStorage.getItem(storageKey);
    if (savedH) {
      const h = parseInt(savedH);
      if (!isNaN(h) && h > 50) {
        aboveSection.style.flex = `0 0 ${h}px`;
        aboveSection.style.minHeight = minAboveH + 'px';
      }
    }
  }

  let isDragging = false;
  let startY = 0;
  let startH = 0;

  function getHeight(el) { return el.getBoundingClientRect().height; }

  resizer.addEventListener('mousedown', (e) => {
    isDragging = true;
    startY = e.clientY;
    startH = getHeight(aboveSection);
    // 切换为固定高度（belowChapters flex-1 自然填充剩余空间）
    aboveSection.style.flex = `0 0 ${startH}px`;
    aboveSection.style.transition = 'none';

    resizer.classList.add('active');
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
    document.body.classList.add('resizing-v');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dy = e.clientY - startY;
    const parent = aboveSection.parentElement;
    const totalH = getHeight(parent);
    const resizerH = 6;

    // 允许范围：[minAboveH, 总高度 - 下方最小总高度 - 分隔条高度]
    const maxAboveH = totalH - minBelowH - resizerH;
    let newH = startH + dy;
    newH = Math.max(minAboveH, Math.min(maxAboveH, newH));

    aboveSection.style.flex = `0 0 ${newH}px`;
  });

  document.addEventListener('mouseup', () => {
    if (!isDragging) return;
    isDragging = false;
    aboveSection.style.transition = '';
    resizer.classList.remove('active');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    document.body.classList.remove('resizing-v');
    if (storageKey) {
      localStorage.setItem(storageKey, String(Math.round(getHeight(aboveSection))));
    }
  });

  // 双击重置：恢复章节树为 flex-1
  resizer.addEventListener('dblclick', (e) => {
    e.preventDefault();
    aboveSection.style.flex = '';
    aboveSection.style.maxHeight = '';
    aboveSection.style.minHeight = '';
    if (storageKey) localStorage.removeItem(storageKey);
  });
})();



// ==================== 主题切换下拉菜单 ====================
function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeUI(saved);
}

function updateThemeUI(theme) {
  const labels = {
    light: '🎨', dark: '🌙', warm: '☀️', paper: '📄', ocean: '🌊', ink: '🖋'
  };
  document.getElementById('themeIcon').textContent = labels[theme] || '🎨';
  document.querySelectorAll('.theme-option').forEach(opt => {
    const check = opt.querySelector('.theme-check');
    check.classList.toggle('hidden', opt.dataset.theme !== theme);
  });
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  updateThemeUI(theme);
  document.getElementById('themeDropdown').classList.add('hidden');
}

// 主题按钮点击切换下拉菜单
document.getElementById('themeBtn').onclick = (e) => {
  e.stopPropagation();
  const dd = document.getElementById('themeDropdown');
  dd.classList.toggle('hidden');
};

// 主题选项点击
document.querySelectorAll('.theme-option').forEach(opt => {
  opt.onclick = () => setTheme(opt.dataset.theme);
});

// 点击外部关闭下拉
document.addEventListener('click', (e) => {
  const dd = document.getElementById('themeDropdown');
  if (dd.classList.contains('hidden')) return;
  if (!e.target.closest('#themeBtn') && !e.target.closest('#themeDropdown')) {
    dd.classList.add('hidden');
  }
});

initTheme();

// ==================== 初始化 ====================
// 预加载供应商标签（避免 checkApiStatus 在 loadLlmSettings 之前调用时出错）
  fetch('/api/settings/llm').then(r => r.json()).then(d => {
    if (d.success && d.data && d.data.providers) {
      PROVIDERS_DATA = d.data.providers;
      PROVIDER_LABELS = {};
      Object.entries(PROVIDERS_DATA).forEach(([k, v]) => PROVIDER_LABELS[k] = v.label);
      updateModelBadge(d.data.current || {});
    }
  }).catch(() => {});
checkApiStatus();
loadCourses();

// ================================================================
// 追加：H 系列新增函数（不破坏已有）
// ================================================================

// ---------- 通用工具：教材类型标签映射 ----------
const MATERIAL_TYPE_META = {
  syllabus:      { label: '课程标准/大纲', cls: 'bg-purple-50 text-purple-700 border border-purple-200' },
  textbook:      { label: '教科书',       cls: 'bg-green-50 text-green-700 border border-green-200' },
  reference:     { label: '教参教辅',     cls: 'bg-blue-50 text-blue-700 border border-blue-200' },
  exercise_book: { label: '练习题册',     cls: 'bg-orange-50 text-orange-700 border border-orange-200' },
  paper:         { label: '学术论文',     cls: 'bg-pink-50 text-pink-700 border border-pink-200' },
  other:         { label: '其他',         cls: 'bg-gray-100 text-gray-700 border border-gray-200' },
};

function renderMaterialBadge(m) {
  const rawType = (m.material_type || m.type || 'other').toString().trim();
  const meta = MATERIAL_TYPE_META[rawType]
    || Object.values(MATERIAL_TYPE_META).find(x => x.label === rawType)
    || MATERIAL_TYPE_META.other;
  const label = m.material_type_label || meta.label || rawType;
  const cls = m.color_class || meta.cls;
  return `<span class="type-badge px-1.5 py-0.5 rounded border text-[10px] whitespace-nowrap ${cls}">${escapeHtml(label)}</span>`;
}

// ---------- H2: openTutorial / closeTutorial ----------
function openTutorial() {
  const m = document.getElementById('tutorialModal');
  if (!m) return;
  m.classList.remove('hidden'); m.classList.add('flex');
  try { m.scrollTop = 0; } catch(_) {}
}
function closeTutorial() {
  const m = document.getElementById('tutorialModal');
  if (!m) return;
  m.classList.add('hidden'); m.classList.remove('flex');
}
// 绑定教程按钮 + 遮罩关闭 + 关闭按钮
document.addEventListener('click', (e) => {
  const btn = e.target.closest('#tutorialBtn');
  if (btn) { openTutorial(); return; }
  const tm = document.getElementById('tutorialModal');
  if (tm) {
    if (e.target.closest('.tutorial-close') || (e.target === tm)) closeTutorial();
  }
  // 提取教材弹窗的关闭
  const em = document.getElementById('extractMaterialsModal');
  if (em) {
    if (e.target.closest('.modal-em-close') || e.target.closest('#closeExtractMatBtn') || e.target === em) {
      em.classList.add('hidden'); em.classList.remove('flex');
    }
  }
  // 模板库弹窗
  const tplm = document.getElementById('templateLibraryModal');
  if (tplm) {
    if (e.target.closest('.tpl-close') || e.target === tplm) {
      tplm.classList.add('hidden'); tplm.classList.remove('flex');
    }
  }
  // 知识图谱弹窗
  const kgm = document.getElementById('knowledgeGraphModal');
  if (kgm) {
    if (e.target.closest('.kg-close') || e.target === kgm) {
      kgm.classList.add('hidden'); kgm.classList.remove('flex');
    }
  }
});

// ---------- H6: 首次引导卡片初始化 ----------
document.addEventListener('DOMContentLoaded', () => {
  const card = document.getElementById('tutorialGuideCard');
  const shown = localStorage.getItem('tutorial_shown');
  if (card && shown !== '1') {
    card.classList.remove('hidden');
  }
  const closeBtn = document.getElementById('tutorialGuideCloseBtn');
  if (closeBtn) {
    closeBtn.onclick = () => {
      localStorage.setItem('tutorial_shown', '1');
      if (card) card.classList.add('hidden');
    };
  }

  // 知识点面板导出 XLSX
  const kpExp = document.getElementById('exportKpXlsxBtn');
  if (kpExp) {
    kpExp.onclick = async () => {
      if (!state.currentCourseId) { toast('请先选择课程'); return; }
      try {
        const btn = kpExp;
        const oldT = btn.textContent;
        btn.disabled = true; btn.textContent = '导出中...';
        try {
          const res = await fetch(`/api/courses/${state.currentCourseId}/knowledge-points/export-xlsx`, { method: 'POST' });
          if (!res.ok) {
            let msg = `导出失败 (${res.status})`;
            try { const err = await res.json(); msg = err.detail || err.message || msg; } catch(_) {}
            throw new Error(msg);
          }
          const blob = await res.blob();
          const disposition = res.headers.get('Content-Disposition') || '';
          let filename = '知识点导出.xlsx';
          const starMatch = disposition.match(/filename\*=UTF-8''([^;]+)/);
          if (starMatch) filename = decodeURIComponent(starMatch[1]);
          else { const m = disposition.match(/filename="([^"]+)"/); if (m) filename = m[1]; }
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = filename;
          document.body.appendChild(a); a.click(); a.remove();
          URL.revokeObjectURL(url);
          toast('已导出：' + filename);
        } finally {
          btn.disabled = false; btn.textContent = oldT;
        }
      } catch (e) { toast('导出失败: ' + e.message, 3500); }
    };
  }

  // ---------- 知识图谱按钮 ----------
  const kgBtn = document.getElementById('knowledgeGraphBtn');
  if (kgBtn) {
    kgBtn.onclick = () => {
      if (!state.currentCourseId) { toast('请先选择课程'); return; }
      openKnowledgeGraph();
    };
  }

  // ---------- 知识图谱导出 XLSX ----------
  const kgExpBtn = document.getElementById('kgExportXlsxBtn');
  if (kgExpBtn) {
    kgExpBtn.onclick = async () => {
      if (!state.currentCourseId) { toast('请先选择课程'); return; }
      try {
        const btn = kgExpBtn;
        const oldT = btn.textContent;
        btn.disabled = true; btn.textContent = '导出中...';
        try {
          const res = await fetch(`/api/courses/${state.currentCourseId}/knowledge-points/export-xlsx`, { method: 'POST' });
          if (!res.ok) {
            let msg = `导出失败 (${res.status})`;
            try { const err = await res.json(); msg = err.detail || err.message || msg; } catch(_) {}
            throw new Error(msg);
          }
          const blob = await res.blob();
          const disposition = res.headers.get('Content-Disposition') || '';
          let filename = '知识点导出.xlsx';
          const starMatch = disposition.match(/filename\*=UTF-8''([^;]+)/);
          if (starMatch) filename = decodeURIComponent(starMatch[1]);
          else { const m = disposition.match(/filename="([^"]+)"/); if (m) filename = m[1]; }
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = filename;
          document.body.appendChild(a); a.click(); a.remove();
          URL.revokeObjectURL(url);
          toast('已导出：' + filename);
        } finally {
          btn.disabled = false; btn.textContent = oldT;
        }
      } catch (e) { toast('导出失败: ' + e.message, 3500); }
    };
  }

  // ---------- 知识图谱刷新 ----------
  const kgRefBtn = document.getElementById('kgRefreshBtn');
  if (kgRefBtn) {
    kgRefBtn.onclick = () => {
      loadKnowledgeGraph();
    };
  }

  // ---------- smartExtractBtn 点击 打开 extractMaterialsModal ----------
  const smBtn = document.getElementById('smartExtractBtn');
  if (smBtn) {
    smBtn.onclick = () => {
      if (!state.currentCourseId) { toast('请先选择课程'); return; }
      renderMaterialsCheckList().then(() => {
        const m = document.getElementById('extractMaterialsModal');
        if (!m) return;
        m.classList.remove('hidden'); m.classList.add('flex');
        const pr = document.getElementById('extractProgress');
        if (pr) pr.classList.add('hidden');
        document.getElementById('extractProgressText').textContent = '联网校验中 ...';
        document.getElementById('extractProgressBar').style.width = '12%';
      });
    };
  }
  const selAll = document.getElementById('selAllMatBtn');
  if (selAll) selAll.onclick = () => {
    document.querySelectorAll('#materialsCheckList input[type="checkbox"].mat-cb').forEach(cb => cb.checked = true);
  };
  const unselAll = document.getElementById('unselAllMatBtn');
  if (unselAll) unselAll.onclick = () => {
    document.querySelectorAll('#materialsCheckList input[type="checkbox"].mat-cb').forEach(cb => cb.checked = false);
  };
  const confirmExtr = document.getElementById('confirmExtractMatBtn');
  if (confirmExtr) {
    confirmExtr.onclick = () => {
      const cbs = Array.from(document.querySelectorAll('#materialsCheckList input[type="checkbox"].mat-cb:checked'));
      if (cbs.length === 0) { toast('请至少选择一本教材'); return; }
      const ids = cbs.map(c => parseInt(c.value)).filter(v => !isNaN(v));
      doSmartExtract(ids);
    };
  }

  // ---------- 模板库按钮绑定 ----------
  const newTplBtn = document.getElementById('newTplBtn');
  if (newTplBtn) newTplBtn.onclick = async () => {
    const name = await showPrompt('新建模板名称', '新模板_' + Date.now());
    if (!name || !name.trim()) return;
    try { await createTemplate(name.trim()); toast('已创建模板'); } catch(e) { toast('创建失败: '+e.message); }
  };
  const uploadTplBtn = document.getElementById('uploadTplBtn');
  if (uploadTplBtn) uploadTplBtn.onclick = () => document.getElementById('uploadTplInput')?.click();
  const uploadTplInput = document.getElementById('uploadTplInput');
  if (uploadTplInput) uploadTplInput.onchange = async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    try { await uploadTemplate(f, state.currentCourseId); toast('模板导入成功，系统已自动识别Word文档内容'); }
    catch(err) { toast('导入失败: '+err.message); }
    finally { uploadTplInput.value = ''; }
  };
  const downloadTplBtn = document.getElementById('downloadTplBtn');
  if (downloadTplBtn) downloadTplBtn.onclick = () => {
    const tpl = state.templates.find(t => t.id === state.activeTemplateId);
    if (tpl) downloadTemplateDocx(tpl);
    else toast('请先选中一个模板');
  };

  // ---------- PPT模板库上传按钮绑定 ----------
  const uploadPptTemplateBtnLib = document.getElementById('uploadPptTemplateBtnLib');
  if (uploadPptTemplateBtnLib) uploadPptTemplateBtnLib.onclick = () => document.getElementById('uploadPptTemplateLibInput')?.click();
  const uploadPptTemplateLibInput = document.getElementById('uploadPptTemplateLibInput');
  if (uploadPptTemplateLibInput) uploadPptTemplateLibInput.onchange = async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    try {
      const fd = new FormData();
      fd.append('file', f);
      await api(`/api/courses/${state.currentCourseId}/ppt-templates/upload`, { method: 'POST', body: fd });
      toast('PPT模板上传成功');
      await loadPptTemplates();
    } catch(err) { toast('上传失败: ' + err.message); }
    finally { uploadPptTemplateLibInput.value = ''; }
  };

  // 失败对话框按钮一次性占位绑定（真正动作由 showOperationFailure 每次覆盖）
  document.getElementById('failRetryBtn')?.addEventListener('click', () => {
    const ctx = state.lastFailureCtx;
    if (ctx && typeof ctx.retryFn === 'function') { closeOperationFailure(); ctx.retryFn(); }
  });
  document.getElementById('failLowerBtn')?.addEventListener('click', () => {
    const ctx = state.lastFailureCtx;
    if (ctx && typeof ctx.lowerParamsFn === 'function') { closeOperationFailure(); ctx.lowerParamsFn(); }
    else toast('当前场景不支持降参');
  });
  document.getElementById('failTplBtn')?.addEventListener('click', async () => {
    const ctx = state.lastFailureCtx;
    if (ctx && typeof ctx.fallbackFn === 'function') { await ctx.fallbackFn(); return; }
    // 默认打开模板库兜底
    openTemplateLibrary();
  });
  document.getElementById('failDraftBtn')?.addEventListener('click', () => {
    const ctx = state.lastFailureCtx;
    if (!ctx || !ctx.draftData) { toast('没有可保存的草稿'); return; }
    try {
      const blob = new Blob([JSON.stringify(ctx.draftData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `draft_${ctx.title || 'failure'}_${Date.now()}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      toast('草稿已下载');
    } catch(e) { toast('保存草稿失败: '+e.message); }
  });
  document.getElementById('failHelpBtn')?.addEventListener('click', () => {
    const ctx = state.lastFailureCtx;
    closeOperationFailure();
    if (ctx && typeof ctx.onHelp === 'function') ctx.onHelp();
    else openTutorial();
  });
});

// ---------- H1: showOperationFailure ----------
function showOperationFailure(title, err, ctx = {}) {
  const m = document.getElementById('failureModal');
  if (!m) return;
  state.lastFailureCtx = { ...ctx, title: title || '操作失败' };
  const errMsg = err?.message || String(err || '未知错误');
  document.getElementById('failureMessage').textContent = (title ? `[${title}] ` : '') + errMsg;
  let code = '';
  if (err) {
    if (err.code) code += ` error_code=${err.code}`;
    if (err.status) code += ` status=${err.status}`;
    if (err.error_code) code += ` code=${err.error_code}`;
  }
  if (!code) code = 'error_code=UNKNOWN';
  document.getElementById('failureCode').textContent = code.trim();

  // 根据错误码或错误信息智能推荐解决方案
  const SOLUTION_MAP = {
    'EXTRACT_ALL_FAILED': [
      '💡 解决方案：',
      '  1️⃣ 检查网络连接是否正常',
      '  2️⃣ 检查 DeepSeek API Key 是否正确（设置 → LLM 配置）',
      '  3️⃣ 减少选择的教材数量（建议每次 ≤ 3 份）',
      '  4️⃣ 改用「章节提取」方式，逐章提取知识点',
      '  5️⃣ 若持续失败，可点击下方「降参重试」降低参数后重试',
    ],
    'PPT_LLM_AND_FALLBACK_FAILED': [
      '💡 解决方案：',
      '  1️⃣ 检查 DeepSeek API Key 是否正确',
      '  2️⃣ 减少生成内容的篇幅',
      '  3️⃣ 点击「降参重试」降低参数重试',
      '  4️⃣ 尝试先生成教案，再基于教案生成 PPT',
    ],
    'PPT_GENERATE_ERROR': [
      '💡 解决方案：',
      '  1️⃣ 检查 DeepSeek API Key 是否正确',
      '  2️⃣ 点击「重试」按钮重新生成',
      '  3️⃣ 在设置中调高 Token 上限后重试',
    ],
    'UNKNOWN': [
      '💡 解决方案：',
      '  1️⃣ 检查网络连接是否正常',
      '  2️⃣ 检查 DeepSeek API Key 配置是否正确',
      '  3️⃣ 刷新页面后重试',
      '  4️⃣ 点击下方「打开帮助」查看详细使用教程',
    ],
  };
  const matchedKey = Object.keys(SOLUTION_MAP).find(k => code.includes(k));
  const solutions = SOLUTION_MAP[matchedKey] || SOLUTION_MAP['UNKNOWN'];
  const solEl = document.getElementById('failureSolution');
  if (solEl) solEl.innerHTML = solutions.map(s => `<div class="text-[11px] leading-relaxed">${s}</div>`).join('');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeOperationFailure() {
  const m = document.getElementById('failureModal');
  if (!m) return;
  m.classList.add('hidden'); m.classList.remove('flex');
  state.lastFailureCtx = null;
}

// ---------- H3: smart-extract 相关 ----------
async function renderMaterialsCheckList() {
  const box = document.getElementById('materialsCheckList');
  if (!box) return;
  if (!state.currentCourseId) { box.innerHTML = '<div class="text-center text-muted py-4">请先选择课程</div>'; return; }
  try {
    const data = await api(`/api/courses/${state.currentCourseId}/materials`);
    const arr = data.data || [];
    if (arr.length === 0) { box.innerHTML = '<div class="text-center text-muted py-4">当前课程暂无教材，请先上传</div>'; return; }
    box.innerHTML = arr.map(m => `
      <label class="flex items-center gap-2 px-2 py-1.5 rounded-md border border-rule hover:bg-teal-50 cursor-pointer">
        <input type="checkbox" class="mat-cb w-3.5 h-3.5 accent-teal-600" value="${m.id}">
        <span class="flex-1 min-w-0 truncate text-xs text-ink">${escapeHtml(m.filename)}</span>
        ${renderMaterialBadge(m)}
      </label>
    `).join('');
  } catch (e) {
    box.innerHTML = `<div class="text-xs text-red-600 p-2">加载失败：${escapeHtml(e.message)}</div>`;
  }
}

async function doSmartExtract(materialIds) {
  if (!state.currentCourseId) { toast('请先选择课程'); return; }
  const progressEl = document.getElementById('extractProgress');
  const progressText = document.getElementById('extractProgressText');
  const progressBar = document.getElementById('extractProgressBar');
  const progressCount = document.getElementById('extractProgressCount');
  const progressPoints = document.getElementById('extractProgressPoints');
  const confirmBtn = document.getElementById('confirmExtractMatBtn');
  if (progressEl) progressEl.classList.remove('hidden');
  if (progressBar) progressBar.style.width = '0%';
  if (progressPoints) progressPoints.classList.add('hidden');
  if (confirmBtn) { confirmBtn.disabled = true; confirmBtn.textContent = '处理中...'; }

  let pollTimer = null;
  let done = false;

  const startPolling = () => {
    pollTimer = setInterval(async () => {
      if (done) return;
      try {
        const data = await api(`/api/courses/${state.currentCourseId}/extract-progress`);
        const p = data.data;
        if (p.total > 0) {
          const pct = Math.round((p.current / p.total) * 100);
          if (progressBar) progressBar.style.width = Math.min(pct, 92) + '%';
          if (progressText) progressText.textContent = `正在提取知识点（第 ${p.current}/${p.total} 段）...`;
          if (progressCount) progressCount.textContent = `(${p.points.length} 个知识点已提取)`;
          if (p.points && p.points.length > 0) {
            progressPoints.classList.remove('hidden');
            const existingList = progressPoints.querySelector('.kp-list');
            let listEl = existingList;
            if (!listEl) {
              listEl = document.createElement('div');
              listEl.className = 'kp-list space-y-0.5';
              progressPoints.appendChild(listEl);
            }
            listEl.innerHTML = p.points.map(kp =>
              `<div class="flex items-center gap-1 text-teal-700">
                <span class="w-1.5 h-1.5 rounded-full bg-teal-400 flex-shrink-0"></span>
                <span>${escapeHtml(kp.name || '')}</span>
              </div>`
            ).join('');
          }
        }
      } catch (e) {
        // 轮询失败静默处理
      }
    }, 800);
  };

  startPolling();

  try {
    const res = await api(`/api/courses/${state.currentCourseId}/smart-extract-points`, {
      method: 'POST',
      body: JSON.stringify({ material_ids: materialIds || [] }),
    });
    done = true;
    if (pollTimer) clearInterval(pollTimer);
    if (progressBar) progressBar.style.width = '100%';
    if (progressText) progressText.textContent = '提取完成 ✓';
    if (progressCount) progressCount.textContent = '';

    const kpCount = (res.data && (res.data.count || res.data.points_count))
      || (Array.isArray(res.data?.points) ? res.data.points.length : 0)
      || 0;
    toast(`✅ 一键提取完成，共 ${kpCount} 个知识点`, 3200);
    appendAiMessage(`<span class="text-teal-600 font-medium">✅ 一键提取知识点完成</span>，共提取 <b>${kpCount}</b> 个知识点。`);

    if (state.currentCourseId) {
      const localMsgs = [
        { id: Date.now(), role: 'assistant', content: `✅ 一键提取知识点完成，共提取 ${kpCount} 个知识点。`, created_at: new Date().toISOString() },
      ];
      saveChatToLocalStorage(state.currentCourseId, localMsgs);
    }

    setTimeout(() => {
      const em = document.getElementById('extractMaterialsModal');
      if (em) { em.classList.add('hidden'); em.classList.remove('flex'); }
      if (progressEl) progressEl.classList.add('hidden');
    }, 600);

    const ok = await showConfirm('导出 XLSX', `一键提取完成，共 ${kpCount} 个知识点。\n是否立即按模板导出为 XLSX？`);
    if (ok) document.getElementById('exportKpXlsxBtn')?.click();

    setTimeout(() => {
      toast('💡 可在课程菜单中查看「知识图谱」浏览知识点关系', 4000);
    }, 500);
  } catch (e) {
    done = true;
    if (pollTimer) clearInterval(pollTimer);
    appendAiMessage(`<span class="text-red-600">一键提取失败：</span>${escapeHtml(e.message)}`);
    showOperationFailure('一键提取知识点失败', e, {
      retryFn: () => doSmartExtract(materialIds),
      lowerParamsFn: () => {
        try {
          const cur = parseFloat(document.getElementById('llmTemperature').value);
          const max = parseInt(document.getElementById('llmMaxTokens').value);
          if (!isNaN(cur)) document.getElementById('llmTemperature').value = (cur / 2).toFixed(2);
          if (!isNaN(max)) document.getElementById('llmMaxTokens').value = Math.round(max * 1.5);
        } catch(_) {}
        doSmartExtract(materialIds.slice(0, Math.max(1, Math.ceil(materialIds.length / 2))));
      },
      draftData: { course_id: state.currentCourseId, material_ids: materialIds },
      onHelp: openTutorial,
    });
  } finally {
    if (pollTimer) clearInterval(pollTimer);
    if (confirmBtn) { confirmBtn.disabled = false; confirmBtn.textContent = '确定'; }
  }
}

// ---------- H4: 模板库相关 ----------
function openTemplateLibrary() {
  const m = document.getElementById('templateLibraryModal');
  if (!m) return;
  m.classList.remove('hidden'); m.classList.add('flex');
  loadTemplates();
}
function closeTemplateLibrary() {
  const m = document.getElementById('templateLibraryModal');
  if (!m) return;
  m.classList.add('hidden'); m.classList.remove('flex');
}
function switchTplTab(tab) {
  const lessonTab = document.getElementById('tplTabLesson');
  const pptTab = document.getElementById('tplTabPpt');
  const lessonContent = document.getElementById('tplLessonContent');
  const pptContent = document.getElementById('tplPptContent');
  if (tab === 'ppt') {
    lessonTab?.classList.remove('active');
    pptTab?.classList.add('active');
    pptContent?.classList.remove('tpl-hidden');
    lessonContent?.classList.add('tpl-hidden');
    loadPptTemplates();
  } else {
    pptTab?.classList.remove('active');
    lessonTab?.classList.add('active');
    lessonContent?.classList.remove('tpl-hidden');
    pptContent?.classList.add('tpl-hidden');
  }
}
document.getElementById('tplTabLesson')?.addEventListener('click', () => switchTplTab('lesson'));
document.getElementById('tplTabPpt')?.addEventListener('click', () => switchTplTab('ppt'));

async function loadTemplates() {
  if (!state.currentCourseId) return;
  try {
    const data = await api(`/api/lesson-templates?course_id=${state.currentCourseId}`);
    state.templates = Array.isArray(data.data) ? data.data : [];
    // 若无激活项则默认 is_default
    if (!state.activeTemplateId || !state.templates.some(t => t.id === state.activeTemplateId)) {
      const def = state.templates.find(t => t.is_default) || state.templates[0];
      state.activeTemplateId = def ? def.id : null;
    }
    renderTemplateList();
    renderActiveTemplateInfo();
  } catch (e) { toast('加载模板库失败: ' + e.message); }
}

async function loadPptTemplates() {
  if (!state.currentCourseId) return;
  try {
    const data = await api(`/api/courses/${state.currentCourseId}/ppt-templates`);
    state.pptTemplates = Array.isArray(data.data) ? data.data : [];
    renderPptTemplateList();
  } catch (e) { toast('加载PPT模板失败: ' + e.message); }
}

function renderPptTemplateList() {
  const el = document.getElementById('pptTemplateGroupLib');
  if (!el) return;
  if (state.pptTemplates.length === 0) {
    el.innerHTML = '<div class="text-center text-muted py-6 w-full text-xs">暂无PPT模板，点击"上传模板"</div>';
    return;
  }
  el.innerHTML = state.pptTemplates.map(t => `
    <div class="tpl-item border border-rule rounded-md p-1.5 cursor-pointer hover:bg-teal-50 text-xs min-w-[60px] text-center" data-id="${t.id}">
      <div class="truncate max-w-[80px]">${escapeHtml(t.name || '未命名')}</div>
    </div>
  `).join('');
  el.querySelectorAll('.tpl-item').forEach(it => {
    it.onclick = () => {
      const id = parseInt(it.dataset.id);
      const tpl = state.pptTemplates.find(t => t.id === id);
      if (tpl) {
        toast('已选择PPT模板: ' + (tpl.name || '未命名'));
      }
    };
  });
}

function renderTemplateList() {
  const el = document.getElementById('tplListGroup');
  if (!el) return;
  if (state.templates.length === 0) { el.innerHTML = '<div class="text-center text-muted py-6">暂无模板，点击"+新建模板"</div>'; return; }
  el.innerHTML = state.templates.map(t => {
    const activeCls = t.id === state.activeTemplateId ? 'bg-teal-100 border-teal-500' : 'bg-white border-rule';
    return `
      <div class="tpl-item border rounded-md p-2 cursor-pointer flex items-start gap-2 hover:bg-teal-50 ${activeCls}" data-id="${t.id}">
        <div class="flex-1 min-w-0" data-role="activate">
          <div class="text-xs font-medium text-ink truncate flex items-center gap-1">
            <span>#${t.id}</span>
            <span>${escapeHtml(t.name || '未命名')}</span>
            ${t.is_default ? '<span class="tag bg-amber-100 text-amber-700">⭐默认</span>' : ''}
          </div>
          <div class="text-[10px] text-muted truncate">${escapeHtml((t.description || '').toString().slice(0, 60))}</div>
        </div>
        <div class="flex items-center gap-0.5 text-xs" data-role="actions">
          <button class="tpl-act px-1 rounded hover:bg-teal-100 text-teal-700" data-act="edit" title="编辑名称">✎</button>
          <button class="tpl-act px-1 rounded hover:bg-teal-100 text-teal-700" data-act="download" title="下载Word文档">⬇</button>
          <button class="tpl-act px-1 rounded hover:bg-amber-100 text-amber-700" data-act="default" title="设为默认">★</button>
          <button class="tpl-act px-1 rounded hover:bg-red-100 text-red-600 ${t.is_default ? 'opacity-30 cursor-not-allowed' : ''}" data-act="delete" title="删除" ${t.is_default ? 'disabled' : ''}>🗑</button>
        </div>
      </div>
    `;
  }).join('');

  el.querySelectorAll('.tpl-item').forEach(it => {
    it.querySelector('[data-role="activate"]').onclick = () => {
      state.activeTemplateId = parseInt(it.dataset.id);
      renderTemplateList();
      renderActiveTemplateInfo();
    };
    it.querySelectorAll('.tpl-act').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        if (btn.hasAttribute('disabled') && btn.getAttribute('disabled') !== 'false') return;
        const act = btn.dataset.act;
        const id = parseInt(it.dataset.id);
        const tpl = state.templates.find(t => t.id === id);
        if (!tpl) return;
        try {
          if (act === 'edit') {
            const name = await showPrompt('重命名模板', tpl.name || '');
            if (name === null || !name.trim()) return;
            await api(`/api/lesson-templates/${id}`, { method: 'PUT', body: JSON.stringify({ name: name.trim() }) });
            toast('已重命名'); loadTemplates();
          } else if (act === 'download') {
            downloadTemplateDocx(tpl);
          } else if (act === 'default') {
            await setDefaultTemplate(id);
          } else if (act === 'delete') {
            if (tpl.is_default) return;
            if (!(await showConfirm('删除模板', `确认删除模板「${tpl.name}」?`))) return;
            await deleteTemplate(id);
          }
        } catch (err) { toast('操作失败: ' + err.message); }
      };
    });
  });
}

async function createTemplate(name) {
  const payload = {
    name: name || '新模板',
    course_id: state.currentCourseId || null,
    structure_json: {
      title: {},
      info_fields: ['course_name','chapter','teacher','duration','date'],
      goal_table: [],
      key_diff_table: [],
      stages: [{ name: '导入', minutes: 5, activities: [] }],
      board_design: {},
      homework: {},
      reflection: {},
    },
  };
  const data = await api('/api/lesson-templates', { method: 'POST', body: JSON.stringify(payload) });
  await loadTemplates();
  return data.data;
}

async function deleteTemplate(id) {
  await api(`/api/lesson-templates/${id}`, { method: 'DELETE' });
  toast('模板已删除');
  if (state.activeTemplateId === id) state.activeTemplateId = null;
  await loadTemplates();
}

async function setDefaultTemplate(id) {
  await api(`/api/lesson-templates/${id}/set-default`, { method: 'POST' });
  toast('已设为默认模板');
  await loadTemplates();
}

function downloadTemplateDocx(tpl) {
  // 从服务器下载 .docx 文件
  const a = document.createElement('a');
  a.href = `/api/lesson-templates/${tpl.id}/download`;
  a.download = `${(tpl.name || '教案模板').replace(/[\\/*?:"<>|]/g, '_')}.docx`;
  document.body.appendChild(a); a.click(); a.remove();
}

async function uploadTemplate(file, course_id) {
  const fd = new FormData();
  fd.append('file', file);
  if (course_id) fd.append('course_id', String(course_id));
  const data = await api('/api/lesson-templates/import', { method: 'POST', body: fd });
  await loadTemplates();
  return data.data;
}

// ==================== 知识图谱相关 ====================
function openKnowledgeGraph() {
  const m = document.getElementById('knowledgeGraphModal');
  if (!m) return;
  m.classList.remove('hidden'); m.classList.add('flex');
  loadKnowledgeGraph();
}
function closeKnowledgeGraph() {
  const m = document.getElementById('knowledgeGraphModal');
  if (!m) return;
  m.classList.add('hidden'); m.classList.remove('flex');
}

async function loadKnowledgeGraph() {
  if (!state.currentCourseId) return;
  const statsEl = document.getElementById('kgStats');
  const courseNameEl = document.getElementById('kgCourseName');
  const relationView = document.getElementById('kgRelationView');
  const tableBody = document.getElementById('kgTableBody');
  const tableCount = document.getElementById('kgTableCount');
  statsEl.textContent = '加载中...';
  try {
    const data = await api(`/api/courses/${state.currentCourseId}/knowledge-graph`);
    const graph = data.data;
    if (!graph || !graph.nodes) {
      statsEl.textContent = '暂无知识点数据';
      document.getElementById('kgEmptyHint').style.display = '';
      document.getElementById('kgCytoscape').style.display = 'none';
      tableBody.innerHTML = '';
      return;
    }
    if (courseNameEl) courseNameEl.textContent = graph.course_name || '';
    statsEl.textContent = `共 ${graph.node_count} 个知识点，${graph.edge_count} 条语义关系`;
    if (tableCount) tableCount.textContent = graph.node_count;
    renderKgRelationView(relationView, graph.nodes, graph.edges);
    renderKgTableView(tableBody, graph.nodes);
  } catch (e) {
    statsEl.textContent = '加载失败';
    document.getElementById('kgEmptyHint').textContent = `加载失败：${e.message}`;
  }
}

// Cytoscape 实例缓存
let kgCytoscapeInstance = null;

function renderKgRelationView(container, nodes, edges) {
  const cyContainer = document.getElementById('kgCytoscape');
  const emptyHint = document.getElementById('kgEmptyHint');
  if (!cyContainer || !window.cytoscape) {
    // 降级：无 Cytoscape 库时使用文本视图
    if (emptyHint) emptyHint.style.display = '';
    if (cyContainer) cyContainer.style.display = 'none';
    container.querySelector('#kgEmptyHint').textContent = '图谱库未加载，请检查网络';
    return;
  }
  if ((!nodes || nodes.length === 0) && (!edges || edges.length === 0)) {
    if (emptyHint) { emptyHint.style.display = ''; emptyHint.textContent = '暂无知识点数据'; }
    cyContainer.style.display = 'none';
    return;
  }
  if (emptyHint) emptyHint.style.display = 'none';
  cyContainer.style.display = '';

  // 构造 Cytoscape 元素
  const cyElements = [];
  const nodeMap = {};
  nodes.forEach(n => {
    nodeMap[n.name] = true;
    // 根据层级和标签决定节点类型
    let nodeType = n.layer || 'core';
    let tagFlags = [];
    if (n.is_key_point) tagFlags.push('key');
    if (n.is_difficult) tagFlags.push('diff');
    if (n.is_exam_point) tagFlags.push('exam');
    cyElements.push({
      data: {
        id: n.name,
        label: n.name,
        layer: nodeType,
        tags: tagFlags.join(','),
        definition: n.definition || '',
        prerequisites: (n.prerequisites || []).join('、')
      }
    });
  });
  (edges || []).forEach(e => {
    if (nodeMap[e.source] && nodeMap[e.target]) {
      cyElements.push({
        data: {
          source: e.source,
          target: e.target,
          relType: e.rel_type || 'prerequisite',
          label: e.label || '前置依赖'
        }
      });
    }
  });

  // 销毁旧实例
  if (kgCytoscapeInstance) {
    kgCytoscapeInstance.destroy();
    kgCytoscapeInstance = null;
  }

  // 青绿水墨配色 (与项目主题一致)
  kgCytoscapeInstance = cytoscape({
    container: cyContainer,
    elements: cyElements,
    minZoom: 0.3,
    maxZoom: 3,
    layout: {
      name: 'breadthfirst',
      directed: true,
      spacingFactor: 1.5,
      padding: 30,
      circle: false,
      animate: true,
      animationDuration: 300
    },
    style: [
      { selector: 'core', style: {
        'background-color': '#f0f7f5',
        'background-image': 'linear-gradient(#d9ebe6 1px, transparent 1px), linear-gradient(90deg, #d9ebe6 1px, transparent 1px)',
        'background-size': '25px 25px'
      }},
      { selector: 'edge', style: {
        'width': 2,
        'line-color': '#7fbab0',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#4a9d8f',
        'curve-style': 'bezier',
        'arrow-scale': 1.2,
        'label': 'data(label)',
        'font-size': '9px',
        'color': '#4a9d8f',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.8,
        'text-background-padding': '2px',
        'text-rotation': 'autorotate',
        'text-margin-y': '-6px',
        'font-family': 'Noto Sans SC, Arial, sans-serif'
      }},
      // 关系类型配色
      { selector: 'edge[relType="prerequisite"]', style: { 'line-color': '#4a9d8f', 'target-arrow-color': '#4a9d8f', 'color': '#4a9d8f' }},
      { selector: 'edge[relType="支撑"]', style: { 'line-color': '#2196F3', 'target-arrow-color': '#2196F3', 'color': '#2196F3', 'line-style': 'dashed' }},
      { selector: 'edge[relType="组成"]', style: { 'line-color': '#FF9800', 'target-arrow-color': '#FF9800', 'color': '#FF9800', 'line-style': 'dotted' }},
      { selector: 'edge[relType="对比"]', style: { 'line-color': '#9C27B0', 'target-arrow-color': '#9C27B0', 'color': '#9C27B0', 'line-style': 'dashed' }},
      { selector: 'edge[relType="应用"]', style: { 'line-color': '#F44336', 'target-arrow-color': '#F44336', 'color': '#F44336', 'line-style': 'dotted' }},
      // 基础层 (青绿淡色)
      { selector: 'node[layer="basic"]', style: {
        'background-color': '#7fbab0',
        'shape': 'round-rectangle',
        'font-size': '11px',
        'padding': '8px'
      }},
      // 核心层 (青绿主色)
      { selector: 'node[layer="core"]', style: {
        'background-color': '#2e7d6e',
        'shape': 'round-rectangle',
        'font-size': '12px',
        'padding': '10px'
      }},
      // 拓展层 (墨色)
      { selector: 'node[layer="extension"]', style: {
        'background-color': '#5a4030',
        'shape': 'round-rectangle',
        'font-size': '11px',
        'padding': '8px'
      }},
      // 标记为重点的节点加金色边框
      { selector: 'node[tags*="key"]', style: {
        'border-width': 3,
        'border-color': '#d4a017',
        'border-style': 'solid'
      }},
      // 标记为难点的节点加红色边框
      { selector: 'node[tags*="diff"]', style: {
        'border-width': 3,
        'border-color': '#c0392b',
        'border-style': 'dashed'
      }},
      // 标记为考点的节点加紫色边框
      { selector: 'node[tags*="exam"]', style: {
        'border-width': 3,
        'border-color': '#8e44ad',
        'border-style': 'double'
      }},
      // 通用节点样式
      { selector: 'node', style: {
        'label': 'data(label)',
        'color': '#ffffff',
        'text-wrap': 'wrap',
        'text-max-width': '90px',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-family': 'Noto Sans SC, Arial, sans-serif',
        'font-weight': '600',
        'width': 'label',
        'height': 'label',
        'border-width': 1,
        'border-color': '#b3d7cd'
      }},
      // 选中节点高亮
      { selector: 'node:selected', style: {
        'background-color': '#236658',
        'border-width': 4,
        'border-color': '#d4a017'
      }}
    ],
    wheelSensitivity: 0.2
  });

  // 点击节点显示详情
  kgCytoscapeInstance.on('tap', 'node', function(evt) {
    const node = evt.target;
    const def = node.data('definition');
    const prereq = node.data('prerequisites');
    const tags = node.data('tags');
    let tagText = '';
    if (tags) {
      const tagArr = tags.split(',').filter(Boolean);
      const tagMap = { key: '重点', diff: '难点', exam: '考点' };
      tagText = tagArr.map(t => tagMap[t] || t).join('、');
    }
    const layer = node.data('layer');
    const layerMap = { basic: '基础', core: '核心', extension: '拓展' };
    const layerText = layerMap[layer] || layer;
    const info = `【${node.data('label')}】 层级：${layerText}${tagText ? ' | 标签：' + tagText : ''}${prereq ? ' | 前置：' + prereq : ''}${def ? '\n' + def : ''}`;
    toast(info, 5000);
  });

  // 绑定缩放控件
  bindKgZoomControls();
  updateKgZoomIndicator();
}

function bindKgZoomControls() {
  const zoomIn = document.getElementById('kgZoomIn');
  const zoomOut = document.getElementById('kgZoomOut');
  const fitBtn = document.getElementById('kgFit');
  if (zoomIn) zoomIn.onclick = () => { if (kgCytoscapeInstance) kgCytoscapeInstance.zoom({ level: kgCytoscapeInstance.zoom() * 1.2, renderedPosition: { x: kgCytoscapeInstance.width()/2, y: kgCytoscapeInstance.height()/2 } }); updateKgZoomIndicator(); };
  if (zoomOut) zoomOut.onclick = () => { if (kgCytoscapeInstance) kgCytoscapeInstance.zoom({ level: kgCytoscapeInstance.zoom() / 1.2, renderedPosition: { x: kgCytoscapeInstance.width()/2, y: kgCytoscapeInstance.height()/2 } }); updateKgZoomIndicator(); };
  if (fitBtn) fitBtn.onclick = () => { if (kgCytoscapeInstance) kgCytoscapeInstance.fit(undefined, 30); updateKgZoomIndicator(); };
  if (kgCytoscapeInstance) kgCytoscapeInstance.on('zoom pan', updateKgZoomIndicator);
}

function updateKgZoomIndicator() {
  const ind = document.getElementById('kgZoomIndicator');
  if (ind && kgCytoscapeInstance) ind.textContent = Math.round(kgCytoscapeInstance.zoom() * 100) + '%';
}

function renderKgTableView(tableBody, nodes) {
  if (!nodes || nodes.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">暂无知识点</td></tr>';
    return;
  }
  let html = '';
  nodes.forEach((node, i) => {
    const layerLabel = node.layer === 'basic' ? '基础' : (node.layer === 'core' ? '核心' : '拓展');
    const tags = [];
    if (node.is_key_point) tags.push('重点');
    if (node.is_difficult) tags.push('难点');
    if (node.is_exam_point) tags.push('考点');
    const tagStr = tags.length ? tags.join('、') : '—';
    const prereqStr = (node.prerequisites && node.prerequisites.length)
      ? node.prerequisites.join('、') : '—';
    html += `<tr class="${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} border-t border-rule hover:bg-teal-50/50">
      <td class="px-2 py-1.5 border-r text-muted">${i + 1}</td>
      <td class="px-2 py-1.5 border-r font-medium text-ink">${escapeHtml(node.name || '')}</td>
      <td class="px-2 py-1.5 border-r">
        <span class="tag ${node.layer === 'basic' ? 'tag-basic' : (node.layer === 'core' ? 'tag-core' : 'tag-ext')}">${layerLabel}</span>
      </td>
      <td class="px-2 py-1.5 border-r">
        ${tags.length ? tags.map(t => `<span class="tag ${t === '重点' ? 'tag-key' : (t === '难点' ? 'tag-diff' : 'tag-exam')}">${t}</span>`).join(' ') : '<span class="text-muted">—</span>'}
      </td>
      <td class="px-2 py-1.5 border-r text-muted text-[10px]">${escapeHtml(prereqStr)}</td>
      <td class="px-2 py-1.5 text-muted text-[10px] leading-snug max-w-xs truncate">${escapeHtml((node.definition || '').slice(0, 120))}</td>
    </tr>`;
  });
  tableBody.innerHTML = html;
}

// ==================== 模板就地编辑 ====================
let _templateEditState = { editing: false, originalJson: null };

function renderActiveTemplateInfo() {
  const nameEl = document.getElementById('activeTplName');
  const card = document.getElementById('tplInfoCard');
  if (!card) return;
  const tpl = state.templates.find(t => t.id === state.activeTemplateId);
  if (!tpl) {
    if (nameEl) nameEl.textContent = '未选择';
    card.innerHTML = '<div class="text-center text-muted py-8">请在左侧选择一个模板查看详情</div>';
    return;
  }
  if (_templateEditState.editing) {
    renderTemplateEditor(card, tpl);
    return;
  }
  if (nameEl) nameEl.textContent = `${tpl.name || '未命名'}${tpl.is_default ? ' ⭐默认' : ''}`;
  const sj = tpl.structure_json || tpl.structure || tpl.json || {};
  const defaults = sj.defaults || sj;
  let infoHtml = `<div class="space-y-2">`;
  infoHtml += `<div class="font-medium text-teal-700 border-b pb-1 mb-1">基本信息</div>`;
  infoHtml += `<div class="grid grid-cols-2 gap-1 text-[10px]">`;
  if (defaults.course_name) infoHtml += `<div><span class="text-muted">课程名称：</span>${escapeHtml(defaults.course_name)}</div>`;
  if (defaults.chapter) infoHtml += `<div><span class="text-muted">章节：</span>${escapeHtml(defaults.chapter)}</div>`;
  infoHtml += `<div><span class="text-muted">总课时：</span>${defaults.total_minutes || 90} 分钟</div>`;
  infoHtml += `</div>`;
  if (defaults.knowledge_goal || defaults.ability_goal || defaults.value_goal) {
    infoHtml += `<div class="font-medium text-teal-700 border-b pb-1 mt-2 mb-1">教学目标</div>`;
    if (defaults.knowledge_goal) infoHtml += `<div class="text-[10px]"><span class="text-muted">知识目标：</span>${escapeHtml(String(defaults.knowledge_goal).slice(0, 80))}</div>`;
    if (defaults.ability_goal) infoHtml += `<div class="text-[10px]"><span class="text-muted">能力目标：</span>${escapeHtml(String(defaults.ability_goal).slice(0, 80))}</div>`;
    if (defaults.value_goal) infoHtml += `<div class="text-[10px]"><span class="text-muted">素质目标：</span>${escapeHtml(String(defaults.value_goal).slice(0, 80))}</div>`;
  }
  const kp = defaults.key_points || [];
  const dp = defaults.difficult_points || [];
  if (kp.length || dp.length) {
    infoHtml += `<div class="font-medium text-teal-700 border-b pb-1 mt-2 mb-1">教学重难点</div>`;
    if (kp.length) infoHtml += `<div class="text-[10px]"><span class="text-muted">重点：</span>${kp.length} 个</div>`;
    if (dp.length) infoHtml += `<div class="text-[10px]"><span class="text-muted">难点：</span>${dp.length} 个</div>`;
  }
  const stages = defaults.stages || [];
  infoHtml += `<div class="font-medium text-teal-700 border-b pb-1 mt-2 mb-1">教学过程</div>`;
  if (stages.length) {
    infoHtml += `<div class="text-[10px]">共 ${stages.length} 个阶段：</div>`;
    infoHtml += `<ul class="list-disc list-inside text-[10px] text-muted">`;
    stages.forEach(s => {
      infoHtml += `<li>${escapeHtml(s.name || '')}（${s.duration_min || 10}分钟）</li>`;
    });
    infoHtml += `</ul>`;
  } else {
    infoHtml += `<div class="text-[10px] text-muted">（未设置）</div>`;
  }
  infoHtml += `<div class="font-medium text-teal-700 border-b pb-1 mt-2 mb-1">其他</div>`;
  infoHtml += `<div class="text-[10px]">`;
  infoHtml += `<div><span class="text-muted">板书设计：</span>${defaults.board_design ? '✓ 已设置' : '—'}</div>`;
  const hw = defaults.homework || [];
  infoHtml += `<div><span class="text-muted">课后作业：</span>${hw.length ? hw.length + ' 项' : '—'}</div>`;
  infoHtml += `<div><span class="text-muted">教学反思：</span>${defaults.reflection ? '✓ 已设置' : '—'}</div>`;
  infoHtml += `</div>`;
  infoHtml += `</div>`;
  infoHtml += `<div class="mt-3 flex justify-end gap-2 pt-2 border-t border-rule">`;
  infoHtml += `<button id="editTplContentBtn" class="btn-ghost px-2 py-1 rounded text-[11px]">✏ 编辑内容</button>`;
  infoHtml += `</div>`;
  card.innerHTML = infoHtml;
  setTimeout(() => {
    const editBtn = document.getElementById('editTplContentBtn');
    if (editBtn) {
      editBtn.onclick = () => {
        _templateEditState.editing = true;
        _templateEditState.originalJson = JSON.parse(JSON.stringify(tpl.structure_json || {}));
        renderActiveTemplateInfo();
      };
    }
  }, 0);
}

function renderTemplateEditor(card, tpl) {
  card.innerHTML = `
    <div class="space-y-2">
      <div class="font-medium text-teal-700 border-b pb-1 mb-1">编辑模板内容（Word）</div>
      <div class="text-[10px] text-muted mb-1">通过 Word 文档编辑模板，无需处理 JSON</div>
      <div class="flex flex-col gap-2 py-2">
        <button id="tplDownloadWordBtn" class="btn-primary px-3 py-2 rounded text-xs">⬇ 下载模板Word文档</button>
        <div class="flex items-center gap-2 text-muted text-[10px]">
          <span class="flex-1 border-t border-rule"></span>
          <span>或</span>
          <span class="flex-1 border-t border-rule"></span>
        </div>
        <button id="tplUploadWordBtn" class="btn-ghost px-3 py-2 rounded text-xs">📄 上传已编辑的Word文档</button>
        <input id="tplUploadWordInput" type="file" accept=".docx" class="hidden">
      </div>
      <div id="tplWordEditStatus" class="text-[10px] text-muted text-center"></div>
      <div class="flex justify-end gap-2 pt-1">
        <button id="tplEditorCancelBtn" class="btn-ghost px-2 py-1 rounded text-[11px]">取消</button>
      </div>
    </div>
  `;
  setTimeout(() => {
    document.getElementById('tplDownloadWordBtn').onclick = () => {
      downloadTemplateDocx(tpl);
      document.getElementById('tplWordEditStatus').textContent = '✅ 已下载，请在 Word 中编辑后上传';
    };
    document.getElementById('tplUploadWordBtn').onclick = () => {
      document.getElementById('tplUploadWordInput').click();
    };
    document.getElementById('tplUploadWordInput').onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      await uploadEditedTemplate(tpl, file);
      e.target.value = '';
    };
    document.getElementById('tplEditorCancelBtn').onclick = () => {
      _templateEditState.editing = false;
      _templateEditState.originalJson = null;
      renderActiveTemplateInfo();
    };
  }, 0);
}

async function uploadEditedTemplate(tpl, file) {
  const statusEl = document.getElementById('tplWordEditStatus');
  try {
    statusEl.textContent = '⏳ 上传解析中...';
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`/api/lesson-templates/${tpl.id}/upload-docx`, {
      method: 'PUT',
      body: formData,
    });
    if (!res.ok) {
      let msg = '上传失败';
      try { const err = await res.json(); msg = err.detail || err.message || msg; } catch(_) {}
      throw new Error(msg);
    }
    statusEl.textContent = '✅ 模板已从 Word 文档更新';
    toast('模板已从 Word 文档更新');
    _templateEditState.editing = false;
    _templateEditState.originalJson = null;
    await loadTemplates();
  } catch (e) {
    statusEl.textContent = '❌ ' + e.message;
    toast('上传失败: ' + e.message, 3500);
  }
}

// ==================== F1: 教案全屏预览 + in-place 编辑 ====================
const _fullscreenLessonState = {
  plan: null,           // 当前全屏渲染的 plan_json
  editMode: false,      // 是否处于编辑模式
  dirty: false,         // 是否有未保存的修改
};

function _setFullscreenDirty(v) {
  _fullscreenLessonState.dirty = !!v;
  const bar = document.getElementById('fullscreenDirtyBar');
  if (bar) bar.classList.toggle('hidden', !_fullscreenLessonState.dirty);
}

// 渲染预览模式（独立渲染，避免污染右栏 previewContent）
function _renderFullscreenPreview() {
  const body = document.getElementById('fullscreenLessonBody');
  const plan = _fullscreenLessonState.plan;
  if (!plan) {
    body.innerHTML = '<div class="text-center text-muted py-10">教案为空</div>';
    return;
  }
  _renderLessonPlanInto(body, plan);
  // 若处于编辑模式，重新开启 contenteditable
  if (_fullscreenLessonState.editMode) _enableContenteditable();
}

// 将 plan_json 渲染为目标容器 innerHTML（独立实现，避免污染右栏）
function _renderLessonPlanInto(target, plan) {
  if (!plan) { target.innerHTML = '<div class="text-center text-muted py-10">教案为空</div>'; return; }
  const titleTable = `
    <table class="title-table">
      <tr><td colspan="2"><h1 data-field="title" data-path="course_name" class="editable-field">${escapeHtml(plan.course_name || '')} · ${escapeHtml(plan.chapter || '')} 教案</h1></td></tr>
      <tr><td colspan="2" style="font-size:0.75rem;color:#8a7968;font-style:italic" data-field="meta" data-path="total_minutes">总课时：${escapeHtml(String(plan.total_minutes ?? ''))} 分钟</td></tr>
    </table>
  `;
  const infoRows = [];
  infoRows.push(`<tr><td>课程名称</td><td data-field="info" data-path="course_name" class="editable-field">${escapeHtml(plan.course_name || '')}</td></tr>`);
  infoRows.push(`<tr><td>授课章节</td><td data-field="info" data-path="chapter" class="editable-field">${escapeHtml(plan.chapter || '')}</td></tr>`);
  if (plan.teaching_object) infoRows.push(`<tr><td>授课对象</td><td>${escapeHtml(plan.teaching_object)}</td></tr>`);
  if (plan.teacher_name) infoRows.push(`<tr><td>授课教师</td><td>${escapeHtml(plan.teacher_name)}</td></tr>`);
  infoRows.push(`<tr><td>课时安排</td><td data-field="info" data-path="total_minutes" class="editable-field">${escapeHtml(String(plan.total_minutes ?? ''))} 分钟</td></tr>`);
  const infoTable = `<table class="info-table"><tbody>${infoRows.join('')}</tbody></table>`;

  const goalRows = [];
  if (plan.knowledge_goal !== undefined) goalRows.push(`<tr><td class="goal-knowledge">知识目标</td><td data-field="goal" data-path="knowledge_goal" class="editable-field">${escapeHtml(plan.knowledge_goal || '')}</td></tr>`);
  if (plan.ability_goal !== undefined) goalRows.push(`<tr><td class="goal-ability">能力目标</td><td data-field="goal" data-path="ability_goal" class="editable-field">${escapeHtml(plan.ability_goal || '')}</td></tr>`);
  if (plan.value_goal !== undefined) goalRows.push(`<tr><td class="goal-value">素质/思政目标</td><td data-field="goal" data-path="value_goal" class="editable-field">${escapeHtml(plan.value_goal || '')}</td></tr>`);
  // teaching_objectives 整体（若存在）
  if (plan.teaching_objectives !== undefined && !goalRows.length) {
    goalRows.push(`<tr><td class="goal-knowledge">教学目标</td><td data-field="goal" data-path="teaching_objectives" class="editable-field">${escapeHtml(plan.teaching_objectives || '')}</td></tr>`);
  }
  const goalTable = `<table class="goal-table"><tbody>${goalRows.join('')}</tbody></table>`;

  const keyDiffRows = [];
  if ((plan.key_points || []).length > 0) {
    keyDiffRows.push(`<tr><td class="td-key">教学重点</td><td><ul>${(plan.key_points || []).map((k, i) => `<li data-field="key_points" data-path="key_points.${i}" class="editable-field">${escapeHtml(k)}</li>`).join('')}</ul></td></tr>`);
  }
  if ((plan.difficult_points || []).length > 0) {
    keyDiffRows.push(`<tr><td class="td-diff">教学难点</td><td><ul>${(plan.difficult_points || []).map((d, i) => `<li data-field="difficult_points" data-path="difficult_points.${i}" class="editable-field">${escapeHtml(d)}</li>`).join('')}</ul></td></tr>`);
  }
  if (plan.difficult_strategy) {
    keyDiffRows.push(`<tr><td style="background:rgba(46,125,110,0.08);color:#2e7d6e">突破策略</td><td data-field="difficult_strategy" data-path="difficult_strategy" class="editable-field">${escapeHtml(plan.difficult_strategy)}</td></tr>`);
  }
  const keyDiffTable = keyDiffRows.length ? `<table class="key-diff-table"><tbody>${keyDiffRows.join('')}</tbody></table>` : '';

  const stagesTable = (() => {
    if (!plan.stages || plan.stages.length === 0) {
      return '<table class="stages-table"><tr><td colspan="5" style="text-align:center;color:#8a7968">暂无教学过程</td></tr></table>';
    }
    const rows = plan.stages.map((s, i) => `
      <tr>
        <td class="stage-name">
          <div data-field="stages" data-path="stages.${i}.name" class="editable-field">${escapeHtml(s.name || '')}</div>
          <span class="text-muted text-[10px]"><span data-field="stages" data-path="stages.${i}.duration_min" class="editable-field">${escapeHtml(String(s.duration_min ?? ''))}</span>分钟</span>
        </td>
        <td data-field="stages" data-path="stages.${i}.teacher_activity" class="editable-field">${escapeHtml(s.teacher_activity || '')}</td>
        <td data-field="stages" data-path="stages.${i}.student_activity" class="editable-field">${escapeHtml(s.student_activity || '')}</td>
        <td data-field="stages" data-path="stages.${i}.design_intent" class="editable-field">${escapeHtml(s.design_intent || '')}</td>
        <td data-field="stages" data-path="stages.${i}.content" class="editable-field">${s.content ? escapeHtml(s.content) : '<span class="text-muted">-</span>'}</td>
      </tr>
    `).join('');
    return `
      <table class="stages-table">
        <thead>
          <tr>
            <th>阶段/时长</th><th>教师行为</th><th>学生行为</th><th>设计意图</th><th>教学内容</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  })();

  const boardTable = plan.board_design !== undefined && plan.board_design !== null && plan.board_design !== '' ? `
    <table class="board-table">
      <tr><td>板书设计</td><td data-field="board_design" data-path="board_design" class="editable-field" style="font-family:monospace;font-size:0.8rem;white-space:pre-wrap">${escapeHtml(plan.board_design)}</td></tr>
    </table>
  ` : '';

  const hwRows = (plan.homework || []).map((h, i) => `<tr><td>${i+1}</td><td data-field="homework" data-path="homework.${i}" class="editable-field">${escapeHtml(h)}</td></tr>`).join('');
  const homeworkTable = hwRows ? `<table class="homework-table"><tbody>${hwRows}</tbody></table>` : '';

  const reflectionTable = `
    <table class="reflection-table">
      <tr><td style="width:80px;background:rgba(46,125,110,0.06);font-weight:500">教学反思</td><td data-field="reflection" data-path="reflection" class="editable-field">${escapeHtml(plan.reflection || '（课后填写）')}</td></tr>
    </table>
  `;

  const nums = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  let n = 4;
  target.innerHTML = `
    ${titleTable}
    <h2>一、教学基本信息</h2>${infoTable}
    <h2>二、教学目标</h2>${goalTable}
    <h2>三、教学重难点</h2>${keyDiffTable || '<table><tr><td colspan="2" style="text-align:center;color:#8a7968">暂无</td></tr></table>'}
    <h2>${nums[n++]}、教学过程设计</h2>${stagesTable}
    ${boardTable ? `<h2>${nums[n++]}、板书设计</h2>${boardTable}` : ''}
    ${homeworkTable ? `<h2>${nums[n++]}、课后作业</h2>${homeworkTable}` : ''}
    <h2>${nums[n]}、教学反思</h2>${reflectionTable}
  `;
  target.scrollTop = 0;
}

// 打开全屏教案 modal
async function openFullscreenLesson() {
  if (!state.currentLessonId) {
    toast('请先生成或选择教案');
    return;
  }
  try {
    const data = await api(`/api/lessons/${state.currentLessonId}`);
    const plan = data.data?.plan_json || data.data?.plan || data.data || null;
    if (!plan) { toast('未获取到教案数据'); return; }
    _fullscreenLessonState.plan = plan;
    _fullscreenLessonState.editMode = false;
    _setFullscreenDirty(false);
    _updateToggleEditBtn();
    _renderFullscreenPreview();
    const subtitle = document.getElementById('fullscreenLessonSubtitle');
    if (subtitle) subtitle.textContent = `· ${plan.course_name || ''} / ${plan.chapter || ''}`;
    const modal = document.getElementById('fullscreenLessonModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  } catch (e) {
    toast('打开全屏教案失败: ' + e.message);
  }
}

function closeFullscreenLesson() {
  const modal = document.getElementById('fullscreenLessonModal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  _fullscreenLessonState.plan = null;
  _fullscreenLessonState.editMode = false;
  _setFullscreenDirty(false);
}

// 更新编辑/预览切换按钮显示
function _updateToggleEditBtn() {
  const btn = document.getElementById('toggleEditBtn');
  if (!btn) return;
  const icon = btn.querySelector('.edit-icon');
  const label = btn.querySelector('.edit-label');
  if (_fullscreenLessonState.editMode) {
    if (icon) icon.textContent = '👁';
    if (label) label.textContent = '预览';
    btn.classList.remove('btn-ghost'); btn.classList.add('btn-primary');
  } else {
    if (icon) icon.textContent = '✏️';
    if (label) label.textContent = '编辑';
    btn.classList.add('btn-ghost'); btn.classList.remove('btn-primary');
  }
}

// 切换编辑/预览模式（保留未保存的修改：每次切换都同步到 _fullscreenLessonState.plan）
function toggleLessonEditMode() {
  if (_fullscreenLessonState.editMode) {
    // 编辑 -> 预览：先收集当前编辑结果到 plan，再重新渲染（保留修改）
    const collected = collectEditedPlan();
    if (collected) _fullscreenLessonState.plan = collected;
    _fullscreenLessonState.editMode = false;
    _updateToggleEditBtn();
    _renderFullscreenPreview();
  } else {
    // 预览 -> 编辑：渲染后开启 contenteditable
    _fullscreenLessonState.editMode = true;
    _updateToggleEditBtn();
    _renderFullscreenPreview();
    _enableContenteditable();
  }
}

// 给所有 .editable-field 元素加 contenteditable 与 hover 提示
function _enableContenteditable() {
  const body = document.getElementById('fullscreenLessonBody');
  body.querySelectorAll('.editable-field').forEach(el => {
    el.setAttribute('contenteditable', 'true');
    el.classList.add('editable-active');
    el.addEventListener('input', () => _setFullscreenDirty(true));
  });
}

// 收集所有 [data-field][data-path] 的 contenteditable 文本，按 path 组装回 plan_json
function collectEditedPlan() {
  const body = document.getElementById('fullscreenLessonBody');
  if (!body) return null;
  const plan = JSON.parse(JSON.stringify(_fullscreenLessonState.plan || {}));
  body.querySelectorAll('[data-path]').forEach(el => {
    const path = el.dataset.path;
    if (!path) return;
    const text = el.textContent;
    setByPath(plan, path, text);
  });
  return plan;
}

// 按 "stages.0.name" 形式的 path 写值（自动类型推断：数字字符串转 number）
function setByPath(obj, path, value) {
  const parts = path.split('.');
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    const nextK = parts[i+1];
    const idx = Number(k);
    if (!isNaN(idx) && Array.isArray(cur)) {
      if (!cur[idx]) cur[idx] = isNaN(Number(nextK)) ? {} : [];
      cur = cur[idx];
    } else if (!isNaN(idx)) {
      if (!cur[k]) cur[k] = [];
      cur = cur[k];
    } else {
      if (!cur[k]) cur[k] = isNaN(Number(nextK)) ? {} : [];
      cur = cur[k];
    }
  }
  const last = parts[parts.length - 1];
  const lastIdx = Number(last);
  let v = value;
  // 数值字段转 number
  if (last === 'duration_min' || last === 'total_minutes') {
    const n = Number(value);
    v = isNaN(n) ? value : n;
  }
  if (!isNaN(lastIdx) && Array.isArray(cur)) {
    cur[lastIdx] = v;
  } else {
    cur[last] = v;
  }
}

// 保存编辑后的教案
async function saveEditedLesson() {
  if (!state.currentLessonId) { toast('未选择教案'); return; }
  const saveBtn = document.getElementById('saveLessonBtn');
  const oldText = saveBtn ? saveBtn.textContent : '';
  try {
    if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = '保存中...'; }
    // 收集编辑结果（即使在预览模式，也用上次同步过的 plan）
    const newPlan = _fullscreenLessonState.editMode ? collectEditedPlan() : _fullscreenLessonState.plan;
    if (!newPlan) { toast('没有可保存的数据'); return; }
    await api(`/api/lessons/${state.currentLessonId}`, {
      method: 'PUT',
      body: JSON.stringify(newPlan),
    });
    _fullscreenLessonState.plan = newPlan;
    _setFullscreenDirty(false);
    toast('教案已保存');
    // 同步刷新右栏预览
    try { renderLessonPreview(newPlan); } catch(_) {}
    // 切回预览模式（若在编辑模式）
    if (_fullscreenLessonState.editMode) {
      _fullscreenLessonState.editMode = false;
      _updateToggleEditBtn();
      _renderFullscreenPreview();
    }
  } catch (e) {
    toast('保存失败: ' + e.message);
  } finally {
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = oldText; }
  }
}

// ==================== F3: 聊天记录持久化 ====================
async function loadChatHistory(courseId) {
  const stream = document.getElementById('chatStream');
  if (!stream || !courseId) return;
  stream.querySelectorAll('.fade-in').forEach(el => el.remove());
  const emptyState = document.getElementById('chatEmptyState');

  const localMsgs = loadChatFromLocalStorage(courseId);
  if (localMsgs.length > 0) {
    if (emptyState) emptyState.classList.add('hidden');
    localMsgs.forEach(m => {
      const role = m.role === 'user' ? 'user' : 'assistant';
      const content = m.content || '';
      if (role === 'user') appendUserMessage(content);
      else appendAiMessage(content);
    });
    stream.scrollTop = stream.scrollHeight;
  }

  try {
    const data = await api(`/api/courses/${courseId}/chat-messages`);
    const remoteMsgs = Array.isArray(data.data) ? data.data : [];
    if (remoteMsgs.length === 0 && localMsgs.length === 0) {
      if (emptyState) emptyState.classList.remove('hidden');
      toast('暂无历史对话', 1500);
      return;
    }
    if (emptyState) emptyState.classList.add('hidden');

    const merged = mergeChatMessages(localMsgs, remoteMsgs);
    saveChatToLocalStorage(courseId, remoteMsgs);

    if (remoteMsgs.length > 0 && localMsgs.length !== remoteMsgs.length) {
      stream.querySelectorAll('.fade-in').forEach(el => el.remove());
      merged.forEach(m => {
        const role = m.role === 'user' ? 'user' : 'assistant';
        const content = m.content || '';
        if (role === 'user') appendUserMessage(content);
        else appendAiMessage(content);
      });
      stream.scrollTop = stream.scrollHeight;
    }
  } catch (e) {
    if (localMsgs.length === 0 && emptyState) emptyState.classList.remove('hidden');
    console.warn('loadChatHistory failed:', e.message);
  }
}

// ==================== F1/F3: 按钮事件绑定 ====================
document.getElementById('fullscreenPreviewBtn')?.addEventListener('click', openFullscreenLesson);
document.getElementById('openTemplateLibraryBtn')?.addEventListener('click', () => {
  if (typeof openTemplateLibrary === 'function') openTemplateLibrary();
});
document.getElementById('pptOpenTemplateLibraryBtn')?.addEventListener('click', () => {
  if (typeof openTemplateLibrary === 'function') openTemplateLibrary();
});
document.getElementById('pptFullscreenBtn')?.addEventListener('click', () => {
  if (typeof renderPptFullscreen === 'function') renderPptFullscreen();
});
document.getElementById('closeFullscreenBtn')?.addEventListener('click', () => {
  if (_fullscreenLessonState.dirty) {
    showConfirm('有未保存的修改', '关闭将丢失未保存的修改，确认关闭？').then(ok => { if (ok) closeFullscreenLesson(); });
  } else {
    closeFullscreenLesson();
  }
});
document.getElementById('toggleEditBtn')?.addEventListener('click', toggleLessonEditMode);
document.getElementById('saveLessonBtn')?.addEventListener('click', saveEditedLesson);
// ESC 关闭
document.getElementById('fullscreenLessonModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'fullscreenLessonModal') {
    if (_fullscreenLessonState.dirty) {
      showConfirm('有未保存的修改', '关闭将丢失未保存的修改，确认关闭？').then(ok => { if (ok) closeFullscreenLesson(); });
    } else {
      closeFullscreenLesson();
    }
  }
});

// contenteditable 元素的 hover 提示样式（淡黄色边框）
(function() {
  const style = document.createElement('style');
  style.textContent = `
    #fullscreenLessonBody .editable-active {
      outline: 1px dashed rgba(245, 158, 11, 0.55);
      outline-offset: 2px;
      border-radius: 2px;
      transition: background 0.15s, box-shadow 0.15s;
      cursor: text;
    }
    #fullscreenLessonBody .editable-active:hover {
      background: rgba(254, 240, 138, 0.45);
      box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.35);
    }
    #fullscreenLessonBody .editable-active:focus {
      background: rgba(254, 240, 138, 0.6);
      outline: 2px solid rgba(46, 125, 110, 0.65);
    }
  `;
  document.head.appendChild(style);
})();