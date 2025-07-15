import React from 'react';

function ProductCard({ product, onApplyRecommendation, showApplyButton }) {
  const isRecommended = product.recommendedPrice !== product.currentPrice;
  const priceDiff = product.recommendedPrice - product.currentPrice;
  const impactColor = priceDiff > 0 ? 'text-green-600' : (priceDiff < 0 ? 'text-red-600' : 'text-gray-600');

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-transform duration-300 hover:scale-105 flex flex-col h-full">
      <img
        src={product.imageUrl}
        alt={product.name}
        className="w-full h-48 object-cover object-center"
        onError={(e) => { e.target.onerror = null; e.target.src = `https://placehold.co/400x300/CCCCCC/000000?text=${product.name.split(' ')[0]}`; }}
      />
      <div className="p-6 flex flex-col flex-grow">
        <h3 className="text-xl font-bold text-gray-800 mb-2">{product.name}</h3>
        <p className="text-gray-600 text-sm mb-4">{product.category} | {product.region}</p>

        <div className="flex items-baseline mb-4">
          <span className="text-gray-500 line-through mr-2">
            Current: ${product.currentPrice.toFixed(2)}
          </span>
          {isRecommended ? (
            <span className={`font-extrabold text-2xl ${impactColor}`}>
              Rec: ${product.recommendedPrice.toFixed(2)}
            </span>
          ) : (
            <span className="text-gray-800 font-bold text-xl">
              Price: ${product.currentPrice.toFixed(2)}
            </span>
          )}
        </div>

        <p className="text-gray-700 text-sm mb-2">Inventory: {product.inventory}</p>
        <p className="text-gray-700 text-sm mb-2">Cost: ${product.cost.toFixed(2)}</p>
        {product.latestDemandFactor && (
            <p className="text-gray-700 text-sm mb-2">Demand Factor: {product.latestDemandFactor.toFixed(2)}</p>
        )}
        {product.latestCompetitorPrice && (
            <p className="text-gray-700 text-sm mb-4">Competitor: ${product.latestCompetitorPrice.toFixed(2)}</p>
        )}

        {isRecommended && (
          <p className="text-blue-600 text-sm italic mb-4 flex-grow">
            Reason: {product.recommendationReason}
          </p>
        )}

        {showApplyButton && isRecommended && (
          <button
            onClick={onApplyRecommendation}
            className="mt-auto bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg shadow-md transition-all duration-300 ease-in-out transform hover:scale-105"
          >
            Apply Recommendation
          </button>
        )}
      </div>
    </div>
  );
}

export default ProductCard;