/**
 * AgentHeader Component
 * Displays agent information: agent_id, overall_success, and query
 */

import { motion } from 'framer-motion';
import { FaCheckCircle, FaTimesCircle, FaUser, FaSearch } from 'react-icons/fa';

const AgentHeader = ({ agentData }) => {
  const { agent_id, overall_success, query } = agentData || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-lg shadow-md p-6 mb-6"
    >
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left Side: Agent ID and Query */}
        <div className="flex-1 space-y-3">
          {/* Agent ID */}
          <div className="flex items-center gap-2">
            <FaUser className="w-5 h-5 text-gray-500" />
            <span className="text-sm text-gray-600">Agent ID:</span>
            <span className="font-mono text-sm font-semibold text-gray-900 bg-gray-100 px-2 py-1 rounded">
              {agent_id || 'N/A'}
            </span>
          </div>

          {/* Query */}
          <div className="flex items-start gap-2">
            <FaSearch className="w-5 h-5 text-gray-500 mt-0.5" />
            <div className="flex-1">
              <span className="text-sm text-gray-600 block mb-1">Query:</span>
              <p className="text-base text-gray-900 font-medium break-words">
                {query || 'No query provided'}
              </p>
            </div>
          </div>
        </div>

        {/* Right Side: Status Badge */}
        <div className="flex items-center justify-end">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring' }}
            className={`flex items-center gap-2 px-4 py-2 rounded-full font-semibold ${
              overall_success
                ? 'bg-green-100 text-green-800 border-2 border-green-300'
                : 'bg-red-100 text-red-800 border-2 border-red-300'
            }`}
          >
            {overall_success ? (
              <>
                <FaCheckCircle className="w-5 h-5" />
                <span>Success</span>
              </>
            ) : (
              <>
                <FaTimesCircle className="w-5 h-5" />
                <span>Failed</span>
              </>
            )}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default AgentHeader;

