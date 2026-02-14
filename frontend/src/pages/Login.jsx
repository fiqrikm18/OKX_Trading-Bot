import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const success = await login(username, password);
        if (success) {
            navigate("/");
        } else {
            setError("Invalid credentials");
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-background text-white">
            <div className="w-full max-w-md p-8 bg-surface rounded-xl border border-border shadow-2xl">
                <h2 className="text-3xl font-bold text-center mb-6">🔐 Login</h2>
                {error && <p className="text-error text-center mb-4">{error}</p>}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full p-3 bg-background border border-border rounded-lg focus:outline-none focus:border-primary"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full p-3 bg-background border border-border rounded-lg focus:outline-none focus:border-primary"
                        />
                    </div>
                    <button
                        type="submit"
                        className="w-full py-3 bg-primary hover:bg-blue-600 rounded-lg font-bold transition-colors"
                    >
                        Sign In
                    </button>
                </form>
            </div>
        </div>
    );
}
