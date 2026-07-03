import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const AuthContext = createContext(null);

function readStoredAuth() {
  try {
    const token = localStorage.getItem('cul_token') || null;
    const tokenType = localStorage.getItem('cul_token_type') || null;
    const userJson = localStorage.getItem('cul_user');
    const user = userJson ? JSON.parse(userJson) : null;
    return { token, tokenType, user };
  } catch {
    return { token: null, tokenType: null, user: null };
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => readStoredAuth());
  const [isReady, setIsReady] = useState(false);

  // Re-read localStorage after mount (catches cases where lazy init misses it)
  useEffect(() => {
    const stored = readStoredAuth();
    console.log('[AuthContext] mounted, stored auth:', stored);
    setAuth(stored);
    setIsReady(true);

    const handleStorage = (e) => {
      if (['cul_token', 'cul_token_type', 'cul_user'].includes(e.key)) {
        setAuth(readStoredAuth());
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const login = useCallback((tokenValue, userData, type = 'staff') => {
    console.log('[AuthContext] login called', { type });
    localStorage.setItem('cul_token', tokenValue);
    localStorage.setItem('cul_token_type', type);
    localStorage.setItem('cul_user', JSON.stringify(userData));
    setAuth({ token: tokenValue, tokenType: type, user: userData });
    console.log('[AuthContext] localStorage after login:', readStoredAuth());
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('cul_token');
    localStorage.removeItem('cul_token_type');
    localStorage.removeItem('cul_user');
    setAuth({ token: null, tokenType: null, user: null });
  }, []);

  const isAuthenticated = !!auth.token;
  const isStaff = auth.tokenType === 'staff';
  const isStudent = auth.tokenType === 'student';
  const isAdmin = isStaff && auth.user?.role === 'admin';
  const isRecordsOfficer = isStaff && (auth.user?.role === 'records_officer' || isAdmin);
  const isLecturer = isStaff && (auth.user?.role === 'lecturer' || isAdmin);
  const isHod = isStaff && (auth.user?.role === 'hod' || isAdmin);
  const isBursar = isStaff && (auth.user?.role === 'bursar' || isAdmin);

  const value = {
    user: auth.user,
    token: auth.token,
    tokenType: auth.tokenType,
    login,
    logout,
    isAuthenticated,
    isReady,
    isStaff,
    isStudent,
    isAdmin,
    isRecordsOfficer,
    isLecturer,
    isHod,
    isBursar,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
