/**
 * StepList Component - Displays all steps with filtering capabilities
 */
import React, { useState, useMemo } from 'react';
import { Filter, Search, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import StepCard from './StepCard';

const StepList = ({ steps }) => {
  const [filter, setFilter] = useState('all'); // 'all', 'success', 'failed', 'captcha'
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSteps = useMemo(() => {
    let filtered = steps || [];

    // Apply status filter
    if (filter === 'success') {
      filtered = filtered.filter(step => step.success && 
        !(step.result?.error === 'CAPTCHA_DETECTED' || 
          step.step?.toUpperCase().includes('CAPTCHA')));
    } else if (filter === 'failed') {
      filtered = filtered.filter(step => !step.success && 
        !(step.result?.error === 'CAPTCHA_DETECTED' || 
          step.step?.toUpperCase().includes('CAPTCHA')));
    } else if (filter === 'captcha') {
      filtered = filtered.filter(step => 
        step.result?.error === 'CAPTCHA_DETECTED' || 
        step.step?.toUpperCase().includes('CAPTCHA'));
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(step =>
        step.step?.toLowerCase().includes(query) ||
        step.result?.message?.toLowerCase().includes(query) ||
        step.result?.data?.title?.toLowerCase().includes(query) ||
        step.result?.data?.url?.toLowerCase().includes(query) ||
        step.result?.error?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [steps, filter, searchQuery]);

  const stats = useMemo(() => {
    const total = steps?.length || 0;
    const success = steps?.filter(step => step.success && 
      !(step.result?.error === 'CAPTCHA_DETECTED' || 
        step.step?.toUpperCase().includes('CAPTCHA'))).length || 0;
    const failed = steps?.filter(step => !step.success && 
      !(step.result?.error === 'CAPTCHA_DETECTED' || 
        step.step?.toUpperCase().includes('CAPTCHA'))).length || 0;
    const captcha = steps?.filter(step => 
      step.result?.error === 'CAPTCHA_DETECTED' || 
      step.step?.toUpperCase().includes('CAPTCHA')).length || 0;

    return { total, success, failed, captcha };
  }, [steps]);

  if (!steps || steps.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No steps to display</p>
      </div>
    );
  }

  return (
    <div>
      {/* Stats and Filters */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="card mb-6"
      >
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Stats */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Filter className="w-4 h-4 text-gray-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Total Steps</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-success-600" />
              <div>
                <p className="text-xs text-gray-500">Success</p>
                <p className="text-lg font-semibold text-success-600">{stats.success}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-error-600" />
              <div>
                <p className="text-xs text-gray-500">Failed</p>
                <p className="text-lg font-semibold text-error-600">{stats.failed}</p>
              </div>
            </div>
            {stats.captcha > 0 && (
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                <div>
                  <p className="text-xs text-gray-500">CAPTCHA</p>
                  <p className="text-lg font-semibold text-yellow-600">{stats.captcha}</p>
                </div>
              </div>
            )}
          </div>

          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search steps..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Filter Buttons */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('success')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                filter === 'success'
                  ? 'bg-success-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <CheckCircle className="w-4 h-4" />
              Success
            </button>
            <button
              onClick={() => setFilter('failed')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                filter === 'failed'
                  ? 'bg-error-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <XCircle className="w-4 h-4" />
              Failed
            </button>
            {stats.captcha > 0 && (
              <button
                onClick={() => setFilter('captcha')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                  filter === 'captcha'
                    ? 'bg-yellow-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <AlertCircle className="w-4 h-4" />
                CAPTCHA
              </button>
            )}
          </div>
        </div>
      </motion.div>

      {/* Steps List */}
      <div className="space-y-4">
        {filteredSteps.length > 0 ? (
          filteredSteps.map((step, index) => (
            <StepCard
              key={index}
              step={step}
              index={steps.indexOf(step)}
            />
          ))
        ) : (
          <div className="card text-center py-12">
            <p className="text-gray-500">No steps match the current filters</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StepList;

