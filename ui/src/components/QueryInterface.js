import React, { useState } from 'react';
import { Zap, Send, Bot } from 'lucide-react';
import axios from 'axios';

const QueryInterface = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [responses, setResponses] = useState([]);

  const sampleQueries = [
    "Where's my riskiest path to the crown jewel database?",
    "What should I fix to reduce risk by 80%?",
    "Show me all paths from external servers to our database",
    "Which assets are most vulnerable to ransomware?",
    "How can I improve our security posture?",
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    const userQuery = query.trim();
    setQuery('');

    // Add user query to responses
    setResponses(prev => [...prev, { type: 'user', content: userQuery }]);

    try {
      // Call the real backend API
      const response = await axios.post('/api/v1/query', {
        query: userQuery,
        context: {}
      });

      const aiResponse = formatAPIResponse(response.data.results);
      setResponses(prev => [...prev, { type: 'ai', content: aiResponse }]);
    } catch (error) {
      console.error('Failed to get AI response:', error);
      const errorResponse = {
        text: "Sorry, I encountered an error processing your query.",
        details: [error.message || "Please try again or check the Attack Path Analysis tab for direct queries."],
        recommendations: []
      };
      setResponses(prev => [...prev, { type: 'ai', content: errorResponse }]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatAPIResponse = (results) => {
    const attackPaths = results.attack_paths || [];
    const explanations = results.explanations || [];
    const plan = results.plan || {};

    if (attackPaths.length === 0) {
      return {
        text: "I analyzed your query and found the following:",
        details: [
          `Target: ${plan.target || 'All crown jewels'}`,
          `Algorithm: ${plan.algorithm || 'hybrid'}`,
          `No direct attack paths found to the target.`,
          "This could indicate good security posture or the need to adjust search parameters."
        ],
        recommendations: [
          "Try increasing max hops to find longer paths",
          "Check if the target asset exists in the database",
          "Use the Attack Path Analysis tab for more control"
        ]
      };
    }

    // Format attack paths into readable text
    const pathTexts = attackPaths.map((path, i) => {
      const pathStr = path.path?.join(' → ') || 'Unknown path';
      const score = Math.round((path.score || 0) * 100);
      return `Path ${i + 1}: ${pathStr} (Risk: ${score}%)`;
    });

    // Extract recommendations from explanations
    const recs = explanations.slice(0, 3).map(exp => {
      return exp.explanation?.split('\n')[0] || "Review and remediate identified vulnerabilities";
    });

    return {
      text: `I found ${attackPaths.length} attack path${attackPaths.length > 1 ? 's' : ''} to ${plan.target || 'the target'}:`,
      details: pathTexts,
      recommendations: recs.length > 0 ? recs : [
        "Review the identified attack paths",
        "Prioritize remediating the highest risk paths",
        "Implement network segmentation where possible"
      ]
    };
  };

  const handleSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center">
          <Zap className="h-6 w-6 mr-2 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              AI Query Interface
            </h2>
            <p className="text-gray-600 mt-1">
              Ask questions about your security posture using natural language
            </p>
          </div>
        </div>
      </div>

      {/* Sample Queries */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Try These Sample Queries
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {sampleQueries.map((sampleQuery, index) => (
            <button
              key={index}
              onClick={() => handleSampleQuery(sampleQuery)}
              className="text-left p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-center">
                <Bot className="h-4 w-4 mr-2 text-gray-400" />
                <span className="text-sm text-gray-700">{sampleQuery}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Query Input */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ask a Question
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Where's my riskiest path to the database?"
                className="flex-1 input-field"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!query.trim() || isLoading}
                className="btn-primary flex items-center"
              >
                <Send className="h-4 w-4 mr-2" />
                {isLoading ? 'Thinking...' : 'Ask'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Chat History */}
      {responses.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Conversation History
          </h3>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {responses.map((response, index) => (
              <div key={index} className={`flex ${response.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl ${response.type === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className={`flex items-start space-x-2 ${
                    response.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      response.type === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {response.type === 'user' ? 'U' : <Bot className="h-4 w-4" />}
                    </div>
                    <div className={`flex-1 ${
                      response.type === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      <div className={`inline-block p-4 rounded-lg ${
                        response.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        {response.type === 'user' ? (
                          <p>{response.content}</p>
                        ) : (
                          <div>
                            <p className="font-medium mb-2">{response.content.text}</p>
                            {response.content.details && (
                              <ul className="list-disc list-inside mb-2 space-y-1">
                                {response.content.details.map((detail, i) => (
                                  <li key={i} className="text-sm">{detail}</li>
                                ))}
                              </ul>
                            )}
                            {response.content.recommendations && (
                              <div className="mt-3 p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                                <p className="font-medium text-blue-900 mb-1">Recommendations:</p>
                                <ul className="list-disc list-inside space-y-1">
                                  {response.content.recommendations.map((rec, i) => (
                                    <li key={i} className="text-sm text-blue-800">{rec}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="spinner"></div>
                      <span className="text-gray-600">AI is analyzing your query...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Capabilities */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          What I Can Help With
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Attack Path Analysis</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Find paths to critical assets</li>
              <li>• Identify high-risk attack vectors</li>
              <li>• Analyze lateral movement possibilities</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Security Recommendations</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Prioritize remediation actions</li>
              <li>• Suggest security controls</li>
              <li>• Generate implementation plans</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryInterface;
