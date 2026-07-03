import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.login(email, password);
      login(data.access_token, { email: data.email, username: data.username, role: data.role, full_name: data.full_name }, 'staff');
      navigate('/staff');
    } catch (err) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

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
          <p style={{ fontSize: '0.875rem', margin: '0 0 0.5rem' }}>
            New staff? <Link to="/register">Register here</Link>
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', margin: 0 }}>
            Staff only. Unauthorized access is prohibited.
          </p>
        </div>
      </div>
    </div>
  );
}
