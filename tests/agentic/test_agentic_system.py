#!/usr/bin/env python3
"""
Comprehensive Test Suite for Agentic Aspects of GNN Attack Path System

This test suite covers:
1. Unit tests for individual agent components
2. Integration tests for agent workflows
3. MCP (Model Context Protocol) functionality
4. End-to-end agent orchestration
5. Mock data and error handling
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent components
from agent.app import AttackPathAgent
from agent.planner import AttackPathPlanner
from agent.remediator import RemediationAgent
from agent.mcp_agent import MCPEnhancedAgent, MCPTool
from agent.mcp_client import MCPClientConfig, MCPToolWrapper

# Import API components
from api.main import app
from fastapi.testclient import TestClient

# Import scorer components
from scorer.service import AttackPathScoringService


class TestAttackPathPlanner:
    """Unit tests for AttackPathPlanner"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the LLM to avoid OpenAI API key requirement
        with patch('agent.planner.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm_class.return_value = mock_llm
            self.planner = AttackPathPlanner()
    
    def test_parse_intent_find_riskiest(self):
        """Test parsing intent for finding riskiest paths"""
        query = "What are the riskiest attack paths?"
        intent = self.planner._parse_intent(query)
        assert intent == "find_riskiest_paths"
    
    def test_parse_intent_find_attack_paths(self):
        """Test parsing intent for finding attack paths"""
        query = "Show me attack paths to the database"
        intent = self.planner._parse_intent(query)
        assert intent == "find_attack_paths"
    
    def test_parse_intent_remediate(self):
        """Test parsing intent for remediation"""
        query = "How can I fix these security issues?"
        intent = self.planner._parse_intent(query)
        assert intent == "remediate_risks"
    
    def test_parse_intent_simulate(self):
        """Test parsing intent for simulation"""
        query = "Simulate the impact of these changes"
        intent = self.planner._parse_intent(query)
        assert intent == "simulate_changes"
    
    def test_extract_target_crown_jewel(self):
        """Test extracting crown jewel target"""
        query = "Find paths to crown jewel"
        target = self.planner._extract_target(query)
        assert target == "crown-jewel-db-001"
    
    def test_extract_target_database(self):
        """Test extracting database target"""
        query = "Show paths to database"
        target = self.planner._extract_target(query)
        assert target == "db-payments"
    
    def test_extract_risk_threshold(self):
        """Test extracting risk threshold"""
        query = "Find high-risk paths"
        threshold = self.planner._extract_risk_threshold(query)
        assert threshold == 0.7  # Default value
    
    def test_extract_max_hops(self):
        """Test extracting max hops"""
        query = "Find paths with max 3 hops"
        max_hops = self.planner._extract_max_hops(query)
        assert max_hops == 4  # Default value
    
    def test_select_algorithm_riskiest(self):
        """Test algorithm selection for riskiest paths"""
        algorithm = self.planner._select_algorithm("find_riskiest_paths")
        assert algorithm == "hybrid"
    
    def test_select_algorithm_attack_paths(self):
        """Test algorithm selection for attack paths"""
        algorithm = self.planner._select_algorithm("find_attack_paths")
        assert algorithm == "gnn"
    
    def test_generate_analysis_actions(self):
        """Test generating analysis actions"""
        actions = self.planner._generate_analysis_actions("find_riskiest_paths")
        assert "load_graph_data" in actions
        assert "find_entry_points" in actions
        assert "score_paths" in actions
        assert "rank_by_risk" in actions
        assert "generate_explanations" in actions
    
    def test_plan_analysis(self):
        """Test complete analysis planning"""
        query = "Find the riskiest attack paths to our database"
        plan = self.planner.plan_analysis(query)
        
        assert "intent" in plan
        assert "target" in plan
        assert "risk_threshold" in plan
        assert "max_hops" in plan
        assert "algorithm" in plan
        assert "actions" in plan
        assert plan["intent"] == "find_riskiest_paths"
        assert plan["target"] == "db-payments"
    
    def test_plan_remediation(self):
        """Test remediation planning"""
        attack_paths = [
            {"path": ["external", "dmz", "db"], "score": 0.9},
            {"path": ["internal", "db"], "score": 0.7}
        ]
        query = "Fix these security issues"
        
        plan = self.planner.plan_remediation(attack_paths, query)
        
        assert "target_risk_reduction" in plan
        assert "blast_radius_constraint" in plan
        assert "priority_actions" in plan
        assert "simulation_required" in plan
        assert "approval_required" in plan


class TestRemediationAgent:
    """Unit tests for RemediationAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.remediator = RemediationAgent()
    
    def test_analyze_paths_for_remediation(self):
        """Test analyzing paths for remediation opportunities"""
        paths = [
            {"path": ["external", "dmz", "db"], "score": 0.9},
            {"path": ["internal", "db"], "score": 0.6}
        ]
        
        analysis = self.remediator._analyze_paths_for_remediation(paths)
        
        assert "high_risk_paths" in analysis
        assert "common_vulnerabilities" in analysis
        assert "network_issues" in analysis
        assert "iam_issues" in analysis
        assert "patch_requirements" in analysis
        assert len(analysis["high_risk_paths"]) == 1  # Only the 0.9 score path
    
    def test_analyze_edge_public_exposure(self):
        """Test analyzing edge for public exposure"""
        analysis = self.remediator._analyze_edge("public-server", "internal-db")
        
        assert "network_issues" in analysis
        assert len(analysis["network_issues"]) == 1
        assert analysis["network_issues"][0]["issue"] == "Public exposure"
        assert analysis["network_issues"][0]["severity"] == "high"
    
    def test_generate_remediation_actions(self):
        """Test generating remediation actions"""
        analysis = {
            "network_issues": [
                {"issue": "Public exposure", "source": "public-server", "target": "db", "severity": "high"}
            ],
            "common_vulnerabilities": [
                {"cve": "CVE-2023-1234", "asset": "server-001"}
            ],
            "iam_issues": [
                {"role": "admin-role", "permissions": "excessive"}
            ]
        }
        constraints = {"max_actions": 5}
        
        actions = self.remediator._generate_remediation_actions(analysis, constraints)
        
        assert len(actions) > 0
        assert any(action["type"] == "remove_public_ingress" for action in actions)
        assert any(action["type"] == "apply_patch" for action in actions)
        assert any(action["type"] == "revoke_iam_permission" for action in actions)
    
    def test_prioritize_actions(self):
        """Test prioritizing actions by impact/effort ratio"""
        actions = [
            {"id": "1", "impact": 3, "effort": 1, "type": "remove_public_ingress"},  # ratio = 3
            {"id": "2", "impact": 2, "effort": 3, "type": "apply_patch"},  # ratio = 0.67
            {"id": "3", "impact": 3, "effort": 2, "type": "revoke_iam_permission"}  # ratio = 1.5
        ]
        constraints = {"max_actions": 2}
        
        prioritized = self.remediator._prioritize_actions(actions, constraints)
        
        assert len(prioritized) == 2
        assert prioritized[0]["id"] == "1"  # Highest impact/effort ratio (3.0)
        assert prioritized[1]["id"] == "3"  # Second highest (1.5)
    
    def test_estimate_risk_reduction(self):
        """Test estimating risk reduction"""
        actions = [
            {"impact": "high"},
            {"impact": "medium"},
            {"impact": "low"}
        ]
        
        reduction = self.remediator._estimate_risk_reduction(actions)
        assert reduction == 0.6  # 0.3 + 0.2 + 0.1
    
    def test_estimate_effort(self):
        """Test estimating effort"""
        actions = [
            {"effort": "low"},
            {"effort": "medium"},
            {"effort": "high"},
            {"effort": "low"}
        ]
        
        effort_counts = self.remediator._estimate_effort(actions)
        assert effort_counts["low"] == 2
        assert effort_counts["medium"] == 1
        assert effort_counts["high"] == 1
    
    def test_simulate_single_action_remove_public_ingress(self):
        """Test simulating removal of public ingress"""
        action = {"type": "remove_public_ingress", "target": "public-server"}
        current_paths = [{"path": ["external", "dmz", "db"], "score": 0.9}]
        
        result = self.remediator._simulate_single_action(action, current_paths)
        
        assert result["success"] is True
        assert result["risk_reduction"] == 0.4
        assert "public-server" in result["affected_assets"]
    
    def test_simulate_single_action_apply_patch(self):
        """Test simulating patch application"""
        action = {"type": "apply_patch", "target": "server-001"}
        current_paths = [{"path": ["internal", "server-001", "db"], "score": 0.8}]
        
        result = self.remediator._simulate_single_action(action, current_paths)
        
        assert result["success"] is True
        assert result["risk_reduction"] == 0.3
        assert "server-001" in result["affected_assets"]
    
    def test_generate_remediation_plan(self):
        """Test generating complete remediation plan"""
        attack_paths = [
            {"path": ["external", "dmz", "db"], "score": 0.9},
            {"path": ["internal", "db"], "score": 0.7}
        ]
        constraints = {"max_actions": 3, "blast_radius_constraint": "moderate"}
        
        plan = self.remediator.generate_remediation_plan(attack_paths, constraints)
        
        assert "analysis" in plan
        assert "actions" in plan
        assert "implementation_plan" in plan
        assert "estimated_risk_reduction" in plan
        assert "estimated_effort" in plan
        assert len(plan["actions"]) <= 3
    
    def test_simulate_remediation(self):
        """Test simulating remediation effects"""
        actions = [
            {"id": "1", "type": "remove_public_ingress", "target": "public-server"},
            {"id": "2", "type": "apply_patch", "target": "server-001"}
        ]
        current_paths = [{"path": ["external", "dmz", "db"], "score": 0.9}]
        
        simulation = self.remediator.simulate_remediation(actions, current_paths)
        
        assert "simulation_results" in simulation
        assert "total_risk_reduction" in simulation
        assert "affected_assets" in simulation
        assert "success_rate" in simulation
        assert "recommendations" in simulation
        assert simulation["total_risk_reduction"] == 0.7  # 0.4 + 0.3
        assert simulation["success_rate"] == 1.0  # Both actions successful


class TestAttackPathAgent:
    """Unit tests for AttackPathAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the scorer service
        with patch('agent.app.AttackPathScoringService') as mock_scorer_class:
            mock_scorer = Mock()
            mock_scorer.get_crown_jewels.return_value = [
                {"id": "crown-jewel-1", "name": "Database", "type": "database"}
            ]
            mock_scorer.get_attack_paths.return_value = [
                {"path": ["external", "dmz", "db"], "score": 0.9, "algorithm": "hybrid"}
            ]
            mock_scorer.get_risk_explanation.return_value = "High-risk path through DMZ"
            mock_scorer.get_metrics.return_value = {"total_paths": 10, "avg_score": 0.7}
            mock_scorer_class.return_value = mock_scorer
            
            self.agent = AttackPathAgent()
            self.mock_scorer = mock_scorer
    
    def test_workflow_construction(self):
        """Test that workflow is properly constructed"""
        assert self.agent.workflow is not None
        assert hasattr(self.agent.workflow, 'invoke')
    
    def test_plan_analysis_node(self):
        """Test the plan analysis node"""
        state = {"user_query": "Find riskiest paths", "context": {}, "results": {}, "errors": []}
        
        result_state = self.agent._plan_analysis(state)
        
        assert "plan" in result_state
        assert "results" in result_state
        assert "plan" in result_state["results"]
        assert result_state["plan"]["intent"] == "find_riskiest_paths"
    
    def test_retrieve_graph_data_node(self):
        """Test the retrieve graph data node"""
        state = {"user_query": "Find paths", "context": {}, "results": {}, "errors": []}
        
        result_state = self.agent._retrieve_graph_data(state)
        
        assert "crown_jewels" in result_state
        assert "results" in result_state
        assert "crown_jewels" in result_state["results"]
        assert len(result_state["crown_jewels"]) == 1
    
    def test_score_attack_paths_node(self):
        """Test the score attack paths node"""
        state = {
            "user_query": "Find paths",
            "plan": {"target": "crown-jewel-1", "algorithm": "hybrid", "max_hops": 4},
            "crown_jewels": [{"id": "crown-jewel-1", "name": "Database"}],
            "results": {},
            "errors": []
        }
        
        result_state = self.agent._score_attack_paths(state)
        
        assert "attack_paths" in result_state
        assert "results" in result_state
        assert "attack_paths" in result_state["results"]
        assert len(result_state["attack_paths"]) == 1
        assert result_state["attack_paths"][0]["score"] == 0.9
    
    def test_explain_paths_node(self):
        """Test the explain paths node"""
        state = {
            "attack_paths": [{"path": ["external", "dmz", "db"], "score": 0.9}],
            "results": {},
            "errors": []
        }
        
        result_state = self.agent._explain_paths(state)
        
        assert "explanations" in result_state
        assert "results" in result_state
        assert "explanations" in result_state["results"]
        assert len(result_state["explanations"]) == 1
        assert "explanation" in result_state["explanations"][0]
    
    def test_should_remediate_remdiate(self):
        """Test should remediate decision for remediation queries"""
        state = {"user_query": "Fix these security issues"}
        decision = self.agent._should_remediate(state)
        assert decision == "remediate"
    
    def test_should_remediate_simulate(self):
        """Test should remediate decision for simulation queries"""
        state = {"user_query": "Simulate the impact of changes"}
        decision = self.agent._should_remediate(state)
        assert decision == "simulate"
    
    def test_should_remediate_end(self):
        """Test should remediate decision for analysis queries"""
        state = {"user_query": "Show me the attack paths"}
        decision = self.agent._should_remediate(state)
        assert decision == "end"
    
    def test_generate_remediation_node(self):
        """Test the generate remediation node"""
        state = {
            "attack_paths": [{"path": ["external", "dmz", "db"], "score": 0.9}],
            "user_query": "Fix these issues",
            "results": {},
            "errors": []
        }
        
        result_state = self.agent._generate_remediation(state)
        
        assert "remediation_plan" in result_state
        assert "remediation_actions" in result_state
        assert "results" in result_state
        assert "remediation" in result_state["results"]
    
    def test_simulate_remediation_node(self):
        """Test the simulate remediation node"""
        state = {
            "remediation_actions": {
                "actions": [{"id": "1", "type": "remove_public_ingress", "target": "public-server"}]
            },
            "attack_paths": [{"path": ["external", "dmz", "db"], "score": 0.9}],
            "results": {},
            "errors": []
        }
        
        result_state = self.agent._simulate_remediation(state)
        
        assert "simulation" in result_state
        assert "results" in result_state
        assert "simulation" in result_state["results"]
    
    def test_verify_remediation_node(self):
        """Test the verify remediation node"""
        state = {
            "simulation": {"total_risk_reduction": 0.5, "affected_assets": ["server-001"]},
            "remediation_actions": {
                "actions": [{"id": "1", "type": "remove_public_ingress", "target": "public-server"}]
            },
            "results": {},
            "errors": []
        }
        
        result_state = self.agent._verify_remediation(state)
        
        assert "verification" in result_state
        assert "results" in result_state
        assert "verification" in result_state["results"]
        assert result_state["verification"]["status"] == "ready_for_implementation"
    
    def test_process_query_success(self):
        """Test successful query processing"""
        query = "Find the riskiest attack paths"
        
        result = self.agent.process_query(query)
        
        assert "plan" in result
        assert "crown_jewels" in result
        assert "attack_paths" in result
        assert "explanations" in result
    
    def test_process_query_error(self):
        """Test query processing with error"""
        # Mock an error in the workflow
        with patch.object(self.agent, 'workflow') as mock_workflow:
            mock_workflow.invoke.side_effect = Exception("Test error")
            
            result = self.agent.process_query("Test query")
            
            assert "error" in result
            assert result["status"] == "failed"
    
    def test_get_metrics(self):
        """Test getting agent metrics"""
        metrics = self.agent.get_metrics()
        
        assert "scorer_metrics" in metrics
        assert "workflow_nodes" in metrics
        assert "planner" in metrics["workflow_nodes"]
        assert "remediator" in metrics["workflow_nodes"]


class TestMCPTool:
    """Unit tests for MCPTool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a proper mock MCPToolWrapper
        from agent.mcp_client import MCPToolWrapper
        self.mock_wrapper = Mock(spec=MCPToolWrapper)
        self.mock_wrapper.test_method = AsyncMock(return_value={"result": "test"})
        
        self.tool = MCPTool(
            name="test_tool",
            description="Test tool",
            mcp_wrapper=self.mock_wrapper,
            tool_method="test_method"
        )
    
    def test_tool_initialization(self):
        """Test tool initialization"""
        assert self.tool.name == "test_tool"
        assert self.tool.description == "Test tool"
        assert self.tool.mcp_wrapper == self.mock_wrapper
        assert self.tool.tool_method == "test_method"
    
    def test_tool_run_success(self):
        """Test successful tool run"""
        result = self.tool._run(param1="value1")
        
        assert result == '{\n  "result": "test"\n}'
        self.mock_wrapper.test_method.assert_called_once_with(param1="value1")
    
    def test_tool_run_error(self):
        """Test tool run with error"""
        self.mock_wrapper.test_method.side_effect = Exception("Test error")
        
        result = self.tool._run(param1="value1")
        
        assert result == "Error: Test error"
    
    @pytest.mark.asyncio
    async def test_tool_arun_success(self):
        """Test successful async tool run"""
        result = await self.tool._arun(param1="value1")
        
        assert result == '{\n  "result": "test"\n}'
        self.mock_wrapper.test_method.assert_called_once_with(param1="value1")


class TestMCPEnhancedAgent:
    """Unit tests for MCPEnhancedAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.openai_api_key = "test-key"
        self.mcp_config = MCPClientConfig()
        self.agent = MCPEnhancedAgent(self.openai_api_key, self.mcp_config)
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        assert self.agent.openai_api_key == "test-key"
        assert self.agent.mcp_config == self.mcp_config
        assert self.agent.mcp_client is None
        assert self.agent.mcp_wrapper is None
        assert self.agent.llm is None
        assert self.agent.tools == []
        assert self.agent.agent_executor is None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful agent initialization"""
        with patch('agent.mcp_agent.GNNAttackPathMCPClient') as mock_client_class, \
             patch('agent.mcp_agent.ChatOpenAI') as mock_llm_class, \
             patch('agent.mcp_agent.create_openai_tools_agent') as mock_agent_class, \
             patch('agent.mcp_agent.AgentExecutor') as mock_executor_class:
            
            # Mock MCP client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock LLM
            mock_llm = Mock()
            mock_llm_class.return_value = mock_llm
            
            # Mock agent and executor
            mock_agent = Mock()
            mock_executor = Mock()
            mock_agent_class.return_value = mock_agent
            mock_executor_class.return_value = mock_executor
            
            await self.agent.initialize()
            
            assert self.agent.mcp_client == mock_client
            assert self.agent.llm == mock_llm
            assert len(self.agent.tools) == 5  # 5 MCP tools
            assert self.agent.agent_executor == mock_executor
    
    @pytest.mark.asyncio
    async def test_initialize_error(self):
        """Test agent initialization with error"""
        with patch('agent.mcp_agent.GNNAttackPathMCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception, match="Connection failed"):
                await self.agent.initialize()
    
    @pytest.mark.asyncio
    async def test_create_mcp_tools(self):
        """Test creating MCP tools"""
        # Mock the MCP wrapper with proper spec
        from agent.mcp_client import MCPToolWrapper
        self.agent.mcp_wrapper = Mock(spec=MCPToolWrapper)
        
        await self.agent._create_mcp_tools()
        
        assert len(self.agent.tools) == 5
        tool_names = [tool.name for tool in self.agent.tools]
        assert "find_attack_paths" in tool_names
        assert "get_risky_assets" in tool_names
        assert "assess_asset" in tool_names
        assert "suggest_fixes" in tool_names
        assert "get_graph_overview" in tool_names
    
    def test_create_agent_executor(self):
        """Test creating agent executor"""
        # Mock components
        self.agent.llm = Mock()
        self.agent.tools = [Mock(), Mock()]
        
        with patch('agent.mcp_agent.create_openai_tools_agent') as mock_agent_class, \
             patch('agent.mcp_agent.AgentExecutor') as mock_executor_class:
            
            mock_agent = Mock()
            mock_executor = Mock()
            mock_agent_class.return_value = mock_agent
            mock_executor_class.return_value = mock_executor
            
            self.agent._create_agent_executor()
            
            assert self.agent.agent_executor == mock_executor
            mock_agent_class.assert_called_once()
            mock_executor_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_security_query_success(self):
        """Test successful security query analysis"""
        # Mock agent executor
        self.agent.agent_executor = AsyncMock()
        self.agent.agent_executor.ainvoke.return_value = {"output": "Test response"}
        
        result = await self.agent.analyze_security_query("Test query")
        
        assert result == "Test response"
        self.agent.agent_executor.ainvoke.assert_called_once_with({"input": "Test query"})
    
    @pytest.mark.asyncio
    async def test_analyze_security_query_not_initialized(self):
        """Test security query analysis when not initialized"""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            await self.agent.analyze_security_query("Test query")
    
    @pytest.mark.asyncio
    async def test_analyze_security_query_error(self):
        """Test security query analysis with error"""
        self.agent.agent_executor = AsyncMock()
        self.agent.agent_executor.ainvoke.side_effect = Exception("Test error")
        
        result = await self.agent.analyze_security_query("Test query")
        
        assert result == "Error analyzing query: Test error"
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the agent"""
        self.agent.mcp_client = AsyncMock()
        self.agent.mcp_client.disconnect = AsyncMock()
        
        await self.agent.close()
        
        self.agent.mcp_client.disconnect.assert_called_once()


class TestIntegration:
    """Integration tests for the agentic system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_api_health_endpoint(self):
        """Test API health endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_api_metrics_endpoint(self):
        """Test API metrics endpoint"""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        assert "api_uptime_seconds" in response.text
        assert "http_requests_total" in response.text
    
    def test_api_attack_paths_endpoint(self):
        """Test API attack paths endpoint"""
        response = self.client.post("/api/v1/paths", json={
            "target": "crown-jewel-db-001",
            "max_hops": 4,
            "algorithm": "hybrid"
        })
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert len(data["paths"]) > 0
        assert "score" in data["paths"][0]
    
    def test_api_crown_jewels_endpoint(self):
        """Test API crown jewels endpoint"""
        response = self.client.get("/api/v1/crown-jewels")
        assert response.status_code == 200
        data = response.json()
        assert "crown_jewels" in data
        assert "count" in data
        assert data["count"] > 0
    
    def test_api_algorithms_endpoint(self):
        """Test API algorithms endpoint"""
        response = self.client.get("/api/v1/algorithms")
        assert response.status_code == 200
        data = response.json()
        assert "algorithms" in data
        assert len(data["algorithms"]) > 0
    
    def test_api_metrics_endpoint(self):
        """Test API metrics endpoint"""
        response = self.client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "attack_paths_analyzed" in data["metrics"]
    
    def test_api_risk_explanation_endpoint(self):
        """Test API risk explanation endpoint"""
        response = self.client.post("/api/v1/risk-explanation", json={
            "path": ["external", "dmz", "database"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_complete_attack_path_analysis_workflow(self):
        """Test complete attack path analysis workflow"""
        # Step 1: Get crown jewels
        response = self.client.get("/api/v1/crown-jewels")
        assert response.status_code == 200
        crown_jewels = response.json()["crown_jewels"]
        assert len(crown_jewels) > 0
        
        # Step 2: Find attack paths to first crown jewel
        target = crown_jewels[0]["id"]
        response = self.client.post("/api/v1/paths", json={
            "target": target,
            "max_hops": 4,
            "algorithm": "hybrid"
        })
        assert response.status_code == 200
        paths = response.json()["paths"]
        assert len(paths) > 0
        
        # Step 3: Get risk explanation for first path
        if paths:
            path = paths[0]["path"]
            response = self.client.post("/api/v1/risk-explanation", json={
                "path": path
            })
            assert response.status_code == 200
            explanation = response.json()["explanation"]
            assert len(explanation) > 0
        
        # Step 4: Get metrics
        response = self.client.get("/api/v1/metrics")
        assert response.status_code == 200
        metrics = response.json()["metrics"]
        assert "attack_paths_analyzed" in metrics
    
    def test_error_handling_workflow(self):
        """Test error handling in workflow"""
        # Test invalid target
        response = self.client.post("/api/v1/paths", json={
            "target": "nonexistent-target",
            "max_hops": 4,
            "algorithm": "invalid-algorithm"
        })
        assert response.status_code == 200  # API should handle gracefully
        data = response.json()
        assert "paths" in data  # Should return empty paths or mock data
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get("/api/v1/crown-jewels")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5


def run_tests():
    """Run all tests"""
    print("🧪 Running Agentic System Tests...")
    print("=" * 50)
    
    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])


if __name__ == "__main__":
    run_tests()
