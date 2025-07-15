import React from 'react';

function Dashboard({ products, recommendations, onTriggerAgentRun, isLoading }) {
  const totalSKUs = products.length;
  const activePromotions = 5; // Placeholder for actual active promotions
  const priceAdjustmentsLast24h = recommendations.length; // Simplified for demo
  const revenueImpactLast7d = "+12.5%"; // Placeholder
  const conversionRateLast7d = "+3.2%"; // Placeholder

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg">
      <h2 className="text-3xl font-semibold text-gray-800 mb-6">Dashboard Overview 📊</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-blue-50 p-6 rounded-lg shadow-sm border border-blue-200">
          <h3 className="text-lg font-medium text-blue-800 mb-2">Total SKUs Managed</h3>
          <p className="text-4xl font-bold text-blue-600">{totalSKUs}</p>
        </div>
        <div className="bg-green-50 p-6 rounded-lg shadow-sm border border-green-200">
          <h3 className="text-lg font-medium text-green-800 mb-2">Active Promotions</h3>
          <p className="text-4xl font-bold text-green-600">{activePromotions}</p>
        </div>
        <div className="bg-yellow-50 p-6 rounded-lg shadow-sm border border-yellow-200">
          <h3 className="text-lg font-medium text-yellow-800 mb-2">Price Adjustments (Last 24h)</h3>
          <p className="text-4xl font-bold text-yellow-600">{priceAdjustmentsLast24h}</p>
        </div>
        <div className="bg-purple-50 p-6 rounded-lg shadow-sm border border-purple-200">
          <h3 className="text-lg font-medium text-purple-800 mb-2">Revenue Impact (Last 7d)</h3>
          <p className="text-4xl font-bold text-purple-600">{revenueImpactLast7d}</p>
        </div>
        <div className="bg-red-50 p-6 rounded-lg shadow-sm border border-red-200">
          <h3 className="text-lg font-medium text-red-800 mb-2">Conversion Rate (Last 7d)</h3>
          <p className="text-4xl font-bold text-red-600">{conversionRateLast7d}</p>
        </div>
      </div>

      <div className="mb-8 p-4 bg-blue-50 rounded-lg shadow-sm flex flex-col sm:flex-row items-center justify-between">
        <p className="text-blue-800 text-lg font-medium mb-2 sm:mb-0">
          Simulate a full AI agent workflow run to get fresh recommendations!
        </p>
        <button
          onClick={onTriggerAgentRun}
          disabled={isLoading}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg shadow-md transition-all duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Running Agents...' : 'Trigger Agent Run'}
        </button>
      </div>

      <h3 className="text-2xl font-semibold text-gray-800 mb-4">Top AI-Recommended Price Adjustment Opportunities ✨</h3>
      {recommendations.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white rounded-lg shadow-sm border border-gray-200">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product SKU</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recommended Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Est. Impact</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {recommendations.slice(0, 5).map(product => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.name} ({product.id})</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${product.currentPrice.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-bold">${product.recommendedPrice.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {product.recommendedPrice > product.currentPrice ?
                     `+${(((product.recommendedPrice - product.currentPrice) / product.currentPrice) * 100).toFixed(1)}% Margin` :
                     `${(((product.recommendedPrice - product.currentPrice) / product.currentPrice) * 100).toFixed(1)}% Sales`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{product.recommendationReason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-gray-600 text-lg p-4 bg-white rounded-lg shadow-sm">No top recommendations to display right now. Click "Trigger Agent Run" to get new insights!</p>
      )}
    </div>
  );
}

export default Dashboard;