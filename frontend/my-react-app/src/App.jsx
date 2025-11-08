/**
 * Main App Component
 * AI Agent Dashboard - Displays browser agent execution results
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaPaperPlane, FaSpinner, FaExclamationCircle, FaCheckCircle, FaRocket } from 'react-icons/fa';
import AgentHeader from './components/AgentHeader';
import StepList from './components/StepList';
import { executeBrowserTask, checkHealth } from './services/agentService';

function App() {
  const [query, setQuery] = useState('');
  const [agentId, setAgentId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  // Check health on component mount
  useEffect(() => {
    const checkServerHealth = async () => {
      try {
        const status = await checkHealth();
        setHealthStatus(status);
      } catch (err) {
        setHealthStatus({ status: 'unhealthy', error: err.message });
      }
    };
    checkServerHealth();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);
    setResponseData(null);

    try {
      const result = await executeBrowserTask(query, agentId || null);
      
      if (result.success && result.data) {
        setResponseData(result.data);
      } else {
        setError(result.error || 'Failed to execute task');
        // Still set response data if available even if success is false
        if (result.data) {
          setResponseData(result.data);
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred while executing the task');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setAgentId('');
    setResponseData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FaRocket className="w-8 h-8 text-primary-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Agent Dashboard</h1>
                <p className="text-sm text-gray-600">Browser Automation Task Executor</p>
              </div>
            </div>
            
            {/* Health Status */}
            {healthStatus && (
              <div className="flex items-center gap-2">
                {healthStatus.status === 'healthy' ? (
                  <>
                    <FaCheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-sm text-green-700 font-medium">Server Online</span>
                  </>
                ) : (
                  <>
                    <FaExclamationCircle className="w-5 h-5 text-red-500" />
                    <span className="text-sm text-red-700 font-medium">Server Offline</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Query Input Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-md p-6 mb-6"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="query" className="block text-sm font-semibold text-gray-700 mb-2">
                Task Query
              </label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your task query (e.g., 'Find latest news about OpenAI', 'Search for AI on Google')"
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                disabled={loading}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label htmlFor="agentId" className="block text-sm font-semibold text-gray-700 mb-2">
                  Agent ID (Optional)
                </label>
                <input
                  id="agentId"
                  type="text"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  placeholder="e.g., agent_123"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={loading}
                />
              </div>

              <div className="flex items-end gap-2">
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  {loading ? (
                    <>
                      <FaSpinner className="w-5 h-5 animate-spin" />
                      <span>Executing...</span>
                    </>
                  ) : (
                    <>
                      <FaPaperPlane className="w-5 h-5" />
                      <span>Execute</span>
                    </>
                  )}
                </button>
                {responseData && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors duration-200"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </form>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg"
              >
                <div className="flex items-start gap-2">
                  <FaExclamationCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-red-900">Error</p>
                    <p className="text-sm text-red-800 mt-1">{error}</p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Results */}
        <AnimatePresence>
          {responseData && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Agent Header */}
              <AgentHeader agentData={responseData} />

              {/* Steps List */}
              {responseData.steps && responseData.steps.length > 0 ? (
                <StepList steps={responseData.steps} />
              ) : (
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                  <p className="text-gray-500">No steps available</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!responseData && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white rounded-lg shadow-md p-12 text-center"
          >
            <FaRocket className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Ready to Execute Tasks
            </h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Enter a task query above to start executing browser automation tasks. The agent will break down your query into steps and execute them automatically.
            </p>
          </motion.div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-600">
            AI Agent Dashboard - Browser Automation Platform
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
