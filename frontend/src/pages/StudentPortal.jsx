import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

export default function StudentPortal() {
  const [matric, setMatric] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [student, setStudent] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!matric.trim()) return;
    setLoading(true);
    setError('');
    setStudent(null);

    try {
      const data = await api.publicStudentLookup(matric.trim().toUpperCase());
      setStudent(data);
    } catch (err) {
      setError(err.message || 'Student not found. Please check your matric number.');
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

  const getDoc = (type, level = null) => {
    if (!student?.documents) return null;
    return student.documents.find((d) => d.document_type === type && (level === null || d.level === level));
  };

  const gradePoints = { A: 5, B: 4, C: 3, D: 2, E: 1, F: 0 };

  return (
    <div className="portal-page">
      {/* Hero Header */}
      <div className="portal-hero">
        <div className="container">
          <img src="/caleb-logo.jpg" alt="Caleb University Logo" />
          <h1>Caleb University</h1>
          <p>Student Self-Service Portal</p>
          <p style={{ fontSize: '0.875rem', fontStyle: 'italic', opacity: 0.8 }}>For God and Humanity</p>
        </div>
      </div>

      {/* Search Card */}
      <div className="portal-search">
        <div className="card">
          <form onSubmit={handleSearch} className="search-bar" style={{ marginBottom: 0 }}>
            <input
              type="text"
              className="form-input"
              placeholder="Enter your matric number (e.g. CUL/2024/0001)"
              value={matric}
              onChange={(e) => setMatric(e.target.value)}
              style={{ fontSize: '1rem' }}
              required
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
              ) : (
                'Lookup'
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Results */}
      <div className="portal-results">
        {error && <div className="alert alert-error">{error}</div>}

        {student && (
          <>
            {/* Profile Card */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
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
                  <div>
                    <h2 style={{ margin: 0 }}>{student.first_name} {student.last_name}</h2>
                    <p style={{ margin: '0.25rem 0 0', color: 'var(--cul-gray-500)' }}>
                      {student.matric_number} &middot; {student.program?.name} &middot; {student.current_level} Level
                    </p>
                  </div>
                </div>
                <span className="badge badge-green">Active</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem' }}>
                <div>
                  <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cul-gray-500)', marginBottom: '0.25rem' }}>Department</p>
                  <p style={{ fontWeight: 600, margin: 0 }}>{student.department?.name || '-'}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cul-gray-500)', marginBottom: '0.25rem' }}>College</p>
                  <p style={{ fontWeight: 600, margin: 0 }}>{student.college?.name || '-'}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cul-gray-500)', marginBottom: '0.25rem' }}>Admission Year</p>
                  <p style={{ fontWeight: 600, margin: 0 }}>{student.admission_year}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cul-gray-500)', marginBottom: '0.25rem' }}>Gender</p>
                  <p style={{ fontWeight: 600, margin: 0, textTransform: 'capitalize' }}>{student.gender}</p>
                </div>
              </div>
            </div>

            {/* Documents */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <h3>Documents</h3>
              </div>

              <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9375rem', color: 'var(--cul-gray-700)' }}>Admission Documents</h4>
              <div className="doc-checklist" style={{ marginBottom: '1.5rem' }}>
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
                        <button
                          onClick={() => api.downloadDocument(doc.id, doc.original_filename).catch((err) => alert(err.message))}
                          className="btn btn-sm btn-outline"
                          style={{ flexShrink: 0 }}
                        >
                          Download
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9375rem', color: 'var(--cul-gray-700)' }}>Clearance Certificates</h4>
              <div className="doc-checklist">
                {Array.from(
                  { length: student.program?.duration_years || 4 },
                  (_, i) => (i + 1) * 100
                ).map((lvl) => {
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
                        <button
                          onClick={() => api.downloadDocument(doc.id, doc.original_filename).catch((err) => alert(err.message))}
                          className="btn btn-sm btn-outline"
                          style={{ flexShrink: 0 }}
                        >
                          Download
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Academic Records */}
            {student.academic_records && student.academic_records.length > 0 && (
              <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div className="card-header">
                  <h3>Academic Records</h3>
                  {student.cgpa !== undefined && (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cul-green)' }}>{student.cgpa.toFixed(2)}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--cul-gray-500)' }}>CGPA</div>
                    </div>
                  )}
                </div>
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Course</th>
                        <th>Title</th>
                        <th>Units</th>
                        <th>Grade</th>
                        <th>Session</th>
                        <th>Semester</th>
                      </tr>
                    </thead>
                    <tbody>
                      {student.academic_records.map((rec) => (
                        <tr key={rec.id}>
                          <td style={{ fontWeight: 600 }}>{rec.course?.code}</td>
                          <td>{rec.course?.title}</td>
                          <td>{rec.course?.credit_units}</td>
                          <td>
                            <span className={`badge badge-${gradePoints[rec.grade] >= 3 ? 'green' : gradePoints[rec.grade] >= 2 ? 'yellow' : 'red'}`}>
                              {rec.grade}
                            </span>
                          </td>
                          <td>{rec.session}</td>
                          <td>{rec.semester}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {!student && !loading && !error && (
          <div className="card text-center" style={{ padding: '3rem', color: 'var(--cul-gray-500)' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎓</div>
            <h3 style={{ marginBottom: '0.5rem' }}>Welcome to the Student Portal</h3>
            <p>Enter your matric number above to view your records, documents, and grades.</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer style={{ marginTop: 'auto', padding: '1.5rem', textAlign: 'center', borderTop: '1px solid var(--cul-gray-200)', background: 'var(--cul-white)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--cul-gray-500)', margin: 0 }}>
          Caleb University, Imota, Lagos &middot; For God and Humanity
        </p>
        <Link to="/" style={{ fontSize: '0.8125rem', marginTop: '0.5rem', display: 'inline-block' }}>
          Staff Login
        </Link>
      </footer>
    </div>
  );
}
