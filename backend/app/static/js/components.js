// UI 组件库
// 封装高频 UI 组件：Toast、Button、Modal、Skeleton、Stepper
// 使用方式：UI.Toast.success('消息'), UI.Button.loading(btn), 等
const UI = (function() {

  // ========== Toast 通知系统 ==========
  const Toast = {
    _icons: { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' },

    show(msg, type, duration) {
      type = type || 'info';
      duration = duration || 2500;
      const container = document.getElementById('toastContainer');
      if (!container) return;
      const icon = this._icons[type] || 'ℹ';
      const item = document.createElement('div');
      item.className = 'toast-item toast-' + type;
      item.innerHTML = '<span class="toast-icon">' + icon + '</span><span>' + msg + '</span>';
      container.appendChild(item);
      setTimeout(function() {
        item.classList.add('toast-leaving');
        setTimeout(function() { item.remove(); }, 250);
      }, duration);
    },

    success(msg, duration) { this.show(msg, 'success', duration); },
    error(msg, duration) { this.show(msg, 'error', duration || 3500); },
    info(msg, duration) { this.show(msg, 'info', duration); },
    warning(msg, duration) { this.show(msg, 'warning', duration); }
  };

  // ========== Button 按钮状态管理 ==========
  const Button = {
    loading(btn, text) {
      if (!btn) return;
      btn._originalText = btn.textContent;
      btn._originalDisabled = btn.disabled;
      btn.disabled = true;
      btn.textContent = text || '处理中...';
    },

    done(btn) {
      if (!btn) return;
      btn.disabled = btn._originalDisabled || false;
      if (btn._originalText) {
        btn.textContent = btn._originalText;
        delete btn._originalText;
      }
      delete btn._originalDisabled;
    },

    async withLoading(btn, asyncFn, loadingText) {
      this.loading(btn, loadingText);
      try {
        return await asyncFn();
      } finally {
        this.done(btn);
      }
    }
  };

  // ========== Modal 模态框 ==========
  const Modal = {
    open(id) {
      const modal = document.getElementById(id);
      if (!modal) return;
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    },

    close(id) {
      const modal = document.getElementById(id);
      if (!modal) return;
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  };

  // ========== Skeleton 骨架屏 ==========
  const Skeleton = {
    show(id) {
      const skeleton = document.getElementById(id + 'Skeleton');
      const content = document.getElementById(id);
      if (skeleton) skeleton.classList.remove('hidden');
      if (content) content.style.display = 'none';
    },

    hide(id) {
      const skeleton = document.getElementById(id + 'Skeleton');
      const content = document.getElementById(id);
      if (skeleton) skeleton.classList.add('hidden');
      if (content) content.style.display = '';
    }
  };

  // ========== Stepper 步骤条 ==========
  const Stepper = {
    goTo(step) {
      if (typeof goToStep === 'function') {
        goToStep(step);
      }
    },

    getCurrent() {
      return typeof state !== 'undefined' ? state.currentStep : 1;
    }
  };

  return { Toast: Toast, Button: Button, Modal: Modal, Skeleton: Skeleton, Stepper: Stepper };
})();