import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

export default function ForgotPassword() {
  const [matric, setMatric] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const res = await api.requestPasswordReset(matric.trim().toUpperCase());
      setMessage(res.message);
      setMatric('');
    } catch (err) {
      setError(err.message);
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
          <span>Password Reset</span>
        </div>

        {message && (
          <div className="alert alert-success" style={{ marginBottom: '1.25rem' }}>
            {message}
          </div>
        )}

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
              placeholder="e.g. 24/00001"
              value={matric}
              onChange={(e) => setMatric(e.target.value)}
              required
              autoFocus
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={loading}
            style={{ marginTop: '0.5rem' }}
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <Link to="/register" style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            Register
          </Link>
          <Link to="/" style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
