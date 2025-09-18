"""
LangGraph-based planner for attack path analysis and remediation.
"""
from typing import Dict, List, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import structlog

logger = structlog.get_logger(__name__)


class AttackPathPlanner:
    """Plans attack path analysis and remediation workflows."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = ChatOpenAI(model_name=model_name, temperature=0.1)
        self.conversation_history = []
    
    def plan_analysis(self, user_query: str) -> Dict[str, Any]:
        """Plan attack path analysis based on user query."""
        logger.info("Planning attack path analysis", query=user_query)
        
        # Parse user intent
        intent = self._parse_intent(user_query)
        
        # Generate analysis plan
        plan = {
            "intent": intent,
            "target": self._extract_target(user_query),
            "risk_threshold": self._extract_risk_threshold(user_query),
            "max_hops": self._extract_max_hops(user_query),
            "algorithm": self._select_algorithm(intent),
            "actions": self._generate_analysis_actions(intent)
        }
        
        logger.info("Analysis plan generated", plan=plan)
        return plan
    
    def plan_remediation(self, attack_paths: List[Dict], user_query: str) -> Dict[str, Any]:
        """Plan remediation actions based on attack paths and user query."""
        logger.info("Planning remediation", paths_count=len(attack_paths))
        
        # Analyze attack paths
        path_analysis = self._analyze_attack_paths(attack_paths)
        
        # Generate remediation plan
        remediation_plan = {
            "target_risk_reduction": self._extract_risk_reduction_target(user_query),
            "blast_radius_constraint": self._extract_blast_radius(user_query),
            "priority_actions": self._prioritize_actions(path_analysis),
            "simulation_required": True,
            "approval_required": True
        }
        
        logger.info("Remediation plan generated", plan=remediation_plan)
        return remediation_plan
    
    def _parse_intent(self, query: str) -> str:
        """Parse user intent from query."""
        query_lower = query.lower()
        
        if "riskiest" in query_lower or "highest risk" in query_lower:
            return "find_riskiest_paths"
        elif "attack path" in query_lower or "path to" in query_lower:
            return "find_attack_paths"
        elif "fix" in query_lower or "remediate" in query_lower or "reduce risk" in query_lower:
            return "remediate_risks"
        elif "simulate" in query_lower:
            return "simulate_changes"
        else:
            return "general_analysis"
    
    def _extract_target(self, query: str) -> Optional[str]:
        """Extract target asset from query."""
        # Simple extraction - in practice, use NER
        if "crown jewel" in query.lower():
            return "crown-jewel-db-001"
        elif "database" in query.lower():
            return "db-payments"
        elif "critical" in query.lower():
            return "critical-asset"
        return None
    
    def _extract_risk_threshold(self, query: str) -> float:
        """Extract risk threshold from query."""
        # Default threshold
        return 0.7
    
    def _extract_max_hops(self, query: str) -> int:
        """Extract maximum hops from query."""
        # Default max hops
        return 4
    
    def _select_algorithm(self, intent: str) -> str:
        """Select appropriate scoring algorithm based on intent."""
        if intent == "find_riskiest_paths":
            return "hybrid"
        elif intent == "find_attack_paths":
            return "gnn"
        else:
            return "hybrid"
    
    def _generate_analysis_actions(self, intent: str) -> List[str]:
        """Generate analysis actions based on intent."""
        actions = ["load_graph_data", "find_entry_points", "score_paths"]
        
        if intent == "find_riskiest_paths":
            actions.extend(["rank_by_risk", "generate_explanations"])
        elif intent == "find_attack_paths":
            actions.extend(["find_all_paths", "filter_by_target"])
        
        return actions
    
    def _analyze_attack_paths(self, paths: List[Dict]) -> Dict[str, Any]:
        """Analyze attack paths to identify remediation opportunities."""
        if not paths:
            return {"critical_issues": [], "remediation_candidates": []}
        
        critical_issues = []
        remediation_candidates = []
        
        for path in paths:
            # Identify critical issues
            if path.get('score', 0) > 0.8:
                critical_issues.append({
                    "path": path.get('path', []),
                    "score": path.get('score', 0),
                    "issues": self._identify_path_issues(path)
                })
            
            # Identify remediation candidates
            candidates = self._identify_remediation_candidates(path)
            remediation_candidates.extend(candidates)
        
        return {
            "critical_issues": critical_issues,
            "remediation_candidates": remediation_candidates
        }
    
    def _identify_path_issues(self, path: Dict) -> List[str]:
        """Identify specific issues in an attack path."""
        issues = []
        
        if path.get('score', 0) > 0.9:
            issues.append("Very high risk path")
        
        if len(path.get('path', [])) > 3:
            issues.append("Complex multi-hop attack")
        
        # Add more specific issue detection
        return issues
    
    def _identify_remediation_candidates(self, path: Dict) -> List[Dict]:
        """Identify potential remediation actions for a path."""
        candidates = []
        
        # Example remediation candidates
        if "public" in str(path.get('path', [])):
            candidates.append({
                "action": "remove_public_ingress",
                "description": "Remove public internet access",
                "impact": "high",
                "effort": "low"
            })
        
        if "vulnerability" in str(path.get('path', [])):
            candidates.append({
                "action": "apply_patch",
                "description": "Apply security patches",
                "impact": "high",
                "effort": "medium"
            })
        
        return candidates
    
    def _extract_risk_reduction_target(self, query: str) -> float:
        """Extract target risk reduction percentage from query."""
        import re
        
        # Look for percentage patterns
        match = re.search(r'(\d+)%', query)
        if match:
            return float(match.group(1)) / 100.0
        
        # Default target
        return 0.8
    
    def _extract_blast_radius(self, query: str) -> str:
        """Extract blast radius constraint from query."""
        query_lower = query.lower()
        
        if "minimal" in query_lower or "small" in query_lower:
            return "minimal"
        elif "limited" in query_lower:
            return "limited"
        else:
            return "moderate"
    
    def _prioritize_actions(self, analysis: Dict) -> List[Dict]:
        """Prioritize remediation actions based on analysis."""
        candidates = analysis.get("remediation_candidates", [])
        
        # Sort by impact/effort ratio
        prioritized = sorted(candidates, 
                           key=lambda x: x.get("impact", 0) / max(x.get("effort", 1), 1), 
                           reverse=True)
        
        return prioritized[:5]  # Top 5 actions
