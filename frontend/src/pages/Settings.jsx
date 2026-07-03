import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function Settings() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [darkMode, setDarkMode] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [changing, setChanging] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('cul_dark_mode') === 'true';
    setDarkMode(saved);
    document.documentElement.classList.toggle('dark', saved);
  }, []);

  const toggleDarkMode = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem('cul_dark_mode', String(next));
    document.documentElement.classList.toggle('dark', next);
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordMessage('');
    setPasswordError('');

    if (newPassword.length < 4) {
      setPasswordError('New password must be at least 4 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    setChanging(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      setPasswordMessage('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordError(err.message || 'Failed to change password');
    } finally {
      setChanging(false);
    }
  };

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
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <h2>⚙️ Settings</h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            {/* Appearance */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ marginBottom: '0.75rem' }}>Appearance</h4>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer',
                }}
              >
                <span>Dark mode</span>
                <input
                  type="checkbox"
                  checked={darkMode}
                  onChange={toggleDarkMode}
                  style={{ width: '1.25rem', height: '1.25rem', cursor: 'pointer' }}
                />
              </label>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '1.5rem 0' }} />

            {/* Change Password */}
            <div>
              <h4 style={{ marginBottom: '0.75rem' }}>Change Password</h4>
              <form onSubmit={handleChangePassword}>
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label className="form-label" htmlFor="currentPassword">Current Password</label>
                  <input
                    id="currentPassword"
                    type="password"
                    className="form-input"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                </div>

                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label className="form-label" htmlFor="newPassword">New Password</label>
                  <input
                    id="newPassword"
                    type="password"
                    className="form-input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={4}
                    autoComplete="new-password"
                  />
                </div>

                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label className="form-label" htmlFor="confirmPassword">Confirm New Password</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    className="form-input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                  />
                </div>

                {passwordError && (
                  <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                    {passwordError}
                  </div>
                )}
                {passwordMessage && (
                  <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                    {passwordMessage}
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={changing}
                >
                  {changing ? (
                    <>
                      <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px', display: 'inline-block', verticalAlign: 'middle', marginRight: '0.5rem' }} />
                      Changing...
                    </>
                  ) : (
                    'Change Password'
                  )}
                </button>
              </form>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '1.5rem 0' }} />

            {/* Session */}
            <div>
              <h4 style={{ marginBottom: '0.75rem' }}>Session</h4>
              <button
                onClick={logout}
                className="btn btn-outline"
                style={{ color: '#dc2626', borderColor: '#dc2626' }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
