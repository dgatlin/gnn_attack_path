"""
LangGraph-based planner for attack path analysis and remediation.
"""
from typing import Dict, List, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import json
import structlog

logger = structlog.get_logger(__name__)


class AttackPathPlanner:
    """
    Plans attack path analysis and remediation workflows.
    Uses GPT-3.5-turbo for fast intent parsing and query understanding.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        try:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0.1)
            self.use_llm = True
            logger.info("Planner Agent initialized", model=model_name, agent="planner")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}. Falling back to rule-based mode.")
            self.llm = None
            self.use_llm = False
        self.conversation_history = []
        self.model_name = model_name
    
    def plan_analysis(self, user_query: str) -> Dict[str, Any]:
        """Plan attack path analysis based on user query."""
        logger.info("Planning attack path analysis", query=user_query, use_llm=self.use_llm)
        
        if self.use_llm and self.llm:
            # Use LLM for intelligent query understanding
            return self._plan_analysis_with_llm(user_query)
        else:
            # Fallback to rule-based logic
            return self._plan_analysis_rule_based(user_query)
    
    def _plan_analysis_with_llm(self, user_query: str) -> Dict[str, Any]:
        """Use LLM to plan attack path analysis."""
        try:
            prompt = f"""You are a cybersecurity analyst assistant. Analyze this user query about attack paths and security risks.

User Query: "{user_query}"

Available crown jewel assets:
- asset-171 (crown-jewel-db-171): Database
- asset-099 (crown-jewel-bucket-099): Storage bucket  
- asset-170 (crown-jewel-vm-170): Virtual machine
- asset-048 (crown-jewel-role-048): IAM role
- asset-071 (crown-jewel-policy-071): IAM policy
- asset-144 (crown-jewel-subnet-144): Network subnet

Extract the following information and respond in JSON format:
{{
    "intent": "find_riskiest_paths | find_attack_paths | remediate_risks | simulate_changes | general_analysis",
    "target": "asset ID from the list above, or null if no specific target",
    "risk_threshold": float between 0.0 and 1.0,
    "max_hops": integer for maximum path length,
    "algorithm": "gnn | hybrid | dijkstra",
    "key_concerns": ["list", "of", "concerns"]
}}

Only respond with valid JSON, no other text."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse LLM response
            import json
            plan = json.loads(response.content)
            
            # Add actions based on intent
            plan["actions"] = self._generate_analysis_actions(plan["intent"])
            
            logger.info("LLM-generated analysis plan", plan=plan)
            return plan
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}. Falling back to rule-based.")
            return self._plan_analysis_rule_based(user_query)
    
    def _plan_analysis_rule_based(self, user_query: str) -> Dict[str, Any]:
        """Fallback rule-based planning when LLM is unavailable."""
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
        
        logger.info("Rule-based analysis plan generated", plan=plan)
        return plan
    
    def plan_remediation(self, attack_paths: List[Dict], user_query: str) -> Dict[str, Any]:
        """Plan remediation actions based on attack paths and user query."""
        logger.info("Planning remediation", paths_count=len(attack_paths), use_llm=self.use_llm)
        
        if self.use_llm and self.llm:
            # Use LLM for intelligent remediation planning
            return self._plan_remediation_with_llm(attack_paths, user_query)
        else:
            # Fallback to rule-based logic
            return self._plan_remediation_rule_based(attack_paths, user_query)
    
    def _plan_remediation_with_llm(self, attack_paths: List[Dict], user_query: str) -> Dict[str, Any]:
        """Use LLM to plan remediation actions."""
        try:
            # Summarize attack paths for LLM
            paths_summary = []
            for i, path in enumerate(attack_paths[:5], 1):  # Top 5 paths
                paths_summary.append({
                    "path_id": i,
                    "path": path.get("path", []),
                    "risk_score": path.get("score", 0),
                    "vulnerabilities": path.get("vulnerabilities", [])
                })
            
            prompt = f"""You are a cybersecurity remediation expert. Based on these attack paths, recommend remediation actions.

User Query: "{user_query}"

Attack Paths (Top 5):
{json.dumps(paths_summary, indent=2)}

Provide a remediation plan in JSON format:
{{
    "target_risk_reduction": float (0.0-1.0),
    "blast_radius_constraint": "minimal | limited | moderate",
    "priority_actions": [
        {{
            "action": "action_name",
            "description": "what to do",
            "impact": "high | medium | low",
            "effort": "high | medium | low",
            "rationale": "why this action"
        }}
    ],
    "simulation_required": true,
    "approval_required": true
}}

Only respond with valid JSON, no other text."""

            import json
            response = self.llm.invoke([HumanMessage(content=prompt)])
            remediation_plan = json.loads(response.content)
            
            logger.info("LLM-generated remediation plan", plan=remediation_plan)
            return remediation_plan
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}. Falling back to rule-based.")
            return self._plan_remediation_rule_based(attack_paths, user_query)
    
    def _plan_remediation_rule_based(self, attack_paths: List[Dict], user_query: str) -> Dict[str, Any]:
        """Fallback rule-based remediation planning."""
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
        
        logger.info("Rule-based remediation plan generated", plan=remediation_plan)
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
        query_lower = query.lower()
        
        # Map common terms to actual crown jewel IDs from our database
        if "crown jewel" in query_lower or "crown-jewel" in query_lower:
            return "asset-171"  # crown-jewel-db-171
        elif "database" in query_lower or "db" in query_lower:
            return "asset-171"  # crown-jewel-db-171
        elif "bucket" in query_lower or "storage" in query_lower:
            return "asset-099"  # crown-jewel-bucket-099
        elif "vm" in query_lower or "virtual machine" in query_lower:
            return "asset-170"  # crown-jewel-vm-170
        elif "role" in query_lower:
            return "asset-048"  # crown-jewel-role-048
        elif "policy" in query_lower:
            return "asset-071"  # crown-jewel-policy-071
        elif "subnet" in query_lower or "network" in query_lower:
            return "asset-144"  # crown-jewel-subnet-144
        elif "critical" in query_lower:
            return "asset-171"  # Default to database
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
