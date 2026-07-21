import { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('cul_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('cul_token') || null);
  const [tokenType, setTokenType] = useState(() => localStorage.getItem('cul_token_type') || null);

  const login = useCallback((tokenValue, userData, type = 'staff') => {
    localStorage.setItem('cul_token', tokenValue);
    localStorage.setItem('cul_token_type', type);
    localStorage.setItem('cul_user', JSON.stringify(userData));
    setToken(tokenValue);
    setTokenType(type);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('cul_token');
    localStorage.removeItem('cul_token_type');
    localStorage.removeItem('cul_user');
    setToken(null);
    setTokenType(null);
    setUser(null);
  }, []);

  const isAuthenticated = !!token;
  const isStaff = tokenType === 'staff';
  const isStudent = tokenType === 'student';
  const isAdmin = isStaff && (user?.role === 'admin' || user?.role === 'registrar');
  const isRegistrar = isStaff && user?.role === 'registrar';
  const isDean = isStaff && (user?.role === 'dean' || isAdmin);
  const isRecordsOfficer = isStaff && (user?.role === 'records_officer' || isAdmin);
  const isLecturer = isStaff && (user?.role === 'lecturer' || isAdmin);
  const isHod = isStaff && (user?.role === 'hod' || isAdmin);
  const isBursar = isStaff && (user?.role === 'bursar' || isAdmin);
  const collegeId = isStaff ? user?.college_id : null;
  const collegeName = isStaff ? user?.college_name : null;
  const departmentId = isStaff ? user?.department_id : null;
  const departmentName = isStaff ? user?.department_name : null;

  const value = {
    user,
    token,
    tokenType,
    login,
    logout,
    isAuthenticated,
    isStaff,
    isStudent,
    isAdmin,
    isRegistrar,
    isDean,
    isRecordsOfficer,
    isLecturer,
    isHod,
    isBursar,
    collegeId,
    collegeName,
    departmentId,
    departmentName,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
