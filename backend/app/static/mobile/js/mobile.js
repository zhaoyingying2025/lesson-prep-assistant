(function() {
  'use strict';

  const API_BASE = '/api';

  let state = {
    currentTab: 'plan',
    courses: [],
    currentCourseId: null,
    currentLessonId: null,
    workflows: [],
    messages: [],
    currentStep: 1,
    knowledgePoints: [],
    lessonPreview: null,
  };

  async function api(path, options = {}) {
    const url = API_BASE + path;
    const config = {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    };
    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }
    try {
      const res = await fetch(url, config);
      const data = await res.json();
      if (!data.success) throw new Error(data.message || '请求失败');
      return data.data;
    } catch (err) {
      if (err.message !== '请求失败') throw err;
      throw err;
    }
  }

  function toast(msg) {
    const el = document.getElementById('mobileToast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), 2000);
  }

  function switchTab(tabId) {
    state.currentTab = tabId;
    document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));
    const panel = document.getElementById('tab-' + tabId);
    const tab = document.querySelector(`[data-tab="${tabId}"]`);
    if (panel) panel.classList.add('active');
    if (tab) tab.classList.add('active');
  }

  function showLoading(btn) {
    if (!btn) return;
    btn._origHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-dots"><span></span><span></span><span></span></span>';
  }

  function hideLoading(btn) {
    if (!btn) return;
    btn.disabled = false;
    if (btn._origHtml) btn.innerHTML = btn._origHtml;
  }

  async function checkApiStatus() {
    const dot = document.getElementById('mobileApiStatus');
    if (!dot) return;
    try {
      const res = await fetch(API_BASE + '/health');
      if (res.ok) {
        dot.className = 'api-status online';
      } else {
        dot.className = 'api-status offline';
      }
    } catch {
      dot.className = 'api-status offline';
    }
  }

  async function loadCourses() {
    const list = document.getElementById('mobileCourseList');
    if (!list) return;
    try {
      state.courses = await api('/courses') || [];
      if (state.courses.length === 0) {
        list.innerHTML = '<div class="empty-state"><div class="empty-icon">📚</div><div class="empty-text">暂无课程，请在桌面端创建</div></div>';
        return;
      }
      list.innerHTML = state.courses.map(c => `
        <div class="list-item" data-course-id="${c.id}" onclick="mobileApp.selectCourse(${c.id}, '${escapeJs(c.name)}')">
          <div class="item-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M4 6H2v14a2 2 0 002 2h14v-2H4V6zm16-4H8a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2zm0 14H8V4h12v12z"/></svg>
          </div>
          <div class="item-info">
            <div class="item-title">${escapeHtml(c.name)}</div>
            <div class="item-sub">${escapeHtml(c.subject || '')}${c.grade ? ' · ' + escapeHtml(c.grade) : ''}</div>
          </div>
          <div class="item-arrow">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
          </div>
        </div>
      `).join('');
    } catch (err) {
      list.innerHTML = `<div class="empty-state"><div class="empty-text">加载失败: ${err.message}</div></div>`;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function escapeJs(str) {
    if (!str) return '';
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '\\r');
  }

  async function selectCourse(id, name) {
    state.currentCourseId = id;
    state.currentLessonId = null;
    state.currentStep = 1;
    document.getElementById('mobileSelectedCourse').textContent = name;
    document.getElementById('mobileStep1').classList.add('completed');
    document.getElementById('mobileStep1Connector').classList.add('active');
    toast('已选择: ' + name);
    loadChapters(id);
  }

  async function loadChapters(courseId) {
    const list = document.getElementById('mobileChapterList');
    if (!list) return;
    try {
      const chapters = await api(`/courses/${courseId}/chapters`) || [];
      if (chapters.length === 0) {
        list.innerHTML = '<div class="empty-state"><div class="empty-text">暂无章节，请先在桌面端添加</div></div>';
        return;
      }
      list.innerHTML = chapters.map(ch => `
        <div class="list-item" onclick="mobileApp.selectChapter(${ch.id}, '${escapeJs(ch.title)}')">
          <div class="item-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 7V3.5L18.5 9H13z"/></svg>
          </div>
          <div class="item-info">
            <div class="item-title">${escapeHtml(ch.title)}</div>
          </div>
          <div class="item-arrow">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
          </div>
        </div>
      `).join('');
    } catch (err) {
      list.innerHTML = `<div class="empty-state"><div class="empty-text">加载失败: ${err.message}</div></div>`;
    }
  }

  async function selectChapter(id, title) {
    state.currentLessonId = id;
    document.getElementById('mobileSelectedChapter').textContent = title;
    document.getElementById('mobileStep2').classList.add('completed');
    document.getElementById('mobileStep2Connector').classList.add('active');
    toast('已选择: ' + title);
  }

  async function startExtract() {
    if (!state.currentCourseId || !state.currentLessonId) {
      toast('请先选择课程和章节');
      return;
    }
    const btn = document.getElementById('mobileExtractBtn');
    showLoading(btn);
    try {
      const result = await api('/knowledge/extract', {
        method: 'POST',
        body: { course_id: state.currentCourseId, lesson_id: state.currentLessonId },
      });
      state.knowledgePoints = result.knowledge_points || [];
      state.currentStep = 3;
      document.getElementById('mobileStep3').classList.add('completed');
      toast('知识点提取完成');
      renderKnowledgePoints();
    } catch (err) {
      toast('提取失败: ' + err.message);
    } finally {
      hideLoading(btn);
    }
  }

  function renderKnowledgePoints() {
    const container = document.getElementById('mobileKpResult');
    if (!container) return;
    if (state.knowledgePoints.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="empty-text">暂无知识点数据</div></div>';
      return;
    }
    container.innerHTML = state.knowledgePoints.map(kp => `
      <div class="card" style="padding:10px 14px;margin-bottom:6px">
        <div style="font-size:13px;font-weight:500">${escapeHtml(kp.name)}</div>
        ${kp.description ? '<div style="font-size:12px;color:var(--text-muted);margin-top:4px">' + escapeHtml(kp.description) + '</div>' : ''}
      </div>
    `).join('');
  }

  async function generateLesson() {
    if (!state.currentCourseId || !state.currentLessonId) {
      toast('请先选择课程和章节');
      return;
    }
    const btn = document.getElementById('mobileGenerateBtn');
    showLoading(btn);
    try {
      const result = await api('/lesson/generate', {
        method: 'POST',
        body: { course_id: state.currentCourseId, lesson_id: state.currentLessonId },
      });
      state.lessonPreview = result;
      toast('教案生成完成');
      renderLessonPreview();
    } catch (err) {
      toast('生成失败: ' + err.message);
    } finally {
      hideLoading(btn);
    }
  }

  function renderLessonPreview() {
    const container = document.getElementById('mobileLessonPreview');
    if (!container || !state.lessonPreview) return;
    const lp = state.lessonPreview;
    container.innerHTML = `
      <div class="card">
        <div class="card-title">
          <span>${escapeHtml(lp.title || '教案预览')}</span>
          <span class="tag tag-primary">${lp.status || 'draft'}</span>
        </div>
        ${lp.teaching_objectives ? '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px"><strong>教学目标</strong><br>' + escapeHtml(lp.teaching_objectives) + '</div>' : ''}
        ${lp.teaching_process ? '<div style="font-size:12px;color:var(--text-secondary)"><strong>教学过程</strong><br>' + escapeHtml(lp.teaching_process.substring(0, 200)) + '…</div>' : ''}
      </div>
    `;
  }

  async function loadWorkflows() {
    const list = document.getElementById('mobileWorkflowList');
    if (!list) return;
    try {
      state.workflows = await api('/workflows') || [];
      if (state.workflows.length === 0) {
        list.innerHTML = '<div class="empty-state"><div class="empty-icon">⚙️</div><div class="empty-text">暂无工作流，请在桌面端创建</div></div>';
        return;
      }
      list.innerHTML = state.workflows.map(wf => `
        <div class="card" style="padding:12px 14px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-size:14px;font-weight:500">${escapeHtml(wf.name)}</div>
              ${wf.description ? '<div style="font-size:12px;color:var(--text-muted);margin-top:2px">' + escapeHtml(wf.description) + '</div>' : ''}
            </div>
            <span class="tag tag-primary">${wf.steps ? wf.steps.length : 0}步</span>
          </div>
          <div style="display:flex;gap:6px;margin-top:8px">
            <button class="btn btn-outline btn-sm" onclick="mobileApp.runWorkflow(${wf.id})">执行</button>
            <button class="btn btn-ghost btn-sm" onclick="mobileApp.viewWorkflow(${wf.id})">详情</button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      list.innerHTML = `<div class="empty-state"><div class="empty-text">加载失败: ${err.message}</div></div>`;
    }
  }

  async function runWorkflow(id) {
    const btn = event.target;
    showLoading(btn);
    try {
      const result = await api(`/workflows/${id}/execute`, { method: 'POST' });
      toast('工作流执行完成');
    } catch (err) {
      toast('执行失败: ' + err.message);
    } finally {
      hideLoading(btn);
    }
  }

  function viewWorkflow(id) {
    const wf = state.workflows.find(w => w.id === id);
    if (!wf) return;
    toast(wf.name + ': ' + (wf.description || '无描述'));
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    document.querySelectorAll('.theme-option').forEach(el => {
      el.classList.toggle('active', el.dataset.theme === theme);
    });
  }

  function loadTheme() {
    const saved = localStorage.getItem('theme') || '';
    if (saved) setTheme(saved);
    document.querySelectorAll('.theme-option').forEach(el => {
      el.classList.toggle('active', el.dataset.theme === (saved || ''));
    });
  }

  function initSettings() {
    document.getElementById('mobileAppVersion').textContent = 'v0.1.0';
    document.getElementById('mobileApiEndpoint').textContent = window.location.origin + '/api';
  }

  function init() {
    switchTab('plan');
    checkApiStatus();
    loadCourses();
    loadWorkflows();
    loadTheme();
    initSettings();
    setInterval(checkApiStatus, 30000);
  }

  const mobileApp = {
    switchTab,
    selectCourse,
    selectChapter,
    startExtract,
    generateLesson,
    runWorkflow,
    viewWorkflow,
    setTheme,
    toast,
    loadCourses,
    loadWorkflows,
  };

  window.mobileApp = mobileApp;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();