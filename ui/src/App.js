import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import axios from 'axios';
import { Shield, Zap, Target, Settings, BarChart3 } from 'lucide-react';
import AttackPathAnalysis from './components/AttackPathAnalysis';
import RemediationPanel from './components/RemediationPanel';
import MetricsDashboard from './components/MetricsDashboard';
import QueryInterface from './components/QueryInterface';
import './App.css';

// Configure axios
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [activeTab, setActiveTab] = useState('analysis');
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    // Check API health on startup
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await axios.get('/health');
      setHealthStatus(response.data);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'unhealthy', error: error.message });
    }
  };

  const tabs = [
    { id: 'analysis', label: 'Attack Paths', icon: Target },
    { id: 'remediation', label: 'Remediation', icon: Shield },
    { id: 'query', label: 'AI Query', icon: Zap },
    { id: 'metrics', label: 'Metrics', icon: BarChart3 },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <Shield className="h-8 w-8 text-blue-600 mr-3" />
                <h1 className="text-xl font-bold text-gray-900">
                  GNN Attack Path Demo
                </h1>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    healthStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {healthStatus?.status === 'healthy' ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <button
                  onClick={checkHealth}
                  className="p-2 text-gray-400 hover:text-gray-600"
                >
                  <Settings className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <nav className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-3 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'analysis' && <AttackPathAnalysis />}
          {activeTab === 'remediation' && <RemediationPanel />}
          {activeTab === 'query' && <QueryInterface />}
          {activeTab === 'metrics' && <MetricsDashboard />}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-sm text-gray-500">
              <p>GNN Attack Path Demo - AI-powered cybersecurity analysis</p>
              <p className="mt-1">
                Built with PyTorch Geometric, LangGraph, and React
              </p>
            </div>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
