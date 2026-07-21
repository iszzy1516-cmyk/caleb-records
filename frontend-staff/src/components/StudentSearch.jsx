import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function StudentSearch({ onSelect }) {
  const { isAdmin, isRegistrar, isDean, isHod, isRecordsOfficer, isLecturer, collegeId, departmentId } = useAuth();
  const isGlobal = isAdmin || isRegistrar;
  const isDeptScoped = isHod || isRecordsOfficer || isLecturer;

  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    college_id: isGlobal ? '' : '',
    department_id: isGlobal || isDean ? '' : (departmentId || ''),
    session: '',
  });

  const [colleges, setColleges] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showResults, setShowResults] = useState(false);

  const wrapperRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    api.getColleges().then(setColleges).catch(() => {});
  }, []);

  useEffect(() => {
    const deptCollegeId = isGlobal ? filters.college_id : collegeId;
    if (deptCollegeId) {
      api.getDepartments(deptCollegeId).then(setDepartments).catch(() => {});
    } else {
      setDepartments([]);
    }
    if (isGlobal) {
      setFilters((f) => ({ ...f, department_id: '' }));
    }
  }, [filters.college_id, collegeId, isGlobal]);

  const performSearch = useCallback(async (q, activeFilters) => {
    const hasQuery = q.trim().length > 0;
    const hasFilters = activeFilters && (
      activeFilters.college_id || activeFilters.department_id || activeFilters.session
    );
    if (!hasQuery && !hasFilters) {
      setResults([]);
      setShowResults(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api.searchStudents({ q: q.trim(), ...activeFilters });
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
      performSearch(query, filters);
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [query, filters, performSearch]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const updateFilter = (name, value) => {
    setFilters((f) => ({ ...f, [name]: value }));
  };

  const handleSelect = (student) => {
    onSelect(student);
    setQuery(`${student.matric_number} - ${student.first_name} ${student.last_name}`);
    setShowResults(false);
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <div className="card" style={{ padding: '1rem' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Search by matric number or student name</label>
          <div className="search-bar">
            <input
              type="text"
              className="form-input"
              placeholder="e.g. 22/1220 or John Doe"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => query.trim() && results.length > 0 && setShowResults(true)}
              autoComplete="off"
              style={{ fontSize: '1rem', padding: '0.75rem 1rem' }}
            />
            {loading && <div className="spinner" style={{ marginLeft: '0.5rem' }} />}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '1rem',
            marginTop: '1rem',
          }}
        >
          {isGlobal && (
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">College</label>
              <select
                className="form-select"
                value={filters.college_id}
                onChange={(e) => updateFilter('college_id', e.target.value)}
              >
                <option value="">All Colleges</option>
                {colleges.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          )}

          {(isGlobal || isDean) && !isDeptScoped && (
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Department</label>
              <select
                className="form-select"
                value={filters.department_id}
                onChange={(e) => updateFilter('department_id', e.target.value)}
              >
                <option value="">All Departments</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          )}

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Session</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. 2023/2024"
              value={filters.session}
              onChange={(e) => updateFilter('session', e.target.value)}
            />
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginTop: '1rem' }}>{error}</div>}

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
