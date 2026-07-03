import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../services/api';

export default function StudentSearch({ onSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showResults, setShowResults] = useState(false);
  const wrapperRef = useRef(null);
  const debounceRef = useRef(null);

  const performSearch = useCallback(async (q) => {
    if (!q.trim()) {
      setResults([]);
      setShowResults(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api.searchStudents(q.trim());
      setResults(data);
      setShowResults(true);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      performSearch(query);
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [query, performSearch]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (student) => {
    onSelect(student);
    setQuery(`${student.matric_number} - ${student.first_name} ${student.last_name}`);
    setShowResults(false);
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div className="search-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Start typing matric number or name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim() && results.length > 0 && setShowResults(true)}
          autoComplete="off"
        />
        {loading && <div className="spinner" style={{ marginLeft: '0.5rem' }} />}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {showResults && (
        <div
          className="card"
          style={{
            position: 'absolute',
            top: 'calc(100% + 0.5rem)',
            left: 0,
            right: 0,
            zIndex: 20,
            maxHeight: '320px',
            overflowY: 'auto',
            padding: 0,
          }}
        >
          {results.length > 0 ? (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {results.map((s) => (
                <li
                  key={s.id}
                  style={{
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid var(--cul-gray-200)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '1rem',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--cul-gray-50)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <div onClick={() => handleSelect(s)} style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: 'var(--cul-green)' }}>{s.matric_number}</div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--cul-gray-600)' }}>
                      {s.first_name} {s.last_name} &middot; {s.department?.name || '-'} &middot; {s.current_level}L
                    </div>
                  </div>
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={(e) => { e.stopPropagation(); handleSelect(s); }}
                  >
                    View
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center" style={{ padding: '1.5rem', color: 'var(--cul-gray-500)' }}>
              No students found matching &quot;{query}&quot;
            </div>
          )}
        </div>
      )}
    </div>
  );
}
