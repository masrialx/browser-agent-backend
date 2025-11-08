/**
 * ResultTable Component
 * Displays extracted results in a table format (for titles, URLs, summaries, etc.)
 */

import { FaExternalLinkAlt, FaFileAlt, FaGlobe } from 'react-icons/fa';

const ResultTable = ({ data }) => {
  // Check if data contains array of results (like multiple search results)
  const hasResultsArray = Array.isArray(data.results) || Array.isArray(data.items);
  const resultsArray = data.results || data.items || [];

  // If it's a single result with title/URL, display it simply
  if (!hasResultsArray && (data.title || data.url)) {
    return null; // Already displayed in StepCard
  }

  // If there are multiple results, display them in a table
  if (hasResultsArray && resultsArray.length > 0) {
    return (
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-3">
          <FaFileAlt className="w-4 h-4 text-gray-600" />
          <h4 className="text-sm font-semibold text-gray-900">Extracted Results</h4>
          <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-semibold text-gray-700">
            {resultsArray.length} items
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  URL
                </th>
                {resultsArray.some((r) => r.summary) && (
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Summary
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {resultsArray.map((result, index) => (
                <tr key={index} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {result.title || result.name || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {result.url ? (
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-blue-600 hover:text-blue-800 break-all"
                      >
                        <FaGlobe className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate max-w-xs">{result.url}</span>
                        <FaExternalLinkAlt className="w-3 h-3 flex-shrink-0" />
                      </a>
                    ) : (
                      <span className="text-gray-400">N/A</span>
                    )}
                  </td>
                  {resultsArray.some((r) => r.summary) && (
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-md">
                      <p className="line-clamp-2">{result.summary || result.description || 'N/A'}</p>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // Display other structured data if present
  const otherDataKeys = Object.keys(data).filter(
    (key) => !['title', 'url', 'results', 'items'].includes(key) && data[key] !== null && data[key] !== ''
  );

  if (otherDataKeys.length > 0) {
    return (
      <div className="mt-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">Additional Data</h4>
        <div className="bg-gray-50 rounded-lg p-3 space-y-2">
          {otherDataKeys.map((key) => (
            <div key={key} className="flex flex-col sm:flex-row sm:items-start gap-1">
              <span className="text-xs font-semibold text-gray-600 capitalize min-w-[100px]">
                {key.replace(/_/g, ' ')}:
              </span>
              <span className="text-sm text-gray-900 break-words">
                {typeof data[key] === 'object' ? JSON.stringify(data[key], null, 2) : String(data[key])}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
};

export default ResultTable;

