import React, { useState } from 'react';
import { Zap, Send, Bot, AlertCircle } from 'lucide-react';

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

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = generateAIResponse(userQuery);
      setResponses(prev => [...prev, { type: 'ai', content: aiResponse }]);
      setIsLoading(false);
    }, 1500);
  };

  const generateAIResponse = (userQuery) => {
    const lowerQuery = userQuery.toLowerCase();
    
    if (lowerQuery.includes('riskiest') || lowerQuery.includes('risk')) {
      return {
        text: "I found 3 high-risk attack paths to your crown jewel database:",
        details: [
          "Path 1: External → DMZ → Internal → Database (Risk: 94%)",
          "Path 2: Compromised User → Admin → Root → Database (Risk: 87%)",
          "Path 3: IoT Device → Network → Database (Risk: 82%)"
        ],
        recommendations: [
          "Apply security patches to DMZ servers",
          "Enable multi-factor authentication for admin accounts",
          "Isolate IoT devices from critical networks"
        ]
      };
    } else if (lowerQuery.includes('fix') || lowerQuery.includes('remediate')) {
      return {
        text: "Here are the top remediation actions to reduce risk:",
        details: [
          "1. Remove public ingress from security groups (Risk reduction: 45%)",
          "2. Apply critical security patches (Risk reduction: 30%)",
          "3. Enable MFA for all admin accounts (Risk reduction: 25%)"
        ],
        recommendations: [
          "Start with removing public access - highest impact, lowest effort",
          "Schedule patching during maintenance window",
          "Implement MFA gradually to avoid user disruption"
        ]
      };
    } else if (lowerQuery.includes('vulnerable') || lowerQuery.includes('vulnerability')) {
      return {
        text: "I've identified the most vulnerable assets in your network:",
        details: [
          "Database servers (3 critical vulnerabilities)",
          "Web application servers (2 high-risk vulnerabilities)",
          "Administrative workstations (1 zero-day vulnerability)"
        ],
        recommendations: [
          "Prioritize database server patching immediately",
          "Implement web application firewall rules",
          "Isolate admin workstations from production networks"
        ]
      };
    } else {
      return {
        text: "I can help you analyze attack paths, identify vulnerabilities, and recommend remediation actions. Try asking about:",
        details: [
          "• Risk assessment of specific assets",
          "• Attack path analysis",
          "• Security remediation recommendations",
          "• Vulnerability prioritization"
        ],
        recommendations: [
          "Be specific about what you want to analyze",
          "Mention specific assets or attack scenarios",
          "Ask for actionable recommendations"
        ]
      };
    }
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
