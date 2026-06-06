import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const navigate = useNavigate();
  const [apiUrl, setApiUrl] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const savedUrl = localStorage.getItem('cul_api_url');
    setApiUrl(savedUrl || '');
  }, []);

  const handleSave = () => {
    if (apiUrl.trim()) {
      localStorage.setItem('cul_api_url', apiUrl.trim());
    } else {
      localStorage.removeItem('cul_api_url');
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    localStorage.removeItem('cul_api_url');
    setApiUrl('');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const isTauri = typeof window !== 'undefined' && !!window.__TAURI__;

  return (
    <div className="portal-page">
      <nav className="navbar">
        <div className="container navbar-inner">
          <div className="navbar-brand">
            <img src="/caleb-logo.jpg" alt="CUL" />
            <span>CU-Records Student</span>
          </div>
          <ul className="navbar-nav">
            <li>
              <button onClick={() => navigate('/student-dashboard')}>← Dashboard</button>
            </li>
          </ul>
        </div>
      </nav>

      <div className="container" style={{ paddingTop: '1.5rem', maxWidth: '600px' }}>
        <div className="card">
          <div className="card-header">
            <h2>⚙️ Settings</h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem' }}>
                Server URL
              </label>
              <input
                type="url"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="e.g. http://192.168.1.100:8000"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  fontSize: '1rem',
                }}
              />
              <small style={{ color: '#6b7280', display: 'block', marginTop: '0.5rem' }}>
                Leave empty to use the default server. You must restart the app after changing this.
              </small>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
              <button
                onClick={handleSave}
                style={{
                  background: '#00843D',
                  color: '#fff',
                  border: 'none',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Save
              </button>
              <button
                onClick={handleReset}
                style={{
                  background: '#e5e7eb',
                  color: '#374151',
                  border: 'none',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '8px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Reset to Default
              </button>
            </div>

            {saved && (
              <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                Settings saved! Please reload the app.
              </div>
            )}

            <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '1.5rem 0' }} />

            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>About</h4>
              <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>
                Caleb University Records — Student Mobile App
              </p>
              <p style={{ color: '#6b7280', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                Version 1.0.0
              </p>
              {isTauri && (
                <p style={{ color: '#00843D', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                  🚀 Running as native mobile app
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
