/**
 * StepCard Component - Displays individual step with expand/collapse functionality
 */
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle, XCircle, AlertCircle, ExternalLink, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ResultTable from './ResultTable';

const StepCard = ({ step, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { step: stepDescription, result, success } = step;

  const hasError = result?.error !== null && result?.error !== undefined;
  const hasCaptcha = result?.error === 'CAPTCHA_DETECTED' || 
                     stepDescription?.toUpperCase().includes('CAPTCHA');
  const hasData = result?.data && (
    result.data.title || 
    result.data.url || 
    (result.data.items && result.data.items.length > 0) ||
    Object.keys(result.data).length > 0
  );

  const getStatusIcon = () => {
    if (hasCaptcha) {
      return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    }
    return success ? (
      <CheckCircle className="w-5 h-5 text-success-600" />
    ) : (
      <XCircle className="w-5 h-5 text-error-600" />
    );
  };

  const getStatusBadge = () => {
    if (hasCaptcha) {
      return 'badge-warning';
    }
    return success ? 'badge-success' : 'badge-error';
  };

  const getStatusText = () => {
    if (hasCaptcha) {
      return 'CAPTCHA Detected';
    }
    return success ? 'Success' : 'Failed';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="card mb-4 hover:shadow-lg transition-shadow duration-200"
    >
      <div
        className="cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0 mt-1">
              {getStatusIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  Step {index + 1}
                </span>
                <span className={`badge ${getStatusBadge()}`}>
                  {getStatusText()}
                </span>
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-1 break-words">
                {stepDescription || 'Unknown step'}
              </h3>
              {result?.message && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {result.message}
                </p>
              )}
              {hasError && !hasCaptcha && (
                <p className="text-sm text-error-600 mt-2 font-medium">
                  Error: {result.error}
                </p>
              )}
              {hasCaptcha && (
                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                  <p className="text-sm text-yellow-800 font-medium">
                    ⚠️ CAPTCHA detected. Manual intervention may be required.
                  </p>
                </div>
              )}
            </div>
          </div>
          <button
            className="flex-shrink-0 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="mt-4 pt-4 border-t border-gray-200"
          >
            <div className="space-y-4">
              {/* Result Message */}
              {result?.message && (
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700 mb-1">Message:</p>
                    <p className="text-sm text-gray-600">{result.message}</p>
                  </div>
                </div>
              )}

              {/* URL Link */}
              {result?.data?.url && (
                <div className="flex items-center gap-2">
                  <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 mb-1">URL:</p>
                    <a
                      href={result.data.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-700 hover:underline break-all"
                    >
                      {result.data.url}
                    </a>
                  </div>
                </div>
              )}

              {/* Title */}
              {result?.data?.title && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Title:</p>
                  <p className="text-sm text-gray-900">{result.data.title}</p>
                </div>
              )}

              {/* Result Table for extracted items */}
              {result?.data?.items && result.data.items.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Extracted Results:</p>
                  <ResultTable items={result.data.items} />
                </div>
              )}

              {/* Error Details */}
              {hasError && (
                <div className="p-3 bg-error-50 border border-error-200 rounded-lg">
                  <p className="text-sm font-medium text-error-800 mb-1">Error Details:</p>
                  <p className="text-sm text-error-700 font-mono whitespace-pre-wrap break-words">
                    {result.error}
                  </p>
                </div>
              )}

              {/* Raw Data (for debugging or detailed view) */}
              {hasData && !result?.data?.items && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Data:</p>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-x-auto">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Full Result Object (collapsible) */}
              <details className="group">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 mb-2">
                  View Full Result Object
                </summary>
                <div className="mt-2 bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-x-auto max-h-96 overflow-y-auto">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default StepCard;

