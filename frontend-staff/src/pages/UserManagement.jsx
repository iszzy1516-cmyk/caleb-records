import { useState, useEffect, useRef } from 'react';
import * as XLSX from 'xlsx';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

const ROLES = [
  { value: 'dean', label: 'Dean' },
  { value: 'hod', label: 'HOD' },
  { value: 'records_officer', label: 'Records Officer' },
  { value: 'lecturer', label: 'Lecturer' },
  { value: 'registrar', label: 'Registrar' },
  { value: 'admin', label: 'Admin' },
];

const DEPT_ROLES = ['hod', 'records_officer', 'lecturer'];

export default function UserManagement() {
  const { isAdmin, isRegistrar, isDean, collegeId, collegeName, departmentId } = useAuth();
  const isGlobal = isAdmin || isRegistrar;

  const [mode, setMode] = useState('single');
  const [colleges, setColleges] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState({
    username: '',
    full_name: '',
    email: '',
    phone: '',
    role: isDean ? 'hod' : '',
    college_id: isGlobal ? '' : (collegeId || ''),
    department_id: isDean ? '' : (departmentId || ''),
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Bulk state
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);
  const bulkInputRef = useRef(null);

  useEffect(() => {
    if (isGlobal) {
      api.getColleges().then(setColleges).catch(() => {});
    }
  }, [isGlobal]);

  useEffect(() => {
    if (form.college_id) {
      api.getDepartments(form.college_id).then(setDepartments).catch(() => {});
    } else {
      setDepartments([]);
    }
    setForm((f) => ({ ...f, department_id: '' }));
  }, [form.college_id]);

  useEffect(() => {
    if (isDean && collegeId && !isGlobal) {
      api.getDepartments(collegeId).then(setDepartments).catch(() => {});
    }
  }, [isDean, collegeId, isGlobal]);

  const availableRoles = isGlobal
    ? ROLES
    : ROLES.filter((r) => DEPT_ROLES.includes(r.value));

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const payload = { ...form };
      if (isDean) {
        payload.college_id = collegeId;
      }
      await api.createUser(payload);
      setSuccess(`User ${payload.email} created successfully`);
      setForm({
        username: '',
        full_name: '',
        email: '',
        phone: '',
        role: isDean ? 'hod' : '',
        college_id: isGlobal ? '' : (collegeId || ''),
        department_id: isDean ? '' : (departmentId || ''),
        password: '',
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const parseBulkFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const json = XLSX.utils.sheet_to_json(worksheet, { defval: '' });
          resolve(json);
        } catch {
          reject(new Error('Could not parse file. Make sure it is a valid CSV or Excel sheet.'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsArrayBuffer(file);
    });
  };

  const normalizeUserRow = (row) => {
    const get = (...keys) => {
      for (const k of keys) {
        if (row[k] !== undefined && row[k] !== '') return row[k];
      }
      return undefined;
    };

    const username = String(get('username', 'user_name', 'username') || '').trim();
    const fullName = String(get('full_name', 'fullName', 'full name', 'fullname') || '').trim() || undefined;
    const email = String(get('email', 'email address') || '').trim();
    const phone = String(get('phone', 'phone number', 'phone_no', 'phoneNo') || '').trim() || undefined;
    const role = String(get('role') || '').trim().toLowerCase();
    const collegeIdVal = Number(get('college_id', 'college id', 'collegeId', 'college'));
    const departmentIdVal = Number(get('department_id', 'department id', 'departmentId', 'department'));
    const password = String(get('password') || '').trim() || undefined;

    if (!username) throw new Error('username is required');
    if (!email) throw new Error('email is required');
    if (!role) throw new Error('role is required');
    if (!DEPT_ROLES.includes(role) && role !== 'dean' && role !== 'registrar' && role !== 'admin') {
      throw new Error(`invalid role: ${role}`);
    }
    if (DEPT_ROLES.includes(role) && (!departmentIdVal || isNaN(departmentIdVal))) {
      throw new Error('department_id is required for HOD/records officer/lecturer');
    }
    if ((role === 'dean' || role === 'registrar' || role === 'admin') && (!collegeIdVal || isNaN(collegeIdVal))) {
      throw new Error('college_id is required for dean/registrar/admin');
    }

    return {
      username,
      full_name: fullName,
      email,
      phone,
      role,
      college_id: collegeIdVal || undefined,
      department_id: departmentIdVal || undefined,
      password,
    };
  };

  const handleBulkSubmit = async (e) => {
    e.preventDefault();
    if (!bulkFile) {
      setError('Please select a CSV or Excel file');
      return;
    }
    setBulkLoading(true);
    setError('');
    setBulkResult(null);
    try {
      const rows = await parseBulkFile(bulkFile);
      if (!Array.isArray(rows) || rows.length === 0) throw new Error('File is empty or has no data rows');
      const users = rows.map(normalizeUserRow);
      const res = await api.bulkCreateUsers(users);
      setBulkResult(res);
      setBulkFile(null);
      if (bulkInputRef.current) bulkInputRef.current.value = '';
    } catch (err) {
      setError(err.message);
    } finally {
      setBulkLoading(false);
    }
  };

  const downloadTemplate = () => {
    const headers = ['username', 'full_name', 'email', 'phone', 'role', 'college_id', 'department_id', 'password'];
    const examples = [
      ['dean.cocis', 'Dean of COCIS', 'dean.cocis@calebuniversity.edu.ng', '08000000000', 'dean', 7, '', 'tempPass123'],
      ['hod.cs', 'HOD Computer Science', 'hod.cs@calebuniversity.edu.ng', '08000000001', 'hod', 7, 1, 'tempPass123'],
      ['records.cyber', 'Records Officer Cyber Security', 'records.cyber@calebuniversity.edu.ng', '08000000002', 'records_officer', 7, 2, 'tempPass123'],
    ];
    const ws = XLSX.utils.aoa_to_sheet([headers, ...examples]);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'staff');
    XLSX.writeFile(wb, 'staff_bulk_upload_template.xlsx');
  };

  return (
    <div>
      <div className="page-header">
        <h1>User Management</h1>
        <p>{isGlobal ? 'Create staff accounts one at a time or upload a spreadsheet' : 'Create staff accounts for your college'}</p>
      </div>

      {(isGlobal || isDean) && (
        <div className="tabs" style={{ marginBottom: '1.5rem' }}>
          <button className={`tab ${mode === 'single' ? 'active' : ''}`} onClick={() => setMode('single')}>Single User</button>
          {isGlobal && (
            <button className={`tab ${mode === 'bulk' ? 'active' : ''}`} onClick={() => setMode('bulk')}>Bulk Upload</button>
          )}
        </div>
      )}

      {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: '1rem' }}>{success}</div>}

      {mode === 'single' && (
        <form onSubmit={handleSubmit} className="card" style={{ maxWidth: '700px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input name="username" className="form-input" value={form.username} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input name="full_name" className="form-input" value={form.full_name} onChange={handleChange} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input name="email" type="email" className="form-input" value={form.email} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input name="phone" className="form-input" value={form.phone} onChange={handleChange} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Role</label>
            <select name="role" className="form-select" value={form.role} onChange={handleChange} required>
              <option value="">Select role</option>
              {availableRoles.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {isGlobal ? (
              <div className="form-group">
                <label className="form-label">College</label>
                <select name="college_id" className="form-select" value={form.college_id} onChange={handleChange} required>
                  <option value="">Select College</option>
                  {colleges.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label">College</label>
                <input className="form-input" value={collegeName || ''} disabled />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Department</label>
              <select
                name="department_id"
                className="form-select"
                value={form.department_id}
                onChange={handleChange}
                required={DEPT_ROLES.includes(form.role)}
                disabled={!form.college_id && isGlobal}
              >
                <option value="">Select Department</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Temporary Password</label>
            <input name="password" type="password" className="form-input" value={form.password} onChange={handleChange} required />
            <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)', marginTop: '0.25rem' }}>
              New dean and HOD accounts will be asked to change this password on first login.
            </p>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create User'}
          </button>
        </form>
      )}

      {mode === 'bulk' && (
        <form onSubmit={handleBulkSubmit} className="card" style={{ maxWidth: '700px' }}>
          <div className="form-group">
            <label className="form-label">Staff Spreadsheet (CSV or Excel)</label>
            <input
              ref={bulkInputRef}
              type="file"
              className="form-input"
              accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
              onChange={(e) => setBulkFile(e.target.files[0])}
              required
            />
            <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)', marginTop: '0.5rem' }}>
              Required columns: <strong>username, email, role</strong>. For HOD/records officer/lecturer add <strong>department_id</strong>.
              For dean/registrar/admin add <strong>college_id</strong>. Optional: full_name, phone, password.
              If password is omitted, a default will be generated.
            </p>
            <button type="button" className="btn btn-sm btn-outline" style={{ marginTop: '0.5rem' }} onClick={downloadTemplate}>
              Download Template
            </button>
          </div>

          <button type="submit" className="btn btn-primary" disabled={bulkLoading || !bulkFile}>
            {bulkLoading ? 'Uploading...' : 'Upload Staff'}
          </button>

          {bulkResult && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: bulkResult.failed > 0 ? 'var(--cul-warning-light)' : 'var(--cul-success-light)', borderRadius: '0.5rem' }}>
              <p style={{ margin: 0, fontWeight: 600, color: bulkResult.failed > 0 ? 'var(--cul-warning)' : 'var(--cul-success)' }}>
                {bulkResult.created} created, {bulkResult.failed} failed
              </p>
              {bulkResult.usernames.length > 0 && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ fontSize: '0.875rem', cursor: 'pointer' }}>Usernames ({bulkResult.usernames.length})</summary>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', marginTop: '0.5rem', maxHeight: '150px', overflow: 'auto' }}>
                    {bulkResult.usernames.map((u) => <div key={u}>{u}</div>)}
                  </div>
                </details>
              )}
              {bulkResult.errors.length > 0 && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ fontSize: '0.875rem', cursor: 'pointer', color: 'var(--cul-danger)' }}>Errors ({bulkResult.errors.length})</summary>
                  <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--cul-danger)' }}>
                    {bulkResult.errors.map((e, i) => <div key={i}>{e}</div>)}
                  </div>
                </details>
              )}
            </div>
          )}
        </form>
      )}
    </div>
  );
}
