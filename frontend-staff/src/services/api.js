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
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

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
  searchStudents: (params) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set('q', params.q);
    if (params.college_id) qs.set('college_id', params.college_id);
    if (params.department_id) qs.set('department_id', params.department_id);
    if (params.session) qs.set('session', params.session);
    return request(`/api/students/search?${qs.toString()}`);
  },
  getStudent: (id) => request(`/api/students/${id}`),
  createStudent: (data) => request('/api/students', { method: 'POST', body: JSON.stringify(data) }),
  bulkCreateStudents: (students) => request('/api/students/bulk', { method: 'POST', body: JSON.stringify({ students }) }),
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

  // Stats
  getStats: () => request('/api/stats'),

  // Document Deadlines
  getDocumentDeadlines: () => request('/api/document-deadlines'),
  createDocumentDeadline: (data) => request('/api/document-deadlines', { method: 'POST', body: JSON.stringify(data) }),
  deleteDocumentDeadline: (id) => request(`/api/document-deadlines/${id}`, { method: 'DELETE' }),

  // Alerts
  getAlerts: () => request('/api/alerts'),

  // Reports
  getMissingDocuments: () => request('/api/reports/missing-documents'),

  // Audit logs
  getAuditLogs: (limit = 50) => request(`/api/audit-logs?limit=${limit}`),

  // User management
  createUser: (data) => request('/api/users', { method: 'POST', body: JSON.stringify(data) }),
  bulkCreateUsers: (users) => request('/api/users/bulk', { method: 'POST', body: JSON.stringify({ users }) }),
  changeStaffPassword: (data, token = null) => {
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return request('/api/users/change-password', { method: 'POST', headers, body: JSON.stringify(data) });
  },

  // Staff Registration with OTP
  requestStaffRegistration: (data) => request('/api/staff/register-request', { method: 'POST', body: JSON.stringify(data) }),
  verifyStaffRegistration: (data) => request('/api/staff/register-verify', { method: 'POST', body: JSON.stringify(data) }),

  // Password Reset
  requestPasswordReset: (matric) => request('/api/password-reset-request', { method: 'POST', body: JSON.stringify({ matric_number: matric }) }),
  confirmPasswordReset: (token, newPassword) => request('/api/password-reset', { method: 'POST', body: JSON.stringify({ token, new_password: newPassword }) }),

  // Public
  publicStudentLookup: (matric) => request(`/api/public/students/${encodeURIComponent(matric)}`),
};
