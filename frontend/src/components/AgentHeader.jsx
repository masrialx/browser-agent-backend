/**
 * AgentHeader Component - Displays agent information
 */
import React from 'react';
import { CheckCircle, XCircle, User, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

const AgentHeader = ({ agentId, overallSuccess, query }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="card mb-6"
    >
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className={`p-2 rounded-lg ${
              overallSuccess 
                ? 'bg-success-100 text-success-600' 
                : 'bg-error-100 text-error-600'
            }`}>
              {overallSuccess ? (
                <CheckCircle className="w-6 h-6" />
              ) : (
                <XCircle className="w-6 h-6" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Browser Agent Dashboard
              </h1>
              <p className="text-sm text-gray-500">
                {overallSuccess ? 'Task completed successfully' : 'Task encountered errors'}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 mt-4">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">Agent ID:</span>
              <span className="text-sm font-mono font-semibold text-gray-900">
                {agentId || 'N/A'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">Query:</span>
              <span className="text-sm font-medium text-gray-900 max-w-md truncate">
                {query || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex-shrink-0">
          <span className={`badge ${
            overallSuccess ? 'badge-success' : 'badge-error'
          } text-base px-4 py-2`}>
            {overallSuccess ? 'Success' : 'Failed'}
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default AgentHeader;

