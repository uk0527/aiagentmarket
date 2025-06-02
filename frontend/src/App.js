import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import Signup from './pages/Signup';
import Login from './pages/Login';
import AgentCart from './pages/AgentCart';
import Home from './pages/Home';
import Navigation from './components/Navigation';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <CartProvider>
          <Router>
            <Navigation />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/cart"
                element={
                  <ProtectedRoute>
                    <AgentCart />
                  </ProtectedRoute>
                }
              />
              {/* Add more routes as needed */}
            </Routes>
          </Router>
        </CartProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
