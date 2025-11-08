/**
 * Browser Agent Service - API communication for browser automation
 */
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:5000/api/v1/browser-agent';

/**
 * Execute a browser task
 * @param {string} query - The task query to execute
 * @param {string} [agentId] - Optional agent identifier
 * @param {string} [userId] - Optional user identifier
 * @returns {Promise<Object>} The execution results
 */
export const executeBrowserTask = async (query, agentId = null, userId = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/execute`, {
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

    return await response.json();
  } catch (error) {
    console.error('Error executing browser task:', error);
    throw error;
  }
};

/**
 * Health check for the browser agent service
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
};

