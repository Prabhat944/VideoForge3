import { createContext, useContext, useEffect, useState } from "react";
import api from "./api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => {
        const raw = localStorage.getItem("vf_user");
        return raw ? JSON.parse(raw) : null;
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("vf_token");
        if (token && !user) {
            api.get("/auth/me").then((r) => {
                setUser(r.data);
                localStorage.setItem("vf_user", JSON.stringify(r.data));
            }).catch(() => {});
        }
    }, []);

    const login = async (email, password) => {
        setLoading(true);
        try {
            const r = await api.post("/auth/login", { email, password });
            localStorage.setItem("vf_token", r.data.token);
            localStorage.setItem("vf_user", JSON.stringify(r.data.user));
            setUser(r.data.user);
            return r.data.user;
        } finally { setLoading(false); }
    };

    const register = async (email, password, full_name) => {
        setLoading(true);
        try {
            const r = await api.post("/auth/register", { email, password, full_name });
            localStorage.setItem("vf_token", r.data.token);
            localStorage.setItem("vf_user", JSON.stringify(r.data.user));
            setUser(r.data.user);
            return r.data.user;
        } finally { setLoading(false); }
    };

    const logout = () => {
        localStorage.removeItem("vf_token");
        localStorage.removeItem("vf_user");
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
