const ToastProvider = {
  container: null,
  
  init() {
    if (!document.getElementById('toast-container')) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    } else {
      this.container = document.getElementById('toast-container');
    }
  },
  
  show(message, type) {
    this.init();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '';
    if (type === 'success') icon = 'check-circle';
    else if (type === 'error') icon = 'alert-circle';
    else if (type === 'warning') icon = 'alert-triangle';
    else if (type === 'info') icon = 'info';
    
    toast.innerHTML = `
      <i data-lucide="${icon}" class="toast-icon"></i>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.closest('.toast').classList.remove('show'); setTimeout(() => this.closest('.toast').remove(), 300);"><i data-lucide="x"></i></button>
    `;
    
    this.container.appendChild(toast);
    if(window.lucide) lucide.createIcons({root: toast});
    
    // Trigger reflow for animation
    void toast.offsetWidth;
    toast.classList.add('show');
    
    // Auto dismiss after 3 seconds
    setTimeout(() => {
      if (toast.parentElement) {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
      }
    }, 3000);
  }
};

window.showSuccess = (msg) => ToastProvider.show(msg, 'success');
window.showError = (msg) => ToastProvider.show(msg, 'error');
window.showWarning = (msg) => ToastProvider.show(msg, 'warning');
window.showInfo = (msg) => ToastProvider.show(msg, 'info');
window.showToast = (msg, type = 'success') => ToastProvider.show(msg, type);
