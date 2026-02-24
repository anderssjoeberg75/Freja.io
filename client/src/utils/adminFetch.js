const ADMIN_TOKEN_KEY = "freja_admin_token";

export const getAdminToken = () => {
    try {
        return localStorage.getItem(ADMIN_TOKEN_KEY) || "";
    } catch (e) {
        return "";
    }
};

export const setAdminToken = (token) => {
    try {
        if (token) {
            localStorage.setItem(ADMIN_TOKEN_KEY, token);
        } else {
            localStorage.removeItem(ADMIN_TOKEN_KEY);
        }
    } catch (e) {
        // Ignore storage failures
    }
};

export const adminFetch = (url, options = {}) => {
    const token = getAdminToken();
    const headers = {
        ...(options.headers || {}),
    };
    if (token) {
        headers["X-Admin-Token"] = token;
    }
    return fetch(url, { ...options, headers });
};
