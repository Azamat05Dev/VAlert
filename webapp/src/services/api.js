/**
 * VAlert API Service
 * Handles all API calls to the backend with caching
 */

// API Base URL - use relative path for Vercel deployment
const API_BASE = '/api'

// Local cache for rates
let ratesCache = {
    data: null,
    timestamp: null,
    ttl: 60000 // 1 minute client-side cache
}

/**
 * Check if cache is valid
 */
const isCacheValid = () => {
    if (!ratesCache.data || !ratesCache.timestamp) return false
    return Date.now() - ratesCache.timestamp < ratesCache.ttl
}

/**
 * Fetch all rates from API
 * @param {boolean} forceRefresh - Force fetch from API
 * @returns {Promise<Array>} - Array of rate objects
 */
export const fetchRates = async (forceRefresh = false) => {
    // Return cached data if valid
    if (!forceRefresh && isCacheValid()) {
        return ratesCache.data
    }

    try {
        const response = await fetch(`${API_BASE}/rates`)

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        const data = await response.json()

        // Update cache
        ratesCache.data = data
        ratesCache.timestamp = Date.now()

        return data
    } catch (error) {
        console.error('Failed to fetch rates:', error)

        // Return cached data as fallback
        if (ratesCache.data) {
            return ratesCache.data
        }

        // Return null to indicate error
        return null
    }
}

/**
 * Fetch single currency rate
 * @param {string} currency - Currency code (e.g., "USD")
 * @returns {Promise<Object|null>} - Rate object or null
 */
export const fetchRate = async (currency) => {
    try {
        const response = await fetch(`${API_BASE}/rates/${currency}`)

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error(`Failed to fetch rate for ${currency}:`, error)
        return null
    }
}

/**
 * Fetch historical rates for charts
 * @param {string} currency - Currency code
 * @param {number} days - Number of days
 * @returns {Promise<Array>} - Array of history points
 */
export const fetchHistory = async (currency, days = 7) => {
    try {
        const response = await fetch(`${API_BASE}/history/${currency}?days=${days}`)

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error(`Failed to fetch history for ${currency}:`, error)
        return null
    }
}

/**
 * Get cache status
 * @returns {Promise<Object>} - Cache status from API
 */
export const getCacheStatus = async () => {
    try {
        const response = await fetch(`${API_BASE}/cache/status`)

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Failed to get cache status:', error)
        return null
    }
}

/**
 * Force refresh API cache
 * @returns {Promise<boolean>} - Success status
 */
export const refreshApiCache = async () => {
    try {
        const response = await fetch(`${API_BASE}/cache/refresh`, {
            method: 'POST'
        })

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        // Clear local cache too
        ratesCache.data = null
        ratesCache.timestamp = null

        return true
    } catch (error) {
        console.error('Failed to refresh cache:', error)
        return false
    }
}

/**
 * Create a new alert
 * @param {Object} alertData - Alert data
 * @returns {Promise<Object|null>} - Created alert or null
 */
export const createAlert = async (alertData) => {
    try {
        const response = await fetch(`${API_BASE}/alerts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertData)
        })

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Failed to create alert:', error)
        return null
    }
}

/**
 * Fetch all alerts
 * @returns {Promise<Array>} - Array of alerts
 */
export const fetchAlerts = async () => {
    try {
        const response = await fetch(`${API_BASE}/alerts`)

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Failed to fetch alerts:', error)
        return []
    }
}

/**
 * Delete an alert
 * @param {number} alertId - Alert ID to delete
 * @returns {Promise<boolean>} - Success status
 */
export const deleteAlert = async (alertId) => {
    try {
        const response = await fetch(`${API_BASE}/alerts/${alertId}`, {
            method: 'DELETE'
        })

        return response.ok
    } catch (error) {
        console.error(`Failed to delete alert ${alertId}:`, error)
        return false
    }
}

export default {
    fetchRates,
    fetchRate,
    fetchHistory,
    getCacheStatus,
    refreshApiCache,
    createAlert,
    fetchAlerts,
    deleteAlert
}
