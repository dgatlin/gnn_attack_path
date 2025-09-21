import React, { useState } from 'react';
import { Shield, Play, CheckCircle } from 'lucide-react';

const RemediationPanel = () => {
  const [selectedActions, setSelectedActions] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationResults, setSimulationResults] = useState(null);

  const remediationActions = [
    { id: 'patch-server', name: 'Apply Security Patches', impact: 'High', effort: 'Medium' },
    { id: 'update-firewall', name: 'Update Firewall Rules', impact: 'High', effort: 'Low' },
    { id: 'enable-mfa', name: 'Enable Multi-Factor Authentication', impact: 'Medium', effort: 'Low' },
    { id: 'isolate-network', name: 'Isolate Network Segment', impact: 'High', effort: 'High' },
    { id: 'rotate-keys', name: 'Rotate Access Keys', impact: 'Medium', effort: 'Low' },
  ];

  const handleActionToggle = (actionId) => {
    setSelectedActions(prev => 
      prev.includes(actionId) 
        ? prev.filter(id => id !== actionId)
        : [...prev, actionId]
    );
  };

  const handleSimulate = async () => {
    setIsSimulating(true);
    
    // Simulate API call
    setTimeout(() => {
      setSimulationResults({
        originalRisk: 0.85,
        newRisk: 0.32,
        riskReduction: 0.53,
        affectedAssets: ['server-001', 'database-002'],
        estimatedTime: '2 hours',
        success: true
      });
      setIsSimulating(false);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Shield className="h-6 w-6 mr-2 text-blue-600" />
              Remediation Simulation
            </h2>
            <p className="text-gray-600 mt-1">
              Simulate security fixes and see their impact on attack paths
            </p>
          </div>
          <button
            onClick={handleSimulate}
            disabled={selectedActions.length === 0 || isSimulating}
            className="btn-primary flex items-center"
          >
            <Play className="h-4 w-4 mr-2" />
            {isSimulating ? 'Simulating...' : 'Simulate'}
          </button>
        </div>
      </div>

      {/* Remediation Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Select Remediation Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {remediationActions.map((action) => (
            <div
              key={action.id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                selectedActions.includes(action.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleActionToggle(action.id)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">{action.name}</h4>
                  <div className="flex space-x-4 mt-2">
                    <span className={`badge ${
                      action.impact === 'High' ? 'badge-high' : 
                      action.impact === 'Medium' ? 'badge-medium' : 'badge-low'
                    }`}>
                      Impact: {action.impact}
                    </span>
                    <span className={`badge ${
                      action.effort === 'High' ? 'badge-high' : 
                      action.effort === 'Medium' ? 'badge-medium' : 'badge-low'
                    }`}>
                      Effort: {action.effort}
                    </span>
                  </div>
                </div>
                <div className={`w-4 h-4 rounded border-2 ${
                  selectedActions.includes(action.id)
                    ? 'bg-blue-500 border-blue-500'
                    : 'border-gray-300'
                }`}>
                  {selectedActions.includes(action.id) && (
                    <CheckCircle className="w-4 h-4 text-white" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Simulation Results */}
      {simulationResults && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
            Simulation Results
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {Math.round(simulationResults.originalRisk * 100)}%
              </div>
              <div className="text-sm text-gray-600">Original Risk</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {Math.round(simulationResults.newRisk * 100)}%
              </div>
              <div className="text-sm text-gray-600">New Risk</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {Math.round(simulationResults.riskReduction * 100)}%
              </div>
              <div className="text-sm text-gray-600">Risk Reduction</div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Impact Analysis</h4>
            <div className="space-y-2 text-sm text-gray-600">
              <div>• Affected Assets: {simulationResults.affectedAssets.join(', ')}</div>
              <div>• Estimated Implementation Time: {simulationResults.estimatedTime}</div>
              <div>• Status: {simulationResults.success ? 'Ready to Deploy' : 'Needs Review'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Terraform Output */}
      {simulationResults && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Generated Infrastructure Code
          </h3>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
            <pre className="text-sm">
{`# Terraform configuration for selected remediations
resource "aws_security_group_rule" "block_external_access" {
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = "sg-12345678"
  action            = "deny"
}

resource "aws_iam_policy" "enable_mfa" {
  name = "force-mfa-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Deny"
      Action = "*"
      Resource = "*"
      Condition = {
        BoolIfExists = {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }]
  })
}`}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default RemediationPanel;
