import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("vf_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

api.interceptors.response.use(
    (r) => r,
    (err) => {
        if (err?.response?.status === 401) {
            localStorage.removeItem("vf_token");
            localStorage.removeItem("vf_user");
        }
        return Promise.reject(err);
    }
);

/** Append auth token to media URLs so <img> tags can load auth-protected files. */
export function withAuth(url) {
    if (!url) return url;
    const token = localStorage.getItem("vf_token");
    if (!token) return url;
    return url + (url.includes("?") ? "&" : "?") + "token=" + encodeURIComponent(token);
}

export default api;
