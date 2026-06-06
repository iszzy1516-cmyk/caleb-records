
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function StudentLogin() {
  const [matric, setMatric] = useState('');
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
      const data = await api.studentLogin(matric.trim().toUpperCase(), password);
      login(
        data.access_token,
        { matric_number: data.matric_number, full_name: data.full_name },
        'student'
      );
      navigate('/student-dashboard');
    } catch (err) {
      setError(err.message || 'Invalid matric number or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <img src="/caleb-logo.jpg" alt="Caleb University Logo" />
          <h1>CU-Records</h1>
          <span>Student Portal — Caleb University</span>
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
            <label className="form-label" htmlFor="matric">Matric Number</label>
            <input
              id="matric"
              type="text"
              className="form-input"
              placeholder="e.g. CUL/2024/0001"
              value={matric}
              onChange={(e) => setMatric(e.target.value)}
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

        <div style={{ marginTop: '1.5rem', textAlign: 'center', display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <Link to="/forgot-password" style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            Forgot Password?
          </Link>
          <Link to="/register" style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            Register
          </Link>
        </div>

        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--cul-gray-200)', textAlign: 'center' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', margin: 0 }}>
            Default password is usually <strong>Caleb{String(new Date().getFullYear()).slice(-2)}</strong> unless changed by staff.
          </p>
        </div>
      </div>
    </div>
  );
}
