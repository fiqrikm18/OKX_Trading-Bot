import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem("token"));

    useEffect(() => {
        if (token) {
            axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
            setUser({ name: "Admin" }); // Simplification for now
        } else {
            delete axios.defaults.headers.common["Authorization"];
            setUser(null);
        }
    }, [token]);

    const login = async (username, password) => {
        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);

            const res = await axios.post("http://localhost:8000/auth/token", formData);
            const newToken = res.data.access_token;

            localStorage.setItem("token", newToken);
            setToken(newToken);
            return true;
        } catch (error) {
            console.error("Login failed", error);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem("token");
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
};
