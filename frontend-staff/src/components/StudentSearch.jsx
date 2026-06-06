import { useState } from 'react';
import { api } from '../services/api';

export default function StudentSearch({ onSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.searchStudents(query);
      setResults(data);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSearch} className="search-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Search by matric number or name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? '...' : 'Search'}
        </button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {results.length > 0 && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Matric No</th>
                  <th>Name</th>
                  <th>Department</th>
                  <th>Level</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {results.map((s) => (
                  <tr key={s.id} style={{ cursor: 'pointer' }} onClick={() => onSelect(s)}>
                    <td style={{ fontWeight: 600, color: 'var(--cul-green)' }}>{s.matric_number}</td>
                    <td>{s.first_name} {s.last_name}</td>
                    <td>{s.department?.name || '-'}</td>
                    <td>{s.current_level}L</td>
                    <td>
                      <button className="btn btn-sm btn-outline" onClick={(e) => { e.stopPropagation(); onSelect(s); }}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && query && results.length === 0 && (
        <div className="card text-center" style={{ marginTop: '1rem', padding: '2rem', color: 'var(--cul-gray-500)' }}>
          No students found matching &quot;{query}&quot;
        </div>
      )}
    </div>
  );
}
