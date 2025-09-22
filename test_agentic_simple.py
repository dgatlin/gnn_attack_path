#!/usr/bin/env python3
"""
Simplified Agentic System Test Suite

This test suite focuses on testing the core agentic functionality
without requiring external dependencies like OpenAI API keys or Neo4j.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent components
from agent.planner import AttackPathPlanner
from agent.remediator import RemediationAgent

# Import API components
from api.main import app
from fastapi.testclient import TestClient


class TestAgenticCore:
    """Test core agentic functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_planner_intent_recognition(self):
        """Test intent recognition without LLM dependency"""
        # Test intent parsing methods directly
        planner = AttackPathPlanner.__new__(AttackPathPlanner)  # Create without __init__
        
        # Test intent parsing
        assert planner._parse_intent("What are the riskiest attack paths?") == "find_riskiest_paths"
        assert planner._parse_intent("Show me attack paths to the database") == "find_attack_paths"
        assert planner._parse_intent("How can I fix these security issues?") == "remediate_risks"
        assert planner._parse_intent("Simulate the impact of changes") == "simulate_changes"
        assert planner._parse_intent("General query") == "general_analysis"
    
    def test_planner_target_extraction(self):
        """Test target extraction"""
        planner = AttackPathPlanner.__new__(AttackPathPlanner)
        
        # Test target extraction
        assert planner._extract_target("Find paths to crown jewel") == "crown-jewel-db-001"
        assert planner._extract_target("Show paths to database") == "db-payments"
        assert planner._extract_target("Find critical assets") == "critical-asset"
        assert planner._extract_target("General query") is None
    
    def test_planner_algorithm_selection(self):
        """Test algorithm selection"""
        planner = AttackPathPlanner.__new__(AttackPathPlanner)
        
        # Test algorithm selection
        assert planner._select_algorithm("find_riskiest_paths") == "hybrid"
        assert planner._select_algorithm("find_attack_paths") == "gnn"
        assert planner._select_algorithm("remediate_risks") == "hybrid"
        assert planner._select_algorithm("simulate_changes") == "hybrid"
    
    def test_remediator_path_analysis(self):
        """Test remediation path analysis"""
        remediator = RemediationAgent()
        
        paths = [
            {"path": ["external", "dmz", "db"], "score": 0.9},
            {"path": ["internal", "db"], "score": 0.6}
        ]
        
        analysis = remediator._analyze_paths_for_remediation(paths)
        
        assert "high_risk_paths" in analysis
        assert "common_vulnerabilities" in analysis
        assert "network_issues" in analysis
        assert "iam_issues" in analysis
        assert "patch_requirements" in analysis
        assert len(analysis["high_risk_paths"]) == 1  # Only the 0.9 score path
    
    def test_remediator_action_generation(self):
        """Test remediation action generation"""
        remediator = RemediationAgent()
        
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
        
        actions = remediator._generate_remediation_actions(analysis, constraints)
        
        assert len(actions) > 0
        assert any(action["type"] == "remove_public_ingress" for action in actions)
        assert any(action["type"] == "apply_patch" for action in actions)
        assert any(action["type"] == "revoke_iam_permission" for action in actions)
    
    def test_remediator_action_prioritization(self):
        """Test action prioritization"""
        remediator = RemediationAgent()
        
        actions = [
            {"id": "1", "impact": 3, "effort": 1, "type": "remove_public_ingress"},  # ratio = 3
            {"id": "2", "impact": 2, "effort": 3, "type": "apply_patch"},  # ratio = 0.67
            {"id": "3", "impact": 3, "effort": 2, "type": "revoke_iam_permission"}  # ratio = 1.5
        ]
        constraints = {"max_actions": 2}
        
        prioritized = remediator._prioritize_actions(actions, constraints)
        
        assert len(prioritized) == 2
        assert prioritized[0]["id"] == "1"  # Highest impact/effort ratio (3.0)
        assert prioritized[1]["id"] == "3"  # Second highest (1.5)
    
    def test_remediator_simulation(self):
        """Test remediation simulation"""
        remediator = RemediationAgent()
        
        actions = [
            {"id": "1", "type": "remove_public_ingress", "target": "public-server"},
            {"id": "2", "type": "apply_patch", "target": "server-001"}
        ]
        current_paths = [{"path": ["external", "dmz", "db"], "score": 0.9}]
        
        simulation = remediator.simulate_remediation(actions, current_paths)
        
        assert "simulation_results" in simulation
        assert "total_risk_reduction" in simulation
        assert "affected_assets" in simulation
        assert "success_rate" in simulation
        assert "recommendations" in simulation
        assert simulation["total_risk_reduction"] == 0.7  # 0.4 + 0.3
        assert simulation["success_rate"] == 1.0  # Both actions successful
    
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
    
    def test_api_metrics_json_endpoint(self):
        """Test API metrics JSON endpoint"""
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
    
    def test_complete_workflow(self):
        """Test complete attack path analysis workflow"""
        # Step 1: Get crown jewels
        response = self.client.get("/api/v1/crown-jewels")
        assert response.status_code == 200
        crown_jewels = response.json()["crown_jewels"]
        assert len(crown_jewels) > 0
        
        # Step 2: Find attack paths to a known target
        target = "crown-jewel-db-001"  # Use known target instead of dynamic
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
    
    def test_error_handling(self):
        """Test error handling in workflow"""
        # Test invalid target
        response = self.client.post("/api/v1/paths", json={
            "target": "nonexistent-target",
            "max_hops": 4,
            "algorithm": "invalid-algorithm"
        })
        assert response.status_code == 200  # API should handle gracefully
        data = response.json()
        assert "paths" in data  # Should return mock data
    
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


def run_simple_tests():
    """Run simplified tests"""
    print("🧪 Running Simplified Agentic System Tests...")
    print("=" * 50)
    
    # Run pytest
    pytest.main([
        "test_agentic_simple.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ])


if __name__ == "__main__":
    run_simple_tests()
