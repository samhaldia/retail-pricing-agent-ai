import React, { useState } from 'react';

function AIPromoGenerator({ apiBaseUrl }) {
  const [llmPrompt, setLlmPrompt] = useState('');
  const [llmResponse, setLlmResponse] = useState('');
  const [llmLoading, setLlmLoading] = useState(false);
  const [error, setError] = useState(null);

  const getPromotionIdeas = async () => {
    setLlmLoading(true);
    setLlmResponse('');
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/generate-promo-idea`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: llmPrompt }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setLlmResponse(data.promo_idea);
    } catch (e) {
      console.error("Failed to get promotion ideas:", e);
      setError("Failed to get promotion ideas. Is the backend running?");
    } finally {
      setLlmLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg max-w-2xl mx-auto">
      <h2 className="text-3xl font-semibold text-gray-800 mb-6">Generate Promotion Ideas with AI 💡</h2>
      <p className="text-gray-600 mb-4">
        This feature simulates asking an Amazon Bedrock-powered LLM for creative and data-driven promotion ideas.
        In a real scenario, the prompt would be enriched with real-time market data, product insights, and target audience profiles.
      </p>
      <div className="flex flex-col space-y-4">
        <textarea
          className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 resize-y"
          rows="5"
          placeholder="e.g., 'Suggest a promotion for new customers buying electronics in US-East.', 'Generate a campaign to clear slow-moving furniture inventory.', 'Give me ideas for a flash sale on audio accessories.'"
          value={llmPrompt}
          onChange={(e) => setLlmPrompt(e.target.value)}
        ></textarea>
        <button
          onClick={getPromotionIdeas}
          disabled={llmLoading || !llmPrompt.trim()}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg shadow-md transition-all duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {llmLoading ? 'Generating...' : 'Get Promotion Idea'}
        </button>
      </div>
      {error && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
      {llmResponse && (
        <div className="mt-6 p-6 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold text-blue-800 mb-3">AI Generated Idea:</h3>
          <p className="text-blue-700 whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: llmResponse.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}></p>
        </div>
      )}
    </div>
  );
}

export default AIPromoGenerator;