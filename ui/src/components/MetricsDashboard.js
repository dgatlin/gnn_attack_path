import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, AlertTriangle, Shield } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const MetricsDashboard = () => {
  const [timeRange, setTimeRange] = useState('24h');
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    // Mock data for demonstration
    const mockMetrics = {
      responseTime: [
        { time: '00:00', ms: 120 },
        { time: '04:00', ms: 95 },
        { time: '08:00', ms: 180 },
        { time: '12:00', ms: 150 },
        { time: '16:00', ms: 200 },
        { time: '20:00', ms: 110 },
      ],
      riskDistribution: [
        { level: 'High', count: 12, color: '#ef4444' },
        { level: 'Medium', count: 28, color: '#f59e0b' },
        { level: 'Low', count: 45, color: '#10b981' },
      ],
      algorithmPerformance: [
        { algorithm: 'GNN', accuracy: 94, speed: 120 },
        { algorithm: 'Hybrid', accuracy: 89, speed: 85 },
        { algorithm: 'Dijkstra', accuracy: 76, speed: 45 },
        { algorithm: 'PageRank', accuracy: 82, speed: 60 },
      ],
      attackPaths: [
        { path: 'External → DMZ → DB', count: 15, risk: 0.9 },
        { path: 'User → Admin → DB', count: 8, risk: 0.7 },
        { path: 'IoT → Network → DB', count: 12, risk: 0.8 },
      ]
    };

    // Simulate loading metrics
    const loadMetrics = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMetrics(mockMetrics);
    };
    loadMetrics();
  }, [timeRange]);

  // const COLORS = ['#ef4444', '#f59e0b', '#10b981'];

  if (!metrics) {
    return (
      <div className="space-y-6">
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="spinner mx-auto mb-4"></div>
            <p className="text-gray-600">Loading metrics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BarChart3 className="h-6 w-6 mr-2 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Metrics Dashboard
              </h2>
              <p className="text-gray-600 mt-1">
                Real-time performance and security metrics
              </p>
            </div>
          </div>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="select-field w-32"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24h</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
              <p className="text-2xl font-bold text-gray-900">142ms</p>
              <p className="text-sm text-green-600">↓ 12% from yesterday</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Risk Paths</p>
              <p className="text-2xl font-bold text-gray-900">12</p>
              <p className="text-sm text-red-600">↑ 3 from yesterday</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Shield className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Security Score</p>
              <p className="text-2xl font-bold text-gray-900">87%</p>
              <p className="text-sm text-green-600">↑ 5% from yesterday</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Paths Analyzed</p>
              <p className="text-2xl font-bold text-gray-900">1,247</p>
              <p className="text-sm text-blue-600">↑ 23% from yesterday</p>
            </div>
          </div>
        </div>
      </div>

      {/* Response Time Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Response Time Over Time
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metrics.responseTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip 
                formatter={(value) => [`${value}ms`, 'Response Time']}
                labelFormatter={(label) => `Time: ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="ms" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Distribution and Algorithm Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Risk Level Distribution
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.riskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ level, count }) => `${level}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {metrics.riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Algorithm Performance */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Algorithm Performance
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.algorithmPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="algorithm" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="accuracy" fill="#3b82f6" name="Accuracy %" />
                <Bar dataKey="speed" fill="#10b981" name="Speed (ms)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Attack Paths Analysis */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Top Attack Paths
        </h3>
        <div className="space-y-4">
          {metrics.attackPaths.map((path, index) => (
            <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-gray-900">{path.path}</div>
                <div className="text-sm text-gray-600">
                  {path.count} occurrences • Risk: {Math.round(path.risk * 100)}%
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-sm text-gray-600">Risk Level</div>
                  <div className={`badge ${
                    path.risk >= 0.8 ? 'badge-high' : 
                    path.risk >= 0.6 ? 'badge-medium' : 'badge-low'
                  }`}>
                    {path.risk >= 0.8 ? 'High' : path.risk >= 0.6 ? 'Medium' : 'Low'}
                  </div>
                </div>
                <div className="w-24">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        path.risk >= 0.8 ? 'bg-red-500' : 
                        path.risk >= 0.6 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${path.risk * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Health */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          System Health
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">99.9%</div>
            <div className="text-sm text-gray-600">Uptime</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">2.1s</div>
            <div className="text-sm text-gray-600">Avg Analysis Time</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">1,247</div>
            <div className="text-sm text-gray-600">Total Analyses</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
