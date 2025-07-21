import React, { useState } from 'react';

const AIPromoGenerator = ({ apiUrl }) => {
  const [sku, setSku] = useState('');
  const [prompt, setPrompt] = useState('');
  const [idea, setIdea] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getPromotionIdea = async () => {
    setLoading(true);
    setError(null);
    setIdea(''); // Clear previous idea

    if (!sku || !prompt) {
      setError("Please enter both SKU and a prompt.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sku, prompt }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json(); // Parse the JSON response from backend

      // --- NEW DEBUGGING LINE ---
      console.log("AIPromoGenerator: Received data from backend:", data);
      // --- END NEW DEBUGGING LINE ---

      // Ensure the key matches exactly what the backend sends
      // The backend sends: {'promo_idea': promo_text}
      if (data && data.promo_idea) { // Check if data and promo_idea exist
        setIdea(data.promo_idea);
      } else {
        setError("Received invalid response from backend: 'promo_idea' not found.");
        console.error("Backend response missing 'promo_idea':", data);
      }

    } catch (e) {
      console.error("Failed to get promotion ideas:", e);
      setError(`Failed to get promotion ideas: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">Generate AI Promotion Idea</h2>
      <div className="mb-4">
        <label htmlFor="sku" className="block text-gray-700 text-sm font-bold mb-2">SKU:</label>
        <input
          type="text"
          id="sku"
          value={sku}
          onChange={(e) => setSku(e.target.value)}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          placeholder="e.g., P001"
        />
      </div>
      <div className="mb-6">
        <label htmlFor="prompt" className="block text-gray-700 text-sm font-bold mb-2">Prompt:</label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32"
          placeholder="e.g., Suggest a creative social media campaign for summer."
        ></textarea>
      </div>
      <button
        onClick={getPromotionIdea}
        className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        disabled={loading}
      >
        {loading ? 'Generating...' : 'Generate Idea'}
      </button>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {/* Only render the idea if 'idea' state is not empty */}
      {idea && (
        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-md">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Generated Promotion Idea:</h3>
          <p className="text-gray-700 whitespace-pre-line">{idea}</p>
        </div>
      )}
    </div>
  );
};

export default AIPromoGenerator;