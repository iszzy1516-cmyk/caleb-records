import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

export default function StaffRegister() {
  const [step, setStep] = useState('form'); // 'form' | 'otp' | 'success'
  const [form, setForm] = useState({
    username: '',
    full_name: '',
    email: '',
    phone: '',
    department: '',
    password: '',
  });
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleRequest = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await api.requestStaffRegistration(form);
      setStep('otp');
      setSuccess('A verification code has been sent to the email address.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await api.verifyStaffRegistration({ email: form.email, otp });
      setStep('success');
      setSuccess(`Staff account created successfully! Username: ${data.username}, Email: ${data.email}`);
      setForm({ username: '', full_name: '', email: '', phone: '', department: '', password: '' });
      setOtp('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep('form');
    setForm({ username: '', full_name: '', email: '', phone: '', department: '', password: '' });
    setOtp('');
    setError('');
    setSuccess('');
  };

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: '600px', width: '100%' }}>
        <div className="login-logo">
          <img src={`${import.meta.env.BASE_URL}caleb-logo.jpg`} alt="Caleb University Logo" />
          <h1>CU-Records</h1>
          <span>Staff Registration</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', marginTop: '0.5rem', fontStyle: 'italic' }}>
            For God and Humanity
          </span>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>{error}</div>}
        {success && <div className="alert alert-success" style={{ marginBottom: '1.25rem' }}>{success}</div>}

        {step === 'form' && (
          <form onSubmit={handleRequest}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input name="full_name" className="form-input" value={form.full_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label className="form-label">Username</label>
                <input name="username" className="form-input" value={form.username} onChange={handleChange} required placeholder="e.g. j.smith" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">School Email</label>
                <input name="email" type="email" className="form-input" value={form.email} onChange={handleChange} required placeholder="e.g. staff@calebuniversity.edu.ng" />
              </div>
              <div className="form-group">
                <label className="form-label">Phone Number</label>
                <input name="phone" className="form-input" value={form.phone} onChange={handleChange} placeholder="e.g. 08012345678" />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Department</label>
              <input name="department" className="form-input" value={form.department} onChange={handleChange} required placeholder="e.g. Computer Science" />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input name="password" type="password" className="form-input" value={form.password} onChange={handleChange} required minLength={6} />
            </div>

            <button type="submit" className="btn btn-primary w-full" disabled={loading}>
              {loading ? 'Sending code...' : 'Send Verification Code'}
            </button>
          </form>
        )}

        {step === 'otp' && (
          <form onSubmit={handleVerify}>
            <div className="form-group">
              <label className="form-label">Verification Code</label>
              <input
                type="text"
                className="form-input"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                placeholder="Enter 6-digit code from email"
                maxLength={6}
                autoComplete="one-time-code"
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', marginTop: '0.5rem' }}>
                A code was sent to {form.email}. It expires in 15 minutes.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="submit" className="btn btn-primary w-full" disabled={loading || otp.length !== 6}>
                {loading ? 'Verifying...' : 'Verify & Create Account'}
              </button>
              <button type="button" className="btn btn-outline" onClick={reset} disabled={loading}>
                Cancel
              </button>
            </div>
          </form>
        )}

        {step === 'success' && (
          <div className="text-center">
            <p style={{ marginBottom: '1.5rem' }}>
              The staff account has been created with the role <strong>Records Officer</strong>.
            </p>
            <button type="button" className="btn btn-primary w-full" onClick={reset}>
              Register Another Staff
            </button>
          </div>
        )}

        <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--cul-gray-200)', textAlign: 'center' }}>
          <p style={{ fontSize: '0.875rem', margin: 0 }}>
            Already have an account? <Link to="/">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
