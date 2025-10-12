import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { Target, AlertTriangle, Clock, Zap, ChevronRight } from 'lucide-react';
import axios from 'axios';

const AttackPathAnalysis = () => {
  const [target, setTarget] = useState('asset-171');
  const [algorithm, setAlgorithm] = useState('hybrid');
  const [maxHops, setMaxHops] = useState(4);
  const [crownJewels, setCrownJewels] = useState([]);

  // Fetch crown jewels
  useEffect(() => {
    const fetchCrownJewels = async () => {
      try {
        const response = await axios.get('/api/v1/crown-jewels');
        setCrownJewels(response.data.crown_jewels);
      } catch (error) {
        console.error('Failed to fetch crown jewels:', error);
      }
    };
    fetchCrownJewels();
  }, []);

  // Fetch attack paths
  const { data: attackPaths, isLoading, error, refetch } = useQuery(
    ['attackPaths', target, algorithm, maxHops],
    async () => {
      const response = await axios.post('/api/v1/paths', {
        target,
        algorithm,
        max_hops: maxHops,
        k: 5
      });
      return response.data;
    },
    {
      enabled: !!target,
      refetchOnWindowFocus: false,
    }
  );

  const getRiskLevel = (score) => {
    if (score >= 0.8) return { level: 'high', color: 'text-red-600', bg: 'bg-red-100' };
    if (score >= 0.6) return { level: 'medium', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { level: 'low', color: 'text-green-600', bg: 'bg-green-100' };
  };

  const formatScore = (score) => {
    return Math.round(score * 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Target className="h-6 w-6 mr-2 text-blue-600" />
              Attack Path Analysis
            </h2>
            <p className="text-gray-600 mt-1">
              Identify and analyze potential attack paths to critical assets
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="btn-primary flex items-center"
            disabled={isLoading}
          >
            <Zap className="h-4 w-4 mr-2" />
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Asset
            </label>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="select-field"
            >
              <option value="">Select target...</option>
              {crownJewels.map((jewel) => (
                <option key={jewel.id} value={jewel.id}>
                  {jewel.name} ({jewel.type})
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Algorithm
            </label>
            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
              className="select-field"
            >
              <option value="hybrid">Hybrid (Recommended)</option>
              <option value="dijkstra">Dijkstra</option>
              <option value="pagerank">PageRank</option>
              <option value="motif">Motif Detection</option>
              <option value="gnn">Graph Neural Network</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Hops
            </label>
            <select
              value={maxHops}
              onChange={(e) => setMaxHops(parseInt(e.target.value))}
              className="select-field"
            >
              <option value={2}>2 hops</option>
              <option value={3}>3 hops</option>
              <option value={4}>4 hops</option>
              <option value={5}>5 hops</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="card text-center py-12">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Analyzing attack paths...</p>
        </div>
      )}

      {error && (
        <div className="card border-red-200 bg-red-50">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-800">
              Failed to analyze attack paths: {error.message}
            </p>
          </div>
        </div>
      )}

      {attackPaths && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Analysis Results
                </h3>
                <p className="text-gray-600">
                  Found {attackPaths.paths.length} attack paths to {attackPaths.target}
                </p>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">Response Time</div>
                <div className="text-lg font-semibold text-blue-600">
                  {attackPaths.latency_ms.toFixed(0)}ms
                </div>
              </div>
            </div>
          </div>

          {/* Attack Paths */}
          {attackPaths.paths.map((path, index) => {
            const risk = getRiskLevel(path.score);
            return (
              <div key={index} className="card">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`badge ${risk.bg} ${risk.color} mr-3`}>
                      Risk: {formatScore(path.score)}%
                    </div>
                    <span className="text-sm text-gray-500">
                      Path {index + 1} • {path.length} hops • {path.algorithm}
                    </span>
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <Clock className="h-4 w-4 mr-1" />
                    {path.length * 2} min estimated
                  </div>
                </div>

                {/* Path Visualization */}
                <div className="mb-4">
                  <div className="flex items-center flex-wrap">
                    {path.path.map((node, nodeIndex) => (
                      <React.Fragment key={nodeIndex}>
                        <div className={`path-node ${
                          nodeIndex === 0 ? 'entry' : 
                          nodeIndex === path.path.length - 1 ? 'target' : 'intermediate'
                        }`}>
                          {nodeIndex === 0 ? 'E' : 
                           nodeIndex === path.path.length - 1 ? 'T' : nodeIndex}
                        </div>
                        {nodeIndex < path.path.length - 1 && (
                          <ChevronRight className="path-arrow" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                {/* Risk Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Risk Level</span>
                    <span>{formatScore(path.score)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`risk-bar ${risk.level}`}
                      style={{ width: `${formatScore(path.score)}%` }}
                    />
                  </div>
                </div>

                {/* Explanation */}
                {path.explanation && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Attack Path Analysis</h4>
                    <p className="text-gray-700 text-sm">{path.explanation}</p>
                  </div>
                )}

                {/* Path Details */}
                <details className="mt-4">
                  <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                    View Path Details
                  </summary>
                  <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">
                      <div className="font-medium mb-2">Path Nodes:</div>
                      <div className="space-y-1">
                        {path.path.map((node, nodeIndex) => (
                          <div key={nodeIndex} className="flex items-center">
                            <span className="w-6 text-center text-xs text-gray-500">
                              {nodeIndex + 1}.
                            </span>
                            <code className="ml-2 px-2 py-1 bg-white rounded text-xs">
                              {node}
                            </code>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </details>
              </div>
            );
          })}

          {attackPaths.paths.length === 0 && (
            <div className="card text-center py-12">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Attack Paths Found
              </h3>
              <p className="text-gray-600">
                No direct attack paths were found to the selected target.
                This could indicate good security posture or the need to adjust parameters.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AttackPathAnalysis;
