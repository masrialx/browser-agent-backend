/**
 * AI Agent Service - API communication
 */
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const generateCode = async (prompt, language = 'python', context = {}) => {
  const response = await fetch(`${API_BASE_URL}/agent/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      language,
      context,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

export const analyzeCode = async (code, language = 'python') => {
  const response = await fetch(`${API_BASE_URL}/agent/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code,
      language,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

export const refactorCode = async (code, language = 'python', refactorType = 'optimize') => {
  const response = await fetch(`${API_BASE_URL}/agent/refactor`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code,
      language,
      refactor_type: refactorType,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

