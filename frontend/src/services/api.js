function getApiBase() {
  // Use explicit API URL if set (build-time env var)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Tauri mobile/desktop app connects to live server
  if (typeof window !== 'undefined' && window.__TAURI__) {
    return 'https://culrecords.duckdns.org';
  }
  // Web frontend uses same-domain relative path
  return '';
}

const API_BASE = getApiBase();

function getToken() {
  return localStorage.getItem('cul_token');
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem('cul_token');
    localStorage.removeItem('cul_token_type');
    localStorage.removeItem('cul_user');
    window.location.href = '/';
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Auth
  login: (username, password) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    return fetch(`${API_BASE}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(err.detail || 'Login failed');
      }
      return res.json();
    });
  },

  studentLogin: (matric, password) => {
    const form = new URLSearchParams();
    form.append('username', matric);
    form.append('password', password);
    return fetch(`${API_BASE}/token/student`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(err.detail || 'Login failed');
      }
      return res.json();
    });
  },

  // Reference data
  getColleges: () => request('/api/colleges'),
  getDepartments: (collegeId) => request(`/api/departments?college_id=${collegeId}`),
  getPrograms: (deptId) => request(`/api/programs?department_id=${deptId}`),
  getCourses: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/courses?${qs}`);
  },

  // Students
  searchStudents: (q) => request(`/api/students/search?q=${encodeURIComponent(q)}`),
  getStudent: (id) => request(`/api/students/${id}`),
  createStudent: (data) => request('/api/students', { method: 'POST', body: JSON.stringify(data) }),
  registerStudent: (data) => fetch(`${API_BASE}/api/students/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(async (res) => {
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  }),
  getStudentCgpa: (id) => request(`/api/students/${id}/cgpa`),

  // Documents (staff)
  uploadDocument: (formData) => {
    return fetch(`${API_BASE}/api/documents`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || 'Upload failed');
      }
      return res.json();
    });
  },

  // Documents (student self-service)
  uploadMyDocument: (formData) => {
    return fetch(`${API_BASE}/api/me/documents`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || 'Upload failed');
      }
      return res.json();
    });
  },

  downloadDocument: (id) => `${API_BASE}/api/documents/${id}/download`,

  // Grades
  createGrade: (data) => request('/api/grades', { method: 'POST', body: JSON.stringify(data) }),
  getMyGrades: () => request('/api/me/grades'),

  // Student self-service
  getMe: () => request('/api/me'),

  // Reports
  getMissingDocuments: () => request('/api/reports/missing-documents'),

  // Audit logs
  getAuditLogs: (limit = 50) => request(`/api/audit-logs?limit=${limit}`),

  // Alerts
  getMyAlerts: () => request('/api/me/alerts'),
  markAlertRead: (id) => request(`/api/me/alerts/${id}/read`, { method: 'POST' }),

  // Payments
  makePayment: (data) => request('/api/me/payments', { method: 'POST', body: JSON.stringify(data) }),

  // Document deadlines (public)
  getDocumentDeadlines: () => request('/api/document-deadlines'),

  // Password
  requestPasswordReset: (matric) => request('/api/password-reset-request', { method: 'POST', body: JSON.stringify({ matric_number: matric }) }),
  confirmPasswordReset: (token, newPassword) => request('/api/password-reset', { method: 'POST', body: JSON.stringify({ token, new_password: newPassword }) }),
  changePassword: (currentPassword, newPassword) => request('/api/me/change-password', { method: 'POST', body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }),

  // Public
  publicStudentLookup: (matric) => request(`/api/public/students/${encodeURIComponent(matric)}`),
};
