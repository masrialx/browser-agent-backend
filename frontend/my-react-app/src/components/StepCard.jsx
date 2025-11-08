/**
 * StepCard Component
 * Displays individual step information with expand/collapse functionality
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaCheckCircle,
  FaTimesCircle,
  FaChevronDown,
  FaChevronUp,
  FaExternalLinkAlt,
  FaExclamationTriangle,
  FaInfoCircle,
} from 'react-icons/fa';
import ResultTable from './ResultTable';

const StepCard = ({ step, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { step: stepDescription, result, success } = step || {};

  const hasError = result?.error;
  const hasCaptcha = result?.error === 'CAPTCHA_DETECTED' || stepDescription?.toUpperCase().includes('CAPTCHA');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.3 }}
      className={`bg-white rounded-lg shadow-md overflow-hidden border-l-4 ${
        success
          ? 'border-green-500'
          : hasCaptcha
          ? 'border-yellow-500'
          : 'border-red-500'
      }`}
    >
      {/* Step Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left hover:bg-gray-50 transition-colors duration-200"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {/* Status Icon */}
            <div className="flex-shrink-0">
              {success ? (
                <FaCheckCircle className="w-6 h-6 text-green-500" />
              ) : hasCaptcha ? (
                <FaExclamationTriangle className="w-6 h-6 text-yellow-500" />
              ) : (
                <FaTimesCircle className="w-6 h-6 text-red-500" />
              )}
            </div>

            {/* Step Description */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold text-gray-500">Step {index + 1}</span>
                {hasCaptcha && (
                  <span className="px-2 py-0.5 text-xs font-semibold bg-yellow-100 text-yellow-800 rounded-full">
                    CAPTCHA
                  </span>
                )}
              </div>
              <p className="text-sm font-medium text-gray-900 break-words">
                {stepDescription || 'Unknown step'}
              </p>
              {result?.message && (
                <p className="text-xs text-gray-600 mt-1 truncate">{result.message}</p>
              )}
            </div>
          </div>

          {/* Expand/Collapse Icon */}
          <div className="flex-shrink-0">
            {isExpanded ? (
              <FaChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <FaChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-200"
          >
            <div className="p-4 space-y-4">
              {/* Success Message */}
              {result?.message && (
                <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
                  <FaInfoCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-blue-900">{result.message}</p>
                </div>
              )}

              {/* Error Message */}
              {hasError && (
                <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg border border-red-200">
                  <FaTimesCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-red-900 mb-1">Error:</p>
                    <p className="text-sm text-red-800 break-words">{result.error}</p>
                  </div>
                </div>
              )}

              {/* CAPTCHA Warning */}
              {hasCaptcha && (
                <div className="flex items-start gap-2 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <FaExclamationTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-yellow-900 mb-1">CAPTCHA Detected</p>
                    <p className="text-sm text-yellow-800">
                      The agent has detected a CAPTCHA and paused execution. Please complete the CAPTCHA manually in the browser.
                    </p>
                  </div>
                </div>
              )}

              {/* URL and Title */}
              {result?.data && (result.data.url || result.data.title) && (
                <div className="space-y-2">
                  {result.data.title && (
                    <div>
                      <span className="text-xs font-semibold text-gray-600">Title:</span>
                      <p className="text-sm text-gray-900 mt-1">{result.data.title}</p>
                    </div>
                  )}
                  {result.data.url && (
                    <div>
                      <span className="text-xs font-semibold text-gray-600">URL:</span>
                      <a
                        href={result.data.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 mt-1 break-all"
                      >
                        <span className="truncate">{result.data.url}</span>
                        <FaExternalLinkAlt className="w-4 h-4 flex-shrink-0" />
                      </a>
                    </div>
                  )}
                </div>
              )}

              {/* Result Table for extracted data */}
              {result?.data && (
                <ResultTable data={result.data} />
              )}

              {/* Raw Result Data (for debugging) */}
              {process.env.NODE_ENV === 'development' && (
                <details className="mt-4">
                  <summary className="text-xs font-semibold text-gray-600 cursor-pointer hover:text-gray-900">
                    View Raw Data
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto scrollbar-hide">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default StepCard;

