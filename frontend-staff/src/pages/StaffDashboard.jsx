import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import Navbar from '../components/Navbar';
import StudentSearch from '../components/StudentSearch';

function Sidebar() {
  const { isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const items = [
    { path: '/staff', label: 'Dashboard', icon: '📊' },
    { path: '/staff/search', label: 'Search Students', icon: '🔍' },
    { path: '/staff/register', label: 'Register Student', icon: '📝' },
    { path: '/staff/upload', label: 'Upload Document', icon: '📁' },
    { path: '/staff/missing', label: 'Missing Documents', icon: '⚠️' },
    { path: '/staff/deadlines', label: 'Document Deadlines', icon: '⏰' },
  ];

  if (isAdmin) {
    items.push({ path: '/staff/audit', label: 'Audit Logs', icon: '📋' });
  }

  return (
    <aside className="sidebar">
      <ul className="sidebar-nav">
        {items.map((item) => (
          <li key={item.path}>
            <a
              href={item.path}
              onClick={(e) => { e.preventDefault(); navigate(item.path); }}
              className={location.pathname === item.path ? 'active' : ''}
            >
              <span>{item.icon}</span>
              {item.label}
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}

function DashboardHome() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of student records system</p>
      </div>

      {loading ? (
        <div className="card text-center" style={{ padding: '3rem' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : stats ? (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Students</h3>
              <div className="value" style={{ color: 'var(--cul-green)' }}>{stats.total_students.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Documents Stored</h3>
              <div className="value" style={{ color: 'var(--cul-blue)' }}>{stats.total_documents.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <h3>Missing Documents</h3>
              <div className="value" style={{ color: 'var(--cul-danger)' }}>{stats.total_missing}</div>
            </div>
            <div className="stat-card">
              <h3>Colleges</h3>
              <div className="value">{stats.total_colleges}</div>
            </div>
          </div>

          <div className="stats-grid" style={{ marginTop: '1rem' }}>
            <div className="stat-card">
              <h3>Departments</h3>
              <div className="value">{stats.total_departments}</div>
            </div>
            <div className="stat-card">
              <h3>Programs</h3>
              <div className="value">{stats.total_programs}</div>
            </div>
            {Object.entries(stats.students_by_level).map(([level, count]) => (
              <div className="stat-card" key={level}>
                <h3>{level}L Students</h3>
                <div className="value">{count}</div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="alert alert-error">Failed to load dashboard stats.</div>
      )}
    </div>
  );
}

function SearchPage() {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = async (student) => {
    setLoading(true);
    try {
      const data = await api.getStudent(student.id);
      setDetails(data);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const docTypes = [
    { key: 'jamb_result', label: 'JAMB Result' },
    { key: 'waec_result', label: 'WAEC/NECO Result' },
    { key: 'jamb_admission_letter', label: 'JAMB Admission Letter' },
    { key: 'birth_certificate', label: 'Birth Certificate' },
    { key: 'passport_photo', label: 'Passport Photo' },
    { key: 'medical', label: 'Medical Report' },
  ];

  const hasDoc = (type, level = null) => {
    if (!details?.documents) return false;
    return details.documents.some((d) => d.document_type === type && (level === null || d.level === level));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Search Students</h1>
        <p>Find students by matric number or name</p>
      </div>

      <StudentSearch onSelect={handleSelect} />

      {loading && (
        <div className="card text-center" style={{ marginTop: '1rem', padding: '2rem' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
          <p style={{ marginTop: '1rem', color: 'var(--cul-gray-500)' }}>Loading profile...</p>
        </div>
      )}

      {details && !loading && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <div>
              <h2>{details.first_name} {details.last_name}</h2>
              <p style={{ margin: 0 }}>{details.matric_number} &middot; {details.program?.name} &middot; {details.current_level}L</p>
            </div>
            <span className="badge badge-green">Active</span>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ marginBottom: '0.75rem' }}>Document Checklist</h3>
            <div className="doc-checklist">
              {docTypes.map((dt) => (
                <div key={dt.key} className={`doc-checklist-item ${hasDoc(dt.key) ? 'present' : 'missing'}`}>
                  <div className="doc-icon">{hasDoc(dt.key) ? '✓' : '✗'}</div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{dt.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)' }}>
                      {hasDoc(dt.key) ? 'Uploaded' : 'Missing'}
                    </div>
                  </div>
                </div>
              ))}
              {[100, 200, 300, 400, 500].map((lvl) => (
                <div key={lvl} className={`doc-checklist-item ${hasDoc('clearance_cert', lvl) ? 'present' : 'missing'}`}>
                  <div className="doc-icon">{hasDoc('clearance_cert', lvl) ? '✓' : '✗'}</div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{lvl}L Clearance</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)' }}>
                      {hasDoc('clearance_cert', lvl) ? 'Uploaded' : 'Missing'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {details.cgpa !== undefined && (
            <div style={{ background: 'var(--cul-green-light)', padding: '1rem', borderRadius: '0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cul-green)' }}>{details.cgpa.toFixed(2)}</span>
              <span style={{ fontSize: '0.875rem', color: 'var(--cul-gray-600)' }}>CGPA</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RegisterPage() {
  const [mode, setMode] = useState('single');
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', phone: '',
    college_id: '', department_id: '', program_id: '',
    admission_year: new Date().getFullYear(), current_level: 100,
    gender: 'male', date_of_birth: '',
  });
  const [colleges, setColleges] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Bulk state
  const [bulkJson, setBulkJson] = useState('');
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  useEffect(() => {
    api.getColleges().then(setColleges).catch(() => {});
  }, []);

  useEffect(() => {
    if (form.college_id) {
      api.getDepartments(form.college_id).then(setDepartments).catch(() => {});
    } else {
      setDepartments([]);
    }
    setForm((f) => ({ ...f, department_id: '', program_id: '' }));
  }, [form.college_id]);

  useEffect(() => {
    if (form.department_id) {
      api.getPrograms(form.department_id).then(setPrograms).catch(() => {});
    } else {
      setPrograms([]);
    }
    setForm((f) => ({ ...f, program_id: '' }));
  }, [form.department_id]);

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
      const data = await api.createStudent(form);
      setSuccess(`Student registered successfully! Matric: ${data.matric_number}`);
      setForm({
        first_name: '', last_name: '', email: '', phone: '',
        college_id: '', department_id: '', program_id: '',
        admission_year: new Date().getFullYear(), current_level: 100,
        gender: 'male', date_of_birth: '',
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkSubmit = async (e) => {
    e.preventDefault();
    setBulkLoading(true);
    setError('');
    setBulkResult(null);
    try {
      const students = JSON.parse(bulkJson);
      if (!Array.isArray(students)) throw new Error('Must be a JSON array');
      const res = await api.bulkCreateStudents(students);
      setBulkResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBulkLoading(false);
    }
  };

  const bulkExample = `[\n  {\n    "first_name": "John",\n    "last_name": "Doe",\n    "email": "john@caleb.edu.ng",\n    "college_id": 7,\n    "department_id": 1,\n    "program_id": 1,\n    "admission_year": 2024,\n    "current_level": 100,\n    "gender": "male"\n  }\n]`;

  return (
    <div>
      <div className="page-header">
        <h1>Register Student</h1>
        <p>Create a new student record with auto-generated matric number</p>
      </div>

      <div className="tabs" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab ${mode === 'single' ? 'active' : ''}`} onClick={() => setMode('single')}>Single Registration</button>
        <button className={`tab ${mode === 'bulk' ? 'active' : ''}`} onClick={() => setMode('bulk')}>Bulk Registration</button>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: '1rem' }}>{success}</div>}

      {mode === 'single' && (
        <form onSubmit={handleSubmit} className="card" style={{ maxWidth: '700px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">First Name</label>
              <input name="first_name" className="form-input" value={form.first_name} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Last Name</label>
              <input name="last_name" className="form-input" value={form.last_name} onChange={handleChange} required />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input name="email" type="email" className="form-input" value={form.email} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input name="phone" className="form-input" value={form.phone} onChange={handleChange} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">College</label>
              <select name="college_id" className="form-select" value={form.college_id} onChange={handleChange} required>
                <option value="">Select College</option>
                {colleges.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Department</label>
              <select name="department_id" className="form-select" value={form.department_id} onChange={handleChange} required disabled={!form.college_id}>
                <option value="">Select Department</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Program</label>
              <select name="program_id" className="form-select" value={form.program_id} onChange={handleChange} required disabled={!form.department_id}>
                <option value="">Select Program</option>
                {programs.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Admission Year</label>
              <input name="admission_year" type="number" className="form-input" value={form.admission_year} onChange={handleChange} required />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Current Level</label>
              <select name="current_level" className="form-select" value={form.current_level} onChange={handleChange}>
                <option value={100}>100 Level</option>
                <option value={200}>200 Level</option>
                <option value={300}>300 Level</option>
                <option value={400}>400 Level</option>
                <option value={500}>500 Level</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Gender</label>
              <select name="gender" className="form-select" value={form.gender} onChange={handleChange}>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Date of Birth</label>
            <input name="date_of_birth" type="date" className="form-input" value={form.date_of_birth} onChange={handleChange} />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Registering...' : 'Register Student'}
          </button>
        </form>
      )}

      {mode === 'bulk' && (
        <form onSubmit={handleBulkSubmit} className="card" style={{ maxWidth: '700px' }}>
          <div className="form-group">
            <label className="form-label">Bulk Student JSON</label>
            <textarea
              className="form-textarea"
              style={{ minHeight: '200px', fontFamily: 'monospace', fontSize: '0.875rem' }}
              value={bulkJson}
              onChange={(e) => setBulkJson(e.target.value)}
              placeholder={bulkExample}
              required
            />
            <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)', marginTop: '0.5rem' }}>
              Paste a JSON array of student objects. Each object needs: first_name, last_name, college_id, department_id, program_id, admission_year.
            </p>
          </div>

          <button type="submit" className="btn btn-primary" disabled={bulkLoading}>
            {bulkLoading ? 'Registering...' : `Register ${(() => { try { return JSON.parse(bulkJson).length; } catch { return 0; } })()} Students`}
          </button>

          {bulkResult && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: bulkResult.failed > 0 ? 'var(--cul-warning-light)' : 'var(--cul-success-light)', borderRadius: '0.5rem' }}>
              <p style={{ margin: 0, fontWeight: 600, color: bulkResult.failed > 0 ? 'var(--cul-warning)' : 'var(--cul-success)' }}>
                {bulkResult.created} created, {bulkResult.failed} failed
              </p>
              {bulkResult.matric_numbers.length > 0 && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ fontSize: '0.875rem', cursor: 'pointer' }}>Matric Numbers ({bulkResult.matric_numbers.length})</summary>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', marginTop: '0.5rem', maxHeight: '150px', overflow: 'auto' }}>
                    {bulkResult.matric_numbers.map((m) => <div key={m}>{m}</div>)}
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

function UploadPage() {
  const [studentId, setStudentId] = useState('');
  const [docType, setDocType] = useState('');
  const [level, setLevel] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const docTypes = [
    { value: 'clearance_cert', label: 'Clearance Certificate' },
    { value: 'jamb_result', label: 'JAMB Result' },
    { value: 'waec_result', label: 'WAEC/NECO Result' },
    { value: 'jamb_admission_letter', label: 'JAMB Admission Letter' },
    { value: 'birth_certificate', label: 'Birth Certificate' },
    { value: 'passport_photo', label: 'Passport Photo' },
    { value: 'medical', label: 'Medical Report' },
    { value: 'fee_receipt', label: 'Fee Receipt' },
    { value: 'transcript', label: 'Transcript' },
  ];

  const showLevel = docType === 'clearance_cert';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) { setError('Please select a file'); return; }
    setLoading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('student_id', studentId);
    formData.append('document_type', docType);
    formData.append('file', file);
    if (showLevel && level) formData.append('level', level);

    try {
      await api.uploadDocument(formData);
      setSuccess('Document uploaded successfully!');
      setStudentId('');
      setDocType('');
      setLevel('');
      setFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Upload Document</h1>
        <p>Upload student documents securely</p>
      </div>

      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: '600px' }}>
        <div className="form-group">
          <label className="form-label">Student ID</label>
          <input type="number" className="form-input" value={studentId} onChange={(e) => setStudentId(e.target.value)} required placeholder="Enter student ID number" />
        </div>

        <div className="form-group">
          <label className="form-label">Document Type</label>
          <select className="form-select" value={docType} onChange={(e) => setDocType(e.target.value)} required>
            <option value="">Select document type</option>
            {docTypes.map((dt) => <option key={dt.value} value={dt.value}>{dt.label}</option>)}
          </select>
        </div>

        {showLevel && (
          <div className="form-group">
            <label className="form-label">Level</label>
            <select className="form-select" value={level} onChange={(e) => setLevel(e.target.value)} required={showLevel}>
              <option value="">Select level</option>
              {[100, 200, 300, 400, 500].map((l) => <option key={l} value={l}>{l} Level</option>)}
            </select>
          </div>
        )}

        <div className="form-group">
          <label className="form-label">File (PDF, JPG, PNG — max 10MB)</label>
          <input
            type="file"
            className="form-input"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
          {file && <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Selected: {file.name}</p>}
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Uploading...' : 'Upload Document'}
        </button>
      </form>
    </div>
  );
}

function DocumentDeadlinesPage() {
  const [deadlines, setDeadlines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ document_type: '', level: '', deadline_date: '', late_fee_amount: 0 });
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const docTypes = [
    { value: 'clearance_cert', label: 'Clearance Certificate' },
    { value: 'jamb_result', label: 'JAMB Result' },
    { value: 'waec_result', label: 'WAEC/NECO Result' },
    { value: 'jamb_admission_letter', label: 'JAMB Admission Letter' },
    { value: 'birth_certificate', label: 'Birth Certificate' },
    { value: 'passport_photo', label: 'Passport Photo' },
    { value: 'medical', label: 'Medical Report' },
    { value: 'fee_receipt', label: 'Fee Receipt' },
    { value: 'transcript', label: 'Transcript' },
  ];

  const loadDeadlines = async () => {
    setLoading(true);
    try {
      const data = await api.getDocumentDeadlines();
      setDeadlines(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDeadlines();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.createDocumentDeadline(form);
      setSuccess('Deadline set successfully!');
      setForm({ document_type: '', level: '', deadline_date: '', late_fee_amount: 0 });
      loadDeadlines();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Deactivate this deadline?')) return;
    try {
      await api.deleteDocumentDeadline(id);
      loadDeadlines();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Document Deadlines</h1>
        <p>Set upload deadlines and late fees for documents</p>
      </div>

      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: '600px', marginBottom: '1.5rem' }}>
        <div className="form-group">
          <label className="form-label">Document Type</label>
          <select className="form-select" value={form.document_type} onChange={(e) => setForm({ ...form, document_type: e.target.value })} required>
            <option value="">Select type</option>
            {docTypes.map((dt) => <option key={dt.value} value={dt.value}>{dt.label}</option>)}
          </select>
        </div>

        {form.document_type === 'clearance_cert' && (
          <div className="form-group">
            <label className="form-label">Level</label>
            <select className="form-select" value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} required>
              <option value="">Select level</option>
              {[100, 200, 300, 400, 500].map((l) => <option key={l} value={l}>{l} Level</option>)}
            </select>
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Deadline Date</label>
          <input type="date" className="form-input" value={form.deadline_date} onChange={(e) => setForm({ ...form, deadline_date: e.target.value })} required />
        </div>

        <div className="form-group">
          <label className="form-label">Late Fee Amount (₦)</label>
          <input type="number" className="form-input" value={form.late_fee_amount} onChange={(e) => setForm({ ...form, late_fee_amount: parseFloat(e.target.value) })} min="0" step="100" required />
        </div>

        <button type="submit" className="btn btn-primary">Set Deadline</button>
      </form>

      {loading ? (
        <div className="card text-center" style={{ padding: '3rem' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : (
        <div className="card">
          <div className="card-header"><h3>Active Deadlines</h3></div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr><th>Document</th><th>Level</th><th>Deadline</th><th>Late Fee</th><th></th></tr>
              </thead>
              <tbody>
                {deadlines.length === 0 && (
                  <tr><td colSpan={5} className="text-center" style={{ padding: '2rem', color: 'var(--cul-gray-500)' }}>No deadlines set.</td></tr>
                )}
                {deadlines.map((d) => (
                  <tr key={d.id}>
                    <td style={{ textTransform: 'capitalize' }}>{d.document_type.replace(/_/g, ' ')}</td>
                    <td>{d.level || '-'}</td>
                    <td>{new Date(d.deadline_date).toLocaleDateString()}</td>
                    <td>₦{d.late_fee_amount.toLocaleString()}</td>
                    <td>
                      <button className="btn btn-sm btn-danger" onClick={() => handleDelete(d.id)}>Remove</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function MissingDocsPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getMissingDocuments()
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>Missing Documents Report</h1>
        <p>Students with incomplete document records</p>
      </div>

      {loading ? (
        <div className="card text-center" style={{ padding: '3rem' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Matric No</th>
                  <th>Name</th>
                  <th>Level</th>
                  <th>Missing Documents</th>
                </tr>
              </thead>
              <tbody>
                {data.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center" style={{ padding: '2rem', color: 'var(--cul-gray-500)' }}>
                      No missing documents — all students are complete!
                    </td>
                  </tr>
                )}
                {data.map((row) => (
                  <tr key={row.student_id}>
                    <td style={{ fontWeight: 600 }}>{row.matric_number}</td>
                    <td>{row.name}</td>
                    <td>{row.current_level}L</td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                        {row.missing_docs.map((doc) => (
                          <span key={doc} className="badge badge-red" style={{ textTransform: 'capitalize' }}>
                            {doc.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getAuditLogs()
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>Audit Logs</h1>
        <p>Immutable record of all system actions</p>
      </div>

      {loading ? (
        <div className="card text-center" style={{ padding: '3rem' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Table</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center" style={{ padding: '2rem', color: 'var(--cul-gray-500)' }}>
                      No audit logs found
                    </td>
                  </tr>
                )}
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.875rem', color: 'var(--cul-gray-500)' }}>
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td>{log.username}</td>
                    <td>
                      <span className={`badge badge-${log.action === 'DELETE' ? 'red' : log.action === 'UPLOAD' ? 'blue' : 'green'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td>{log.table_name}</td>
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function StaffDashboard() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main">
          <div className="container" style={{ maxWidth: '100%', padding: 0 }}>
            <Routes>
              <Route path="/" element={<DashboardHome />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/missing" element={<MissingDocsPage />} />
              <Route path="/deadlines" element={<DocumentDeadlinesPage />} />
              <Route path="/audit" element={<AuditPage />} />
            </Routes>
           </div>
        </main>
      </div>
    </div>
  );
}
