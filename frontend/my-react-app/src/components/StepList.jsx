/**
 * StepList Component
 * Displays a list of steps with filtering and search capabilities
 */

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { FaFilter, FaSearch, FaCheckCircle, FaTimesCircle, FaExclamationTriangle } from 'react-icons/fa';
import StepCard from './StepCard';

const StepList = ({ steps = [] }) => {
  const [filter, setFilter] = useState('all'); // 'all', 'success', 'failed', 'captcha'
  const [searchQuery, setSearchQuery] = useState('');

  // Filter and search steps
  const filteredSteps = useMemo(() => {
    return steps.filter((step) => {
      // Filter by status
      const matchesFilter =
        filter === 'all' ||
        (filter === 'success' && step.success) ||
        (filter === 'failed' && !step.success && step.result?.error !== 'CAPTCHA_DETECTED') ||
        (filter === 'captcha' && (step.result?.error === 'CAPTCHA_DETECTED' || step.step?.toUpperCase().includes('CAPTCHA')));

      // Filter by search query
      const matchesSearch =
        !searchQuery ||
        step.step?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        step.result?.message?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        step.result?.data?.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        step.result?.data?.url?.toLowerCase().includes(searchQuery.toLowerCase());

      return matchesFilter && matchesSearch;
    });
  }, [steps, filter, searchQuery]);

  // Count statistics
  const stats = useMemo(() => {
    const successful = steps.filter((s) => s.success).length;
    const failed = steps.filter((s) => !s.success && s.result?.error !== 'CAPTCHA_DETECTED' && !s.step?.toUpperCase().includes('CAPTCHA')).length;
    const captcha = steps.filter((s) => s.result?.error === 'CAPTCHA_DETECTED' || s.step?.toUpperCase().includes('CAPTCHA')).length;
    return { total: steps.length, successful, failed, captcha };
  }, [steps]);

  if (steps.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <p className="text-gray-500">No steps to display</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Stats and Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Statistics */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-700">Steps:</span>
              <span className="px-2 py-1 bg-gray-100 rounded text-sm font-semibold text-gray-900">
                {stats.total}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <FaCheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm text-gray-600">{stats.successful} Success</span>
            </div>
            <div className="flex items-center gap-2">
              <FaTimesCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-gray-600">{stats.failed} Failed</span>
            </div>
            {stats.captcha > 0 && (
              <div className="flex items-center gap-2">
                <FaExclamationTriangle className="w-4 h-4 text-yellow-500" />
                <span className="text-sm text-gray-600">{stats.captcha} CAPTCHA</span>
              </div>
            )}
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-3 flex-1 lg:flex-initial lg:max-w-md">
            {/* Search */}
            <div className="relative flex-1">
              <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search steps..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Filter */}
            <div className="relative">
              <FaFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm appearance-none bg-white cursor-pointer"
              >
                <option value="all">All Steps</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="captcha">CAPTCHA</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-3">
        {filteredSteps.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-500">No steps match your filters</p>
          </div>
        ) : (
          filteredSteps.map((step, index) => (
            <StepCard key={index} step={step} index={index} />
          ))
        )}
      </div>
    </div>
  );
};

export default StepList;

