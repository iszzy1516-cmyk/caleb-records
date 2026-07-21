import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loginData, setLoginData] = useState(null);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.login(email, password);
      const user = {
        email: data.email,
        username: data.username,
        role: data.role,
        full_name: data.full_name,
        college_id: data.college_id,
        college_name: data.college_name,
        department_id: data.department_id,
        department_name: data.department_name,
      };
      if (data.force_password_change) {
        setLoginData({ token: data.access_token, user });
        setShowPasswordChange(true);
        setPasswordForm({ current_password: password, new_password: '', confirm_password: '' });
      } else {
        login(data.access_token, user, 'staff');
        navigate('/staff');
      }
    } catch (err) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('New passwords do not match');
      return;
    }
    if (passwordForm.new_password.length < 4) {
      setError('New password must be at least 4 characters');
      return;
    }
    setPasswordLoading(true);
    try {
      await api.changeStaffPassword(
        {
          current_password: passwordForm.current_password,
          new_password: passwordForm.new_password,
        },
        loginData.token
      );
      const updatedUser = { ...loginData.user, force_password_change: false };
      login(loginData.token, updatedUser, 'staff');
      navigate('/staff');
    } catch (err) {
      setError(err.message || 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };

  if (showPasswordChange) {
    if (!loginData) {
      // Defensive: reset to login form if state is lost
      setShowPasswordChange(false);
      return null;
    }
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="login-logo">
            <img src={`${import.meta.env.BASE_URL}caleb-logo.jpg`} alt="Caleb University Logo" />
            <h1>CU-Records</h1>
            <span>Change Your Password</span>
          </div>

          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
              {error}
            </div>
          )}

          <p style={{ fontSize: '0.875rem', color: 'var(--cul-gray-600)', marginBottom: '1rem' }}>
            Your account requires a password change before you can access the dashboard.
          </p>

          <form onSubmit={handlePasswordChange}>
            <div className="form-group">
              <label className="form-label" htmlFor="current_password">Current Password</label>
              <input
                id="current_password"
                type="password"
                className="form-input"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="new_password">New Password</label>
              <input
                id="new_password"
                type="password"
                className="form-input"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="confirm_password">Confirm New Password</label>
              <input
                id="confirm_password"
                type="password"
                className="form-input"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary w-full" disabled={passwordLoading}>
              {passwordLoading ? (
                <>
                  <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                  Updating...
                </>
              ) : (
                'Update Password'
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <img src={`${import.meta.env.BASE_URL}caleb-logo.jpg`} alt="Caleb University Logo" />
          <h1>CU-Records</h1>
          <span>Staff Portal — Caleb University</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', marginTop: '0.5rem', fontStyle: 'italic' }}>
            For God and Humanity
          </span>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="e.g. staff@calebuniversity.edu.ng"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={loading}
            style={{ marginTop: '0.5rem' }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--cul-gray-200)', textAlign: 'center' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', margin: 0 }}>
            Staff only. Unauthorized access is prohibited.
          </p>
        </div>
      </div>
    </div>
  );
}
