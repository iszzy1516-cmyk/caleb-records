import { invoke } from '@tauri-apps/api/core';

const els = {
  backendDot: document.getElementById('backend-dot'),
  backendStatus: document.getElementById('backend-status'),
  btnStaff: document.getElementById('btn-staff'),
};

function setStatus(online, text) {
  const dot = els.backendDot;
  const status = els.backendStatus;
  dot.classList.remove('online', 'offline');
  dot.classList.add(online ? 'online' : 'offline');
  status.textContent = text;
}

async function checkStatus() {
  try {
    const backend = await invoke('check_backend_status');
    setStatus(backend, backend ? 'Online' : 'Offline');
  } catch (e) {
    setStatus(false, 'Unreachable');
  }
}

els.btnStaff.addEventListener('click', async () => {
  try {
    await invoke('open_staff_portal');
  } catch (e) {
    alert('Failed to open Staff Portal: ' + e);
  }
});

checkStatus();
setInterval(checkStatus, 5000);
