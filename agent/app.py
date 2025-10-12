"""
Main agent application using LangGraph for orchestration.
Multi-agent system with specialized LLMs:
- Planner Agent: GPT-3.5-turbo for fast intent parsing
- Explainer Agent: GPT-4 for detailed risk explanations  
- Remediator Agent: GPT-4 for complex remediation planning
"""
from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
import json
import structlog

from .planner import AttackPathPlanner
from .remediator import RemediationAgent
from scorer.service import AttackPathScoringService

logger = structlog.get_logger(__name__)


class AttackPathAgent:
    """
    Main agent orchestrating attack path analysis and remediation.
    Uses specialized LLMs for different tasks.
    """
    
    def __init__(self, gnn_model_path: Optional[str] = None):
        # Initialize specialized agents
        self.planner = AttackPathPlanner(model_name="gpt-3.5-turbo")  # Fast intent parsing
        self.remediator = RemediationAgent(model_name="gpt-4")        # Complex remediation
        self.scorer = AttackPathScoringService(gnn_model_path)
        
        # Initialize Explainer LLM (GPT-4 for detailed explanations)
        try:
            self.explainer_llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
            self.use_explainer_llm = True
            logger.info("Explainer Agent initialized", model="gpt-4", agent="explainer")
        except Exception as e:
            logger.warning(f"Failed to initialize Explainer LLM: {e}. Using rule-based explanations.")
            self.explainer_llm = None
            self.use_explainer_llm = False
        
        # Build the agent workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("planner", self._plan_analysis)
        workflow.add_node("retriever", self._retrieve_graph_data)
        workflow.add_node("scorer", self._score_attack_paths)
        workflow.add_node("explainer", self._explain_paths)
        workflow.add_node("remediator", self._generate_remediation)
        workflow.add_node("simulator", self._simulate_remediation)
        workflow.add_node("verifier", self._verify_remediation)
        
        # Define the flow
        workflow.set_entry_point("planner")
        
        workflow.add_edge("planner", "retriever")
        workflow.add_edge("retriever", "scorer")
        workflow.add_edge("scorer", "explainer")
        
        # Conditional edges for remediation
        workflow.add_conditional_edges(
            "explainer",
            self._should_remediate,
            {
                "remediate": "remediator",
                "simulate": "simulator",
                "end": END
            }
        )
        
        workflow.add_edge("remediator", "simulator")
        workflow.add_edge("simulator", "verifier")
        workflow.add_edge("verifier", END)
        
        return workflow.compile()
    
    def process_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user query through the agent workflow."""
        logger.info("Processing user query", query=user_query)
        
        # Initialize state
        state = {
            "user_query": user_query,
            "context": context or {},
            "results": {},
            "errors": []
        }
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            logger.info("Query processed successfully", 
                       result_keys=list(final_state.get("results", {}).keys()))
            
            return final_state.get("results", {})
            
        except Exception as e:
            logger.error("Error processing query", error=str(e))
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _plan_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan the analysis based on user query."""
        user_query = state["user_query"]
        
        try:
            plan = self.planner.plan_analysis(user_query)
            state["plan"] = plan
            state["results"]["plan"] = plan
            
            logger.info("Analysis planned", plan=plan)
            
        except Exception as e:
            logger.error("Error in planning", error=str(e))
            state["errors"].append(f"Planning error: {str(e)}")
        
        return state
    
    def _retrieve_graph_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant graph data."""
        try:
            # Load graph data if not already loaded
            self.scorer.load_graph_data()
            
            # Get crown jewels for context
            crown_jewels = self.scorer.get_crown_jewels()
            state["crown_jewels"] = crown_jewels
            state["results"]["crown_jewels"] = crown_jewels
            
            logger.info("Graph data retrieved", crown_jewels_count=len(crown_jewels))
            
        except Exception as e:
            logger.error("Error retrieving graph data", error=str(e))
            state["errors"].append(f"Data retrieval error: {str(e)}")
        
        return state
    
    def _score_attack_paths(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Score attack paths using the selected algorithm."""
        plan = state.get("plan", {})
        target = plan.get("target")
        algorithm = plan.get("algorithm", "hybrid")
        max_hops = plan.get("max_hops", 4)
        
        try:
            if target:
                # Get paths to specific target
                paths = self.scorer.get_attack_paths(target, algorithm, max_hops, k=5)
            else:
                # Get paths to all crown jewels
                crown_jewels = state.get("crown_jewels", [])
                all_paths = []
                for jewel in crown_jewels:
                    jewel_paths = self.scorer.get_attack_paths(
                        jewel["id"], algorithm, max_hops, k=3
                    )
                    all_paths.extend(jewel_paths)
                
                # Sort by score and take top 5
                all_paths.sort(key=lambda x: x.get("score", 0), reverse=True)
                paths = all_paths[:5]
            
            state["attack_paths"] = paths
            state["results"]["attack_paths"] = paths
            
            logger.info("Attack paths scored", 
                       paths_count=len(paths),
                       algorithm=algorithm)
            
        except Exception as e:
            logger.error("Error scoring attack paths", error=str(e))
            state["errors"].append(f"Scoring error: {str(e)}")
            state["attack_paths"] = []
        
        return state
    
    def _explain_paths(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanations for attack paths using GPT-4."""
        paths = state.get("attack_paths", [])
        
        try:
            if self.use_explainer_llm and self.explainer_llm:
                explanations = self._explain_paths_with_llm(paths)
            else:
                explanations = self._explain_paths_rule_based(paths)
            
            state["explanations"] = explanations
            state["results"]["explanations"] = explanations
            
            logger.info("Path explanations generated", count=len(explanations), use_llm=self.use_explainer_llm)
            
        except Exception as e:
            logger.error("Error generating explanations", error=str(e))
            state["errors"].append(f"Explanation error: {str(e)}")
        
        return state
    
    def _explain_paths_with_llm(self, paths: List[Dict]) -> List[Dict]:
        """Use GPT-4 to generate human-readable risk explanations."""
        try:
            explanations = []
            
            for i, path in enumerate(paths[:5]):  # Top 5 paths
                prompt = f"""You are a cybersecurity expert explaining attack paths to security teams.

Attack Path #{i+1}:
- Path: {' → '.join(path.get('path', []))}
- Risk Score: {path.get('score', 0):.2%}
- Vulnerabilities: {', '.join(path.get('vulnerabilities', ['None identified']))}

Provide a clear, concise explanation covering:
1. What makes this path risky (2-3 sentences)
2. Key vulnerabilities and their impact
3. Potential attack scenario
4. Recommended immediate actions

Keep it professional but accessible. Format as a structured explanation."""

                response = self.explainer_llm.invoke([HumanMessage(content=prompt)])
                
                explanations.append({
                    "path_id": i,
                    "path": path.get("path", []),
                    "score": path.get("score", 0),
                    "explanation": response.content,
                    "vulnerabilities": path.get("vulnerabilities", [])
                })
            
            logger.info("LLM-generated explanations", count=len(explanations))
            return explanations
            
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}. Falling back to rule-based.")
            return self._explain_paths_rule_based(paths)
    
    def _explain_paths_rule_based(self, paths: List[Dict]) -> List[Dict]:
        """Fallback rule-based explanations."""
        explanations = []
        for i, path in enumerate(paths):
            explanation = self.scorer.get_risk_explanation(path.get("path", []))
            explanations.append({
                "path_id": i,
                "path": path.get("path", []),
                "score": path.get("score", 0),
                "explanation": explanation
            })
        return explanations
    
    def _should_remediate(self, state: Dict[str, Any]) -> str:
        """Determine if remediation should be performed."""
        user_query = state.get("user_query", "").lower()
        
        if "fix" in user_query or "remediate" in user_query or "reduce risk" in user_query:
            return "remediate"
        elif "simulate" in user_query:
            return "simulate"
        else:
            return "end"
    
    def _generate_remediation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate remediation plan."""
        paths = state.get("attack_paths", [])
        user_query = state.get("user_query", "")
        
        try:
            # Plan remediation
            remediation_plan = self.planner.plan_remediation(paths, user_query)
            
            # Generate specific actions
            constraints = {
                "max_actions": 5,
                "blast_radius": remediation_plan.get("blast_radius_constraint", "moderate")
            }
            
            remediation_actions = self.remediator.generate_remediation_plan(
                paths, constraints
            )
            
            state["remediation_plan"] = remediation_plan
            state["remediation_actions"] = remediation_actions
            state["results"]["remediation"] = {
                "plan": remediation_plan,
                "actions": remediation_actions
            }
            
            logger.info("Remediation plan generated", 
                       actions_count=len(remediation_actions.get("actions", [])))
            
        except Exception as e:
            logger.error("Error generating remediation", error=str(e))
            state["errors"].append(f"Remediation error: {str(e)}")
        
        return state
    
    def _simulate_remediation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate remediation effects."""
        actions = state.get("remediation_actions", {}).get("actions", [])
        paths = state.get("attack_paths", [])
        
        try:
            if actions:
                simulation = self.remediator.simulate_remediation(actions, paths)
                state["simulation"] = simulation
                state["results"]["simulation"] = simulation
                
                logger.info("Remediation simulated", 
                           risk_reduction=simulation.get("total_risk_reduction", 0))
            else:
                state["simulation"] = {"message": "No actions to simulate"}
            
        except Exception as e:
            logger.error("Error simulating remediation", error=str(e))
            state["errors"].append(f"Simulation error: {str(e)}")
        
        return state
    
    def _verify_remediation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify remediation effectiveness."""
        simulation = state.get("simulation", {})
        actions = state.get("remediation_actions", {}).get("actions", [])
        
        try:
            # Generate IaC diff
            if actions:
                iac_diff = self.remediator.generate_iac_diff(actions)
                state["iac_diff"] = iac_diff
                state["results"]["iac_diff"] = iac_diff
            
            # Generate verification report
            verification = {
                "status": "ready_for_implementation",
                "risk_reduction": simulation.get("total_risk_reduction", 0),
                "affected_assets": simulation.get("affected_assets", []),
                "recommendations": simulation.get("recommendations", []),
                "next_steps": [
                    "Review generated Terraform changes",
                    "Test in development environment",
                    "Schedule maintenance window",
                    "Implement changes with rollback plan"
                ]
            }
            
            state["verification"] = verification
            state["results"]["verification"] = verification
            
            logger.info("Remediation verified", 
                       status=verification["status"],
                       risk_reduction=verification["risk_reduction"])
            
        except Exception as e:
            logger.error("Error verifying remediation", error=str(e))
            state["errors"].append(f"Verification error: {str(e)}")
        
        return state
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            "scorer_metrics": self.scorer.get_metrics(),
            "workflow_nodes": ["planner", "retriever", "scorer", "explainer", 
                             "remediator", "simulator", "verifier"]
        }


def create_workflow(gnn_model_path: Optional[str] = None) -> StateGraph:
    """Create and return a compiled workflow for attack path analysis."""
    agent = AttackPathAgent(gnn_model_path)
    return agent.workflow
