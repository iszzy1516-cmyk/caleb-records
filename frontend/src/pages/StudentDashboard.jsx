import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function StudentDashboard() {
  const { user, logout } = useAuth();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('documents');
  const [alerts, setAlerts] = useState([]);
  const [deadlines, setDeadlines] = useState([]);
  const [paying, setPaying] = useState(false);

  const [uploadForm, setUploadForm] = useState({
    document_type: '',
    level: '',
    file: null,
  });

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [meData, alertsData, deadlinesData] = await Promise.all([
        api.getMe(),
        api.getMyAlerts(),
        api.getDocumentDeadlines(),
      ]);
      setStudent(meData);
      setAlerts(alertsData);
      setDeadlines(deadlinesData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getDoc = (type, level = null) => {
    if (!student?.documents) return null;
    return student.documents.find((d) => d.document_type === type && (level === null || d.level === level));
  };

  const docTypes = [
    { key: 'jamb_result', label: 'JAMB Result' },
    { key: 'waec_result', label: 'WAEC/NECO Result' },
    { key: 'jamb_admission_letter', label: 'JAMB Admission Letter' },
    { key: 'birth_certificate', label: 'Birth Certificate' },
    { key: 'passport_photo', label: 'Passport Photo' },
    { key: 'medical', label: 'Medical Report' },
  ];

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.file) {
      setError('Please select a file');
      return;
    }
    setUploading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('document_type', uploadForm.document_type);
    formData.append('file', uploadForm.file);
    if (uploadForm.document_type === 'clearance_cert' && uploadForm.level) {
      formData.append('level', uploadForm.level);
    }

    try {
      await api.uploadMyDocument(formData);
      setSuccess('Document uploaded successfully!');
      setUploadForm({ document_type: '', level: '', file: null });
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="portal-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div className="text-center">
          <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto' }} />
          <p style={{ marginTop: '1rem', color: 'var(--cul-gray-500)' }}>Loading your records...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="portal-page">
      {/* Navbar */}
      <nav className="navbar">
        <div className="container navbar-inner">
          <div className="navbar-brand">
            <img src="/caleb-logo.jpg" alt="CUL" />
            <span>CU-Records Student</span>
          </div>
          <ul className="navbar-nav">
            <li>
              <span style={{ opacity: 0.9, fontSize: '0.875rem' }}>
                {user?.full_name}
              </span>
            </li>
            <li>
              <span className="badge" style={{ background: 'rgba(255,255,255,0.2)', color: '#fff' }}>
                {user?.matric_number}
              </span>
            </li>
            <li>
              <button onClick={() => window.location.href = '/settings'} style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.3)', color: '#fff' }}>⚙️</button>
            </li>
            <li>
              <button onClick={logout}>Logout</button>
            </li>
          </ul>
        </div>
      </nav>

      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '2rem', maxWidth: '900px' }}>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Alerts */}
        {alerts.filter((a) => !a.is_read).length > 0 && (
          <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--cul-danger)' }}>
            <div className="card-header">
              <h3>🔔 Notifications ({alerts.filter((a) => !a.is_read).length} unread)</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {alerts.filter((a) => !a.is_read).slice(0, 3).map((alert) => (
                <div key={alert.id} style={{ padding: '0.75rem', background: 'var(--cul-danger-light)', borderRadius: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ fontSize: '0.875rem' }}>{alert.message}</span>
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={async (e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      try {
                        await api.markAlertRead(alert.id);
                        setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, is_read: true } : a)));
                      } catch (err) {
                        setError(err.message || 'Failed to dismiss alert');
                      }
                    }}
                  >
                    Dismiss
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Profile Card */}
        {student && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'var(--cul-green-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: 'var(--cul-green)',
                  flexShrink: 0,
                }}
              >
                {student.first_name?.[0]}{student.last_name?.[0]}
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ margin: 0 }}>{student.first_name} {student.last_name}</h2>
                <p style={{ margin: '0.25rem 0 0', color: 'var(--cul-gray-500)' }}>
                  {student.matric_number} &middot; {student.program?.name} &middot; {student.current_level} Level
                </p>
              </div>
              <span className="badge badge-green">Active</span>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs">
          <button className={`tab ${activeTab === 'documents' ? 'active' : ''}`} onClick={() => setActiveTab('documents')}>
            My Documents
          </button>
          <button className={`tab ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>
            Upload Document
          </button>

        </div>

        {/* Documents Tab */}
        {activeTab === 'documents' && student && (
          <>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <h3>Admission Documents</h3>
              </div>
              <div className="doc-checklist">
                {docTypes.map((dt) => {
                  const doc = getDoc(dt.key);
                  return (
                    <div key={dt.key} className={`doc-checklist-item ${doc ? 'present' : 'missing'}`}>
                      <div className="doc-icon">{doc ? '✓' : '✗'}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{dt.label}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)' }}>
                          {doc ? `Uploaded ${new Date(doc.created_at).toLocaleDateString()}` : 'Not uploaded'}
                        </div>
                      </div>
                      {doc && (
                        <a
                          href={api.downloadDocument(doc.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-sm btn-outline"
                          style={{ flexShrink: 0 }}
                        >
                          Download
                        </a>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Clearance Certificates</h3>
              </div>
              <div className="doc-checklist">
                {[100, 200, 300, 400, 500].map((lvl) => {
                  const doc = getDoc('clearance_cert', lvl);
                  return (
                    <div key={lvl} className={`doc-checklist-item ${doc ? 'present' : 'missing'}`}>
                      <div className="doc-icon">{doc ? '✓' : '✗'}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{lvl} Level Clearance</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)' }}>
                          {doc ? `Uploaded ${new Date(doc.created_at).toLocaleDateString()}` : 'Not uploaded'}
                        </div>
                      </div>
                      {doc && (
                        <a
                          href={api.downloadDocument(doc.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-sm btn-outline"
                          style={{ flexShrink: 0 }}
                        >
                          Download
                        </a>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div className="card-header">
              <h3>Upload Document</h3>
            </div>

            {/* Late fee warning */}
            {(() => {
              if (!uploadForm.document_type) return null;
              const dl = deadlines.find((d) => d.document_type === uploadForm.document_type && (d.level == (uploadForm.level || null)));
              if (!dl) return null;
              const isLate = new Date() > new Date(dl.deadline_date);
              const hasDoc = getDoc(uploadForm.document_type, uploadForm.level || null);
              if (!isLate || hasDoc) return null;
              const paid = student?.payments?.some((p) => p.payment_type === `late_fee_${uploadForm.document_type}_${uploadForm.level || 'none'}`);
              if (paid) return (
                <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                  Late fee of ₦{dl.late_fee_amount.toLocaleString()} has been paid. You may upload now.
                </div>
              );
              return (
                <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                  <strong>Deadline Passed!</strong> The deadline for this document was {new Date(dl.deadline_date).toLocaleDateString()}.
                  A late fee of <strong>₦{dl.late_fee_amount.toLocaleString()}</strong> must be paid before uploading.
                  <button
                    type="button"
                    className="btn btn-sm btn-danger"
                    style={{ marginLeft: '1rem' }}
                    onClick={async () => {
                      setPaying(true);
                      try {
                        await api.makePayment({
                          amount: dl.late_fee_amount,
                          payment_type: `late_fee_${uploadForm.document_type}_${uploadForm.level || 'none'}`,
                          reference: `LATE-${Date.now()}`,
                        });
                        setSuccess('Late fee paid successfully!');
                        loadData();
                      } catch (err) {
                        setError(err.message);
                      } finally {
                        setPaying(false);
                      }
                    }}
                    disabled={paying}
                  >
                    {paying ? 'Processing...' : `Pay ₦${dl.late_fee_amount.toLocaleString()}`}
                  </button>
                </div>
              );
            })()}

            <form onSubmit={handleUpload}>
              <div className="form-group">
                <label className="form-label">Document Type</label>
                <select
                  className="form-select"
                  value={uploadForm.document_type}
                  onChange={(e) => setUploadForm({ ...uploadForm, document_type: e.target.value, level: '' })}
                  required
                >
                  <option value="">Select document type</option>
                  {docTypes.map((dt) => (
                    <option key={dt.key} value={dt.key}>{dt.label}</option>
                  ))}
                  <option value="clearance_cert">Clearance Certificate</option>
                  <option value="fee_receipt">Fee Receipt</option>
                  <option value="transcript">Transcript</option>
                </select>
              </div>

              {uploadForm.document_type === 'clearance_cert' && (
                <div className="form-group">
                  <label className="form-label">Level</label>
                  <select
                    className="form-select"
                    value={uploadForm.level}
                    onChange={(e) => setUploadForm({ ...uploadForm, level: e.target.value })}
                    required
                  >
                    <option value="">Select level</option>
                    {[100, 200, 300, 400, 500].map((l) => (
                      <option key={l} value={l}>{l} Level</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">File (PDF, JPG, PNG — max 10MB)</label>
                <input
                  type="file"
                  className="form-input"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files[0] })}
                  required
                />
                {uploadForm.file && (
                  <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                    Selected: {uploadForm.file.name}
                  </p>
                )}
              </div>

              <button type="submit" className="btn btn-primary w-full" disabled={uploading}>
                {uploading ? 'Uploading...' : 'Upload Document'}
              </button>
            </form>
          </div>
        )}

      </div>

      {/* Footer */}
      <footer style={{ marginTop: 'auto', padding: '1.5rem', textAlign: 'center', borderTop: '1px solid var(--cul-gray-200)', background: 'var(--cul-white)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--cul-gray-500)', margin: 0 }}>
          Caleb University, Imota, Lagos &middot; For God and Humanity
        </p>
      </footer>
    </div>
  );
}
