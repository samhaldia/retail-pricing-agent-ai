import React, { useState, useEffect } from 'react';
import ProductCard from './components/ProductCard';
import Dashboard from './components/Dashboard';
import AIPromoGenerator from './components/AIPromoGenerator';

// --- Unified Base URL for all backend interactions ---
const BASE_URL = 'http://127.0.0.1:5000';

// API Endpoints derived from the BASE_URL
const PRODUCTS_API_URL = `${BASE_URL}/api/products`;
const TRIGGER_AGENT_RUN_URL = `${BASE_URL}/trigger-full-agent-run`;
const GENERATE_PROMO_IDEA_URL = `${BASE_URL}/api/generate-promo-idea`;
const APPLY_RECOMMENDATION_URL = `${BASE_URL}/apply-recommendation`;

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [products, setProducts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const fetchProductsAndRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(PRODUCTS_API_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setProducts(data.products);
      setRecommendations(data.recommendations);
    } catch (e) {
      console.error("Failed to fetch data:", e);
      setError("Failed to load data. Is the backend running? " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // --- MODIFIED useEffect for conditional refresh ---
  useEffect(() => {
    fetchProductsAndRecommendations(); // Always fetch initially on tab change or mount

    let intervalId;
    // Only set up the interval if the current tab is NOT 'ai_promos'
    if (activeTab !== 'ai_promos') {
      intervalId = setInterval(fetchProductsAndRecommendations, 10000); // Refresh every 10 seconds
    }

    // Cleanup function: Clear the interval when the component unmounts OR when activeTab changes
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [activeTab]); // Rerun this effect whenever activeTab changes
  // --- END MODIFIED useEffect ---

  const applyRecommendation = async (originalRecommendation) => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await fetch(APPLY_RECOMMENDATION_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            recommendation_id: originalRecommendation.id,
            sku: originalRecommendation.sku,
            new_price: originalRecommendation.recommendedPrice,
            original_recommendation: originalRecommendation
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      console.log("Recommendation apply result:", result);

      setSuccessMessage(`Recommendation for ${originalRecommendation.name} applied successfully!`);
      setTimeout(() => setSuccessMessage(null), 3000);

      await fetchProductsAndRecommendations();
    } catch (e) {
      console.error("Failed to apply recommendation:", e);
      setError(`Failed to apply recommendation: ${e.message}. Check backend logs.`);
    } finally {
      setLoading(false);
    }
  };

  const triggerFullAgentRun = async () => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await fetch(TRIGGER_AGENT_RUN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      console.log("Full agent run triggered:", result);
      setSuccessMessage("Agent workflow triggered successfully! Data will refresh shortly.");
      setTimeout(() => setSuccessMessage(null), 3000);
      setTimeout(fetchProductsAndRecommendations, 2000);
    } catch (e) {
      console.error("Failed to trigger agent run:", e);
      setError("Failed to trigger agent run. Is main.py running (for local) or AWS deployed (for AWS)?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col font-inter">
      <header className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-3xl font-bold">Autonomous Retail Pricing & Promotion Agent 🤖</h1>
          <nav>
            <ul className="flex space-x-6">
              <li><button onClick={() => setActiveTab('dashboard')} className={`py-2 px-4 rounded-md transition-colors ${activeTab === 'dashboard' ? 'bg-blue-700 font-semibold' : 'hover:bg-blue-500'}`}>Dashboard</button></li>
              <li><button onClick={() => setActiveTab('products')} className={`py-2 px-4 rounded-md transition-colors ${activeTab === 'products' ? 'bg-blue-700 font-semibold' : 'hover:bg-blue-500'}`}>Products</button></li>
              <li><button onClick={() => setActiveTab('recommendations')} className={`py-2 px-4 rounded-md transition-colors ${activeTab === 'recommendations' ? 'bg-blue-700 font-semibold' : 'hover:bg-blue-500'}`}>Recommendations ({recommendations.length})</button></li>
              <li><button onClick={() => setActiveTab('ai_promos')} className={`py-2 px-4 rounded-md transition-colors ${activeTab === 'ai_promos' ? 'bg-blue-700 font-semibold' : 'hover:bg-blue-500'}`}>AI Promos</button></li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container mx-auto p-6 flex-grow">
        {loading && <div className="text-center text-xl text-blue-600 py-8">Loading data...</div>}
        {error && <div className="text-center text-xl text-red-600 bg-red-100 p-4 rounded-lg shadow-md mb-4">{error}</div>}
        {successMessage && (
          <div className="text-center text-xl text-green-700 bg-green-100 p-4 rounded-lg shadow-md mb-4">
            {successMessage}
          </div>
        )}

        {!loading && !error && (
          <>
            {activeTab === 'dashboard' && (
              <Dashboard 
                products={products} 
                recommendations={recommendations} 
                onTriggerAgentRun={triggerFullAgentRun} 
                isLoading={loading}
              />
            )}
            {activeTab === 'products' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map(product => (
                  <ProductCard key={product.id} product={product} showApplyButton={false} />
                ))}
              </div>
            )}
            {activeTab === 'recommendations' && (
              <div className="space-y-6">
                <h2 className="text-3xl font-semibold text-gray-800 mb-4">Pending Recommendations ({recommendations.length})</h2>
                {recommendations.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {recommendations.map(product => (
                      <ProductCard 
                        key={product.id} 
                        product={product} 
                        onApplyRecommendation={() => applyRecommendation(product)} 
                        showApplyButton={true} 
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 text-lg p-4 bg-white rounded-lg shadow-sm">🎉 No new pricing recommendations at the moment. All prices are optimal!</p>
                )}
              </div>
            )}
            {activeTab === 'ai_promos' && (
              <AIPromoGenerator apiUrl={GENERATE_PROMO_IDEA_URL} />
            )}
          </>
        )}
      </main>

      <footer className="bg-gray-800 text-white p-4 text-center mt-8 rounded-t-lg">
        <div className="container mx-auto">
          <p>&copy; 2025 Agentic AI Retail Optimizer. Built for Hackathon. 🚀</p>
        </div>
      </footer>
    </div>
  );
}

export default App;