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
    const crownJewels = results.crown_jewels || [];

    // Handle case with no paths
    if (attackPaths.length === 0) {
      // For general queries without specific target, show crown jewels
      if (!plan.target || plan.target === 'null') {
        return {
          text: "I'd be happy to help you analyze your security posture! I've identified your critical assets (crown jewels) in the environment. These are the assets that would have the highest impact if compromised:",
          details: crownJewels.slice(0, 5).map(cj => 
            `• ${cj.name} in ${cj.environment} - This ${cj.type} asset requires protection`
          ),
          recommendations: [
            "Try asking: 'Show me attack paths to our database' to see specific vulnerabilities",
            "I can analyze any of these crown jewels and identify how attackers might reach them",
            "For the most comprehensive view, try 'What are the riskiest paths across all critical assets?'"
          ]
        };
      }
      
      const targetAsset = crownJewels.find(cj => cj.id === plan.target);
      const targetDesc = targetAsset ? `${targetAsset.name}` : plan.target;
      
      return {
        text: `Good news! I analyzed potential attack paths to ${targetDesc} and didn't find any direct routes from external entry points.`,
        details: [
          "This suggests your asset is well-isolated from internet-facing systems",
          "I searched up to " + (plan.max_hops || 4) + " network hops using " + (plan.algorithm || 'hybrid') + " analysis",
          "However, this doesn't mean the asset is completely secure - internal threats or longer attack chains may still exist"
        ],
        recommendations: [
          "Continue monitoring for configuration changes that could create new attack paths",
          "Review internal access controls to prevent lateral movement",
          "Consider increasing the max hops parameter if you want to search for longer attack chains"
        ]
      };
    }

    // Get target name from crown jewels
    const targetAsset = crownJewels.find(cj => cj.id === plan.target);
    const targetName = targetAsset ? targetAsset.name : 'the target';
    const targetType = targetAsset ? targetAsset.type : 'asset';

    // Create natural language intro
    const highRiskPaths = attackPaths.filter(p => (p.score || 0) >= 0.5);
    const mediumRiskPaths = attackPaths.filter(p => (p.score || 0) >= 0.3 && (p.score || 0) < 0.5);
    
    let intro = `I've analyzed your ${targetType} (${targetName}) and identified ${attackPaths.length} potential attack path${attackPaths.length > 1 ? 's' : ''}.`;
    
    if (highRiskPaths.length > 0) {
      intro += ` ${highRiskPaths.length} of these ${highRiskPaths.length > 1 ? 'are' : 'is'} high risk and ${highRiskPaths.length > 1 ? 'require' : 'requires'} immediate attention.`;
    } else if (mediumRiskPaths.length > 0) {
      intro += ` Most paths show medium risk levels - you should plan remediation but there's no immediate crisis.`;
    } else {
      intro += ` The good news is that all paths show relatively low risk scores, suggesting decent security controls are in place.`;
    }

    // Format attack paths naturally
    const pathTexts = attackPaths.map((path, i) => {
      const pathStr = path.path?.join(' → ') || 'Unknown path';
      const score = Math.round((path.score || 0) * 100);
      const riskLevel = score >= 80 ? 'Critical' : score >= 50 ? 'High' : score >= 30 ? 'Medium' : 'Low';
      
      // Make it more conversational
      if (path.path && path.path.length === 2) {
        return `**Direct path** from ${path.path[0]} (${riskLevel} risk - ${score}%)`;
      } else if (path.path && path.path.length > 2) {
        return `**${path.path.length-1}-hop path** through ${path.path.slice(0, -1).join(' → ')} (${riskLevel} risk - ${score}%)`;
      }
      return `${pathStr} (${riskLevel} risk - ${score}%)`;
    });

    // Format explanations naturally
    let recs = [];
    if (explanations && explanations.length > 0) {
      // Extract the most meaningful parts of GPT-4 explanations
      recs = explanations.slice(0, 3).map((exp, i) => {
        if (exp.explanation) {
          // Try to extract actionable items from explanation
          const lines = exp.explanation.split('\n').filter(l => l.trim());
          // Look for lines that start with action words or numbers
          const actionLine = lines.find(l => 
            /^(\d+\.|•|-|Recommend|Implement|Apply|Enable|Disable|Remove|Add|Review|Monitor)/i.test(l)
          );
          return actionLine || lines[0] || `Strengthen security controls for path ${i + 1}`;
        }
        return `Review and harden security controls along attack path ${i + 1}`;
      });
    } else {
      // Generate contextual recommendations
      if (highRiskPaths.length > 0) {
        recs = [
          `Focus on the ${highRiskPaths.length} high-risk path${highRiskPaths.length > 1 ? 's' : ''} first - these present the most immediate threat`,
          "Implement network segmentation to break the attack chains you're seeing",
          "Review and tighten access controls on the assets in these paths"
        ];
      } else {
        recs = [
          "While risk is currently low, maintain your security posture through regular monitoring",
          "Consider additional hardening of entry point systems to prevent future compromise",
          "Implement continuous monitoring to detect any configuration changes that could increase risk"
        ];
      }
    }

    return {
      text: intro,
      details: pathTexts,
      recommendations: recs
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
