import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to="/staff" className="navbar-brand">
          <img src="/caleb-logo.jpg" alt="CUL" />
          <span>CU-Records</span>
        </Link>

        <ul className="navbar-nav">
          <li>
            <span style={{ opacity: 0.9, fontSize: '0.875rem' }}>
              {user?.full_name || user?.username}
            </span>
          </li>
          <li>
            <span
              className="badge"
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: '#fff',
                textTransform: 'capitalize',
              }}
            >
              {user?.role?.replace('_', ' ')}
            </span>
          </li>
          <li>
            <button onClick={logout}>Logout</button>
          </li>
        </ul>
      </div>
    </nav>
  );
}
