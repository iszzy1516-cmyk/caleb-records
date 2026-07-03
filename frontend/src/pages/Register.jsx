import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

export default function Register() {
  const [form, setForm] = useState({
    matric_number: '', first_name: '', last_name: '', email: '', phone: '',
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
      const data = await api.registerStudent(form);
      setSuccess(
        `Registration successful! Your matric number is ${data.matric_number} and your default password is ${data.default_password}. Please save these details.`
      );
      setForm({
        matric_number: '', first_name: '', last_name: '', email: '', phone: '',
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

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: '600px' }}>
        <div className="login-logo">
          <img src="/caleb-logo.jpg" alt="Caleb University Logo" />
          <h1>CUL-Records</h1>
          <span>Student Self-Registration</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--cul-gray-400)', marginTop: '0.5rem', fontStyle: 'italic' }}>
            For God and Humanity
          </span>
        </div>

        {success && (
          <div className="alert alert-success" style={{ marginBottom: '1.25rem' }}>
            {success}
          </div>
        )}

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Matric Number</label>
            <input name="matric_number" className="form-input" value={form.matric_number} onChange={handleChange} required placeholder="e.g. 22/11220" />
          </div>

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
              <input name="email" type="email" className="form-input" value={form.email} onChange={handleChange} required />
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

          <button type="submit" className="btn btn-primary w-full" disabled={loading} style={{ marginTop: '0.5rem' }}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <Link to="/" style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            Student Login
          </Link>
        </div>
      </div>
    </div>
  );
}
