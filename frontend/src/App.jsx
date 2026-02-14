import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Layout from "./components/Layout";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" />;
  return children;
};

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path="trades" element={<div className="text-center mt-20 text-gray-500">Trades Coming Soon</div>} />
              <Route path="calendar" element={<div className="text-center mt-20 text-gray-500">Calendar Coming Soon</div>} />
              <Route path="settings" element={<div className="text-center mt-20 text-gray-500">Settings Coming Soon</div>} />
              <Route path="account" element={<div className="text-center mt-20 text-gray-500">Account Coming Soon</div>} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
