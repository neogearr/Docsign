import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth.jsx';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import SignDocument from './components/Signature/SignDocument';
import SignatureList from './components/Signature/SignatureList';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            <Route path="/sign/:token" element={<SignDocument />} />
            
            {/* Protected routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="documents" element={<div className="p-6">Documentos - Em desenvolvimento</div>} />
              <Route path="templates" element={<div className="p-6">Templates - Em desenvolvimento</div>} />
              <Route path="clients" element={<div className="p-6">Clientes - Em desenvolvimento</div>} />
              <Route path="signatures" element={<SignatureList />} />
              <Route path="users" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <div className="p-6">Usuários - Em desenvolvimento</div>
                </ProtectedRoute>
              } />
              <Route path="settings" element={<div className="p-6">Configurações - Em desenvolvimento</div>} />
            </Route>
            
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
