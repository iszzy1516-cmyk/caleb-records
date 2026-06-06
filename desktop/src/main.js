import { invoke } from '@tauri-apps/api/core';

// DOM refs
const els = {
  backendDot: document.getElementById('backend-dot'),
  backendStatus: document.getElementById('backend-status'),
  studentDot: document.getElementById('student-dot'),
  studentStatus: document.getElementById('student-status'),
  staffDot: document.getElementById('staff-dot'),
  staffStatus: document.getElementById('staff-status'),
  btnStartBackend: document.getElementById('btn-start-backend'),
  btnStopBackend: document.getElementById('btn-stop-backend'),
  btnStudent: document.getElementById('btn-student'),
  btnStaff: document.getElementById('btn-staff'),
  consoleOutput: document.getElementById('console-output'),
  btnClear: document.getElementById('btn-clear'),
};

let backendRunning = false;
let studentRunning = false;
let staffRunning = false;

function log(msg, type = 'info') {
  const time = new Date().toLocaleTimeString();
  const span = document.createElement('div');
  span.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-${type}">${msg}</span>`;
  els.consoleOutput.appendChild(span);
  els.consoleOutput.scrollTop = els.consoleOutput.scrollHeight;
}

function setStatus(service, online, text) {
  const dot = els[`${service}Dot`];
  const status = els[`${service}Status`];
  dot.classList.remove('online', 'offline');
  dot.classList.add(online ? 'online' : 'offline');
  status.textContent = text;
}

function updateButtons() {
  els.btnStartBackend.disabled = backendRunning;
  els.btnStopBackend.disabled = !backendRunning;
  els.btnStudent.disabled = !studentRunning;
  els.btnStaff.disabled = !staffRunning;
}

async function checkStatus() {
  try {
    const backend = await invoke('check_backend_status');
    backendRunning = backend;
    setStatus('backend', backend, backend ? 'Online' : 'Offline');
  } catch (e) {
    backendRunning = false;
    setStatus('backend', false, 'Unreachable');
  }

  try {
    const student = await invoke('check_service_status', { url: 'http://localhost:5173' });
    studentRunning = student;
    setStatus('student', student, student ? 'Online' : 'Offline');
  } catch (e) {
    studentRunning = false;
    setStatus('student', false, 'Unreachable');
  }

  try {
    const staff = await invoke('check_service_status', { url: 'http://localhost:5174' });
    staffRunning = staff;
    setStatus('staff', staff, staff ? 'Online' : 'Offline');
  } catch (e) {
    staffRunning = false;
    setStatus('staff', false, 'Unreachable');
  }

  updateButtons();
}

els.btnStartBackend.addEventListener('click', async () => {
  try {
    log('Starting backend server...', 'info');
    const result = await invoke('start_backend');
    log(result, 'success');
    await checkStatus();
  } catch (e) {
    log(`Failed to start backend: ${e}`, 'error');
  }
});

els.btnStopBackend.addEventListener('click', async () => {
  try {
    log('Stopping backend server...', 'warn');
    const result = await invoke('stop_backend');
    log(result, 'success');
    await checkStatus();
  } catch (e) {
    log(`Failed to stop backend: ${e}`, 'error');
  }
});

els.btnStudent.addEventListener('click', async () => {
  try {
    await invoke('open_student_portal');
    log('Opened Student Portal', 'success');
  } catch (e) {
    log(`Failed to open Student Portal: ${e}`, 'error');
  }
});

els.btnStaff.addEventListener('click', async () => {
  try {
    await invoke('open_staff_portal');
    log('Opened Staff Portal', 'success');
  } catch (e) {
    log(`Failed to open Staff Portal: ${e}`, 'error');
  }
});

els.btnClear.addEventListener('click', () => {
  els.consoleOutput.innerHTML = '';
});

// Initial check and interval
checkStatus();
setInterval(checkStatus, 5000);
log('Caleb Records Desktop initialized', 'info');
log('Checking service status...', 'info');
