/**
 * VAlert API Client
 * Handles all API calls to the FastAPI backend
 */

// API Base URL - change for production
const API_BASE = import.meta.env.VITE_API_URL || 'https://valert-api.up.railway.app';

// Get Telegram WebApp instance
const tg = window.Telegram?.WebApp;

/**
 * Make API request with Telegram auth
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Add Telegram initData for authentication
    if (tg?.initData) {
        headers['X-Telegram-Init-Data'] = tg.initData;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
}

/**
 * Get all current exchange rates
 */
export async function fetchRates() {
    return apiRequest('/rates');
}

/**
 * Get single currency rate
 */
export async function fetchRate(currency) {
    return apiRequest(`/rates/${currency}`);
}

/**
 * Get historical rates for charts
 */
export async function fetchHistory(currency, days = 7) {
    return apiRequest(`/history/${currency}?days=${days}`);
}

/**
 * Get user's alerts
 */
export async function fetchAlerts() {
    return apiRequest('/alerts');
}

/**
 * Create new alert
 */
export async function createAlert(currency, direction, threshold) {
    return apiRequest('/alerts', {
        method: 'POST',
        body: JSON.stringify({ currency, direction, threshold }),
    });
}

/**
 * Delete alert
 */
export async function deleteAlert(alertId) {
    return apiRequest(`/alerts/${alertId}`, {
        method: 'DELETE',
    });
}

export default {
    fetchRates,
    fetchRate,
    fetchHistory,
    fetchAlerts,
    createAlert,
    deleteAlert,
};
