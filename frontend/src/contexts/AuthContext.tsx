import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { auth } from '../services/api';
import { AuthContextType, User, LoginCredentials, SignupData } from '../types';

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      auth.getCurrentUser()
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('token');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    const response = await auth.login(credentials);
    localStorage.setItem('token', response.data.access_token);
    const userResponse = await auth.getCurrentUser();
    setUser(userResponse.data);
    return userResponse.data;
  };

  const signup = async (userData: SignupData): Promise<void> => {
    await auth.signup(userData);
  };

  const logout = (): void => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext; 