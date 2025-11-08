/**
 * API Service for Browser Agent
 * Handles all communication with the backend API
 * Uses Vite proxy in development, or direct URL in production
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '' : 'http://localhost:5000');

/**
 * Execute a browser task
 * @param {string} query - The user query describing the task
 * @param {string} agentId - Optional agent identifier
 * @param {string} userId - Optional user identifier
 * @returns {Promise<Object>} The API response
 */
export const executeBrowserTask = async (query, agentId = null, userId = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/browser-agent/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        ...(agentId && { agent_id: agentId }),
        ...(userId && { user_id: userId }),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error executing browser task:', error);
    throw error;
  }
};

/**
 * Health check endpoint
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/browser-agent/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
};

