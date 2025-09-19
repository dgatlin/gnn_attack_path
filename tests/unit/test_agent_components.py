"""
Unit tests for agent components.

Tests agent planning, remediation, and orchestration in isolation.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from agent.planner import AttackPathPlanner
from agent.remediator import RemediationAgent
from agent.app import AttackPathAgent


class TestPlanner:
    """Unit tests for planner component."""
    
    def setup_method(self):
        """Set up test data."""
        self.sample_state = {
            "messages": [],
            "user_query": "Find attack paths to database servers",
            "intent": None,
            "plan": None
        }
    
    def test_planner_initialization(self):
        """Test planner initializes correctly."""
        planner = AttackPathPlanner()
        assert planner is not None
        assert hasattr(planner, 'plan_analysis')
        assert hasattr(planner, 'plan_remediation')
    
    def test_planner_intent_parsing(self):
        """Test intent parsing in planner."""
        with patch('agent.planner.ChatOpenAI') as mock_llm:
            # Mock the LLM response
            mock_response = Mock()
            mock_response.content = "security_analysis"
            mock_llm.return_value.invoke = Mock(return_value=mock_response)
            
            planner = AttackPathPlanner()
            result = planner.plan_analysis("Find attack paths to database servers")
            
            assert isinstance(result, dict)
            assert "intent" in result
    
    def test_planner_plan_creation(self):
        """Test plan creation in planner."""
        with patch('agent.planner.ChatOpenAI') as mock_llm:
            # Mock the LLM response for plan creation
            mock_response = Mock()
            mock_response.content = "1. Query graph for database servers\n2. Find attack paths\n3. Score paths"
            mock_llm.return_value.invoke = Mock(return_value=mock_response)
            
            planner = AttackPathPlanner()
            result = planner.plan_analysis("Find attack paths to database servers")
            
            assert isinstance(result, dict)
            assert "intent" in result
    
    def test_planner_different_queries(self):
        """Test planner with different query types."""
        test_queries = [
            "Show me risky assets",
            "Find vulnerabilities in web servers",
            "What are the crown jewels?",
            "Analyze network topology"
        ]
        
        with patch('agent.planner.ChatOpenAI') as mock_llm:
            mock_response = Mock()
            mock_response.content = "test_intent"
            mock_llm.return_value.invoke = Mock(return_value=mock_response)
            
            planner = AttackPathPlanner()
            for query in test_queries:
                result = planner.plan_analysis(query)
                
                assert isinstance(result, dict)
                assert "intent" in result
    
    def test_planner_error_handling(self):
        """Test planner error handling."""
        with patch('agent.planner.ChatOpenAI') as mock_llm:
            # Mock LLM to raise an exception
            mock_llm.return_value.invoke = Mock(side_effect=Exception("LLM Error"))
            
            planner = AttackPathPlanner()
            result = planner.plan_analysis("Test query")
            
            # Should handle error gracefully
            assert isinstance(result, dict)
            assert "intent" in result


class TestRemediationAgent:
    """Unit tests for RemediationAgent."""
    
    def setup_method(self):
        """Set up test data."""
        self.agent = RemediationAgent()
        self.sample_path = {
            "path": ["server1", "router1", "database1"],
            "risk_score": 0.8,
            "vulnerabilities": ["CVE-2023-1234", "CVE-2023-5678"]
        }
    
    def test_remediation_agent_initialization(self):
        """Test RemediationAgent initializes correctly."""
        assert self.agent is not None
        assert hasattr(self.agent, 'propose_remediation')
        assert hasattr(self.agent, 'simulate_remediation')
    
    @pytest.mark.asyncio
    async def test_propose_remediation(self):
        """Test remediation proposal."""
        result = await self.agent.propose_remediation(self.sample_path, "patch")
        
        assert isinstance(result, dict)
        assert "actions" in result
        assert "priority" in result
        assert "estimated_effort" in result
        assert isinstance(result["actions"], list)
        assert len(result["actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_simulate_remediation(self):
        """Test remediation simulation."""
        remediation_plan = {
            "actions": [
                {"type": "patch", "target": "server1", "description": "Apply security patch"},
                {"type": "configure", "target": "router1", "description": "Update firewall rules"}
            ],
            "priority": "high",
            "estimated_effort": "2 hours"
        }
        
        result = await self.agent.simulate_remediation(remediation_plan)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "new_risk_score" in result
        assert "impact_analysis" in result
        assert isinstance(result["success"], bool)
        assert 0.0 <= result["new_risk_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_different_remediation_types(self):
        """Test different remediation types."""
        remediation_types = ["patch", "configure", "isolate", "monitor"]
        
        for rem_type in remediation_types:
            result = await self.agent.propose_remediation(self.sample_path, rem_type)
            
            assert isinstance(result, dict)
            assert "actions" in result
            assert len(result["actions"]) > 0
            
            # Check that actions are relevant to the remediation type
            for action in result["actions"]:
                assert "type" in action
                assert "target" in action
                assert "description" in action
    
    @pytest.mark.asyncio
    async def test_high_risk_path_remediation(self):
        """Test remediation for high-risk paths."""
        high_risk_path = {
            "path": ["external", "dmz", "internal", "database"],
            "risk_score": 0.95,
            "vulnerabilities": ["CVE-2023-CRITICAL"]
        }
        
        result = await self.agent.propose_remediation(high_risk_path, "patch")
        
        assert result["priority"] == "critical"
        assert result["estimated_effort"] in ["immediate", "1 hour", "2 hours"]
        assert len(result["actions"]) >= 2  # Should have multiple actions for high risk
    
    @pytest.mark.asyncio
    async def test_low_risk_path_remediation(self):
        """Test remediation for low-risk paths."""
        low_risk_path = {
            "path": ["server1", "server2"],
            "risk_score": 0.2,
            "vulnerabilities": ["CVE-2023-LOW"]
        }
        
        result = await self.agent.propose_remediation(low_risk_path, "monitor")
        
        assert result["priority"] in ["low", "medium"]
        assert result["estimated_effort"] in ["1 day", "1 week"]
        assert len(result["actions"]) >= 1
    
    @pytest.mark.asyncio
    async def test_remediation_validation(self):
        """Test remediation plan validation."""
        invalid_plan = {
            "actions": [],  # Empty actions
            "priority": "invalid",
            "estimated_effort": "invalid"
        }
        
        result = await self.agent.simulate_remediation(invalid_plan)
        
        # Should handle invalid plans gracefully
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] == False  # Should fail validation
    
    @pytest.mark.asyncio
    async def test_remediation_impact_analysis(self):
        """Test remediation impact analysis."""
        remediation_plan = {
            "actions": [
                {"type": "patch", "target": "server1", "description": "Apply critical patch"},
                {"type": "isolate", "target": "network", "description": "Isolate compromised segment"}
            ],
            "priority": "high",
            "estimated_effort": "4 hours"
        }
        
        result = await self.agent.simulate_remediation(remediation_plan)
        
        assert "impact_analysis" in result
        impact = result["impact_analysis"]
        assert "affected_assets" in impact
        assert "downtime_estimate" in impact
        assert "security_improvement" in impact


class TestWorkflowOrchestration:
    """Unit tests for workflow orchestration."""
    
    def setup_method(self):
        """Set up test workflow."""
        self.agent = AttackPathAgent()
    
    def test_workflow_creation(self):
        """Test workflow creation."""
        assert self.agent is not None
        assert hasattr(self.agent, 'analyze_attack_paths')
        assert hasattr(self.agent, 'remediate_paths')
    
    def test_agent_components(self):
        """Test agent component structure."""
        # Check that agent has expected components
        assert hasattr(self.agent, 'planner')
        assert hasattr(self.agent, 'remediator')
        assert hasattr(self.agent, 'scoring_service')
        
        # Check component types
        assert isinstance(self.agent.planner, AttackPathPlanner)
        assert isinstance(self.agent.remediator, RemediationAgent)
    
    @pytest.mark.asyncio
    async def test_agent_analysis(self):
        """Test agent analysis functionality."""
        with patch('agent.planner.ChatOpenAI') as mock_llm:
            mock_response = Mock()
            mock_response.content = "security_analysis"
            mock_llm.return_value.invoke = Mock(return_value=mock_response)
            
            # Test analysis execution
            result = await self.agent.analyze_attack_paths("Find attack paths to database servers")
            
            assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_agent_remediation(self):
        """Test agent remediation functionality."""
        sample_paths = [
            {
                "path": ["external", "dmz", "database"],
                "risk_score": 0.8,
                "vulnerabilities": ["CVE-2023-1234"]
            }
        ]
        
        # Test remediation execution
        result = await self.agent.remediate_paths(sample_paths)
        
        assert isinstance(result, dict)
        assert "remediation_plans" in result
    
    def test_agent_initialization(self):
        """Test agent initialization with different parameters."""
        # Test default initialization
        agent1 = AttackPathAgent()
        assert agent1 is not None
        
        # Test with custom model path
        agent2 = AttackPathAgent(gnn_model_path="/path/to/model")
        assert agent2 is not None
        assert agent2.gnn_model_path == "/path/to/model"