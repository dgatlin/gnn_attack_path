"""
Remediation agent for generating and simulating security fixes.
"""
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class RemediationAgent:
    """Generates and simulates remediation actions for attack paths."""
    
    def __init__(self):
        self.remediation_templates = {
            "remove_public_ingress": self._generate_sg_rule_removal,
            "apply_patch": self._generate_patch_action,
            "revoke_iam_permission": self._generate_iam_revocation,
            "enable_mfa": self._generate_mfa_enforcement,
            "network_segmentation": self._generate_network_segmentation
        }
    
    def generate_remediation_plan(self, attack_paths: List[Dict], 
                                constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive remediation plan."""
        logger.info("Generating remediation plan", 
                   paths_count=len(attack_paths),
                   constraints=constraints)
        
        # Analyze attack paths
        path_analysis = self._analyze_paths_for_remediation(attack_paths)
        
        # Generate remediation actions
        actions = self._generate_remediation_actions(path_analysis, constraints)
        
        # Prioritize actions
        prioritized_actions = self._prioritize_actions(actions, constraints)
        
        # Generate implementation plan
        implementation_plan = self._generate_implementation_plan(prioritized_actions)
        
        return {
            "analysis": path_analysis,
            "actions": prioritized_actions,
            "implementation_plan": implementation_plan,
            "estimated_risk_reduction": self._estimate_risk_reduction(prioritized_actions),
            "estimated_effort": self._estimate_effort(prioritized_actions)
        }
    
    def simulate_remediation(self, actions: List[Dict], 
                           current_paths: List[Dict]) -> Dict[str, Any]:
        """Simulate the effect of remediation actions."""
        logger.info("Simulating remediation", actions_count=len(actions))
        
        # Simulate each action
        simulation_results = []
        for action in actions:
            result = self._simulate_single_action(action, current_paths)
            simulation_results.append(result)
        
        # Calculate overall impact
        total_risk_reduction = sum(r.get('risk_reduction', 0) for r in simulation_results)
        affected_assets = set()
        for result in simulation_results:
            affected_assets.update(result.get('affected_assets', []))
        
        return {
            "simulation_results": simulation_results,
            "total_risk_reduction": total_risk_reduction,
            "affected_assets": list(affected_assets),
            "success_rate": len([r for r in simulation_results if r.get('success', False)]) / len(actions),
            "recommendations": self._generate_simulation_recommendations(simulation_results)
        }
    
    def generate_iac_diff(self, actions: List[Dict]) -> Dict[str, Any]:
        """Generate Infrastructure as Code diff for remediation actions."""
        logger.info("Generating IaC diff", actions_count=len(actions))
        
        terraform_changes = []
        for action in actions:
            if action['type'] in self.remediation_templates:
                iac_change = self.remediation_templates[action['type']](action)
                terraform_changes.append(iac_change)
        
        return {
            "terraform_changes": terraform_changes,
            "summary": self._generate_iac_summary(terraform_changes),
            "validation_commands": self._generate_validation_commands(terraform_changes)
        }
    
    def _analyze_paths_for_remediation(self, paths: List[Dict]) -> Dict[str, Any]:
        """Analyze attack paths to identify remediation opportunities."""
        analysis = {
            "high_risk_paths": [],
            "common_vulnerabilities": [],
            "network_issues": [],
            "iam_issues": [],
            "patch_requirements": []
        }
        
        for path in paths:
            if path.get('score', 0) > 0.8:
                analysis["high_risk_paths"].append(path)
            
            # Analyze path components
            path_nodes = path.get('path', [])
            for i, node in enumerate(path_nodes):
                if i < len(path_nodes) - 1:
                    # Analyze edge between nodes
                    edge_analysis = self._analyze_edge(node, path_nodes[i+1])
                    analysis.update(edge_analysis)
        
        return analysis
    
    def _analyze_edge(self, source: str, target: str) -> Dict[str, Any]:
        """Analyze an edge for remediation opportunities."""
        analysis = {}
        
        # This would typically query the graph database
        # For now, return placeholder analysis
        if "public" in source.lower():
            analysis["network_issues"] = analysis.get("network_issues", []) + [{
                "issue": "Public exposure",
                "source": source,
                "target": target,
                "severity": "high"
            }]
        
        return analysis
    
    def _generate_remediation_actions(self, analysis: Dict, 
                                    constraints: Dict) -> List[Dict]:
        """Generate specific remediation actions based on analysis."""
        actions = []
        
        # Network security actions
        for issue in analysis.get("network_issues", []):
            if issue["severity"] == "high":
                actions.append({
                    "id": f"action_{len(actions)}",
                    "type": "remove_public_ingress",
                    "description": f"Remove public access from {issue['source']}",
                    "target": issue["source"],
                    "priority": "high",
                    "effort": "low",
                    "impact": "high"
                })
        
        # Patch management actions
        for vuln in analysis.get("common_vulnerabilities", []):
            actions.append({
                "id": f"action_{len(actions)}",
                "type": "apply_patch",
                "description": f"Apply patch for {vuln['cve']}",
                "target": vuln["asset"],
                "priority": "high",
                "effort": "medium",
                "impact": "high"
            })
        
        # IAM actions
        for issue in analysis.get("iam_issues", []):
            actions.append({
                "id": f"action_{len(actions)}",
                "type": "revoke_iam_permission",
                "description": f"Revoke excessive permissions from {issue['role']}",
                "target": issue["role"],
                "priority": "medium",
                "effort": "low",
                "impact": "medium"
            })
        
        return actions
    
    def _prioritize_actions(self, actions: List[Dict], 
                          constraints: Dict) -> List[Dict]:
        """Prioritize actions based on impact, effort, and constraints."""
        # Sort by impact/effort ratio
        def priority_score(action):
            impact = action.get("impact", 0)
            effort = action.get("effort", 1)
            return impact / max(effort, 1)
        
        prioritized = sorted(actions, key=priority_score, reverse=True)
        
        # Apply constraints
        max_actions = constraints.get("max_actions", 5)
        return prioritized[:max_actions]
    
    def _generate_implementation_plan(self, actions: List[Dict]) -> Dict[str, Any]:
        """Generate step-by-step implementation plan."""
        phases = {
            "immediate": [],  # Can be done immediately
            "short_term": [],  # Within 1 week
            "medium_term": []  # Within 1 month
        }
        
        for action in actions:
            effort = action.get("effort", "medium")
            if effort == "low":
                phases["immediate"].append(action)
            elif effort == "medium":
                phases["short_term"].append(action)
            else:
                phases["medium_term"].append(action)
        
        return {
            "phases": phases,
            "total_actions": len(actions),
            "estimated_timeline": self._estimate_timeline(phases)
        }
    
    def _estimate_risk_reduction(self, actions: List[Dict]) -> float:
        """Estimate total risk reduction from actions."""
        total_reduction = 0.0
        for action in actions:
            impact = action.get("impact", 0)
            if impact == "high":
                total_reduction += 0.3
            elif impact == "medium":
                total_reduction += 0.2
            else:
                total_reduction += 0.1
        
        return min(total_reduction, 1.0)  # Cap at 100%
    
    def _estimate_effort(self, actions: List[Dict]) -> Dict[str, int]:
        """Estimate effort required for actions."""
        effort_counts = {"low": 0, "medium": 0, "high": 0}
        for action in actions:
            effort = action.get("effort", "medium")
            effort_counts[effort] += 1
        
        return effort_counts
    
    def _estimate_timeline(self, phases: Dict) -> str:
        """Estimate implementation timeline."""
        if phases["immediate"]:
            return "Immediate - 1 week"
        elif phases["short_term"]:
            return "1-2 weeks"
        else:
            return "2-4 weeks"
    
    def _simulate_single_action(self, action: Dict, 
                              current_paths: List[Dict]) -> Dict[str, Any]:
        """Simulate the effect of a single remediation action."""
        # This is a simplified simulation
        # In practice, you'd modify the graph and re-run scoring
        
        action_type = action.get("type")
        risk_reduction = 0.0
        affected_assets = []
        
        if action_type == "remove_public_ingress":
            risk_reduction = 0.4
            affected_assets = [action.get("target", "unknown")]
        elif action_type == "apply_patch":
            risk_reduction = 0.3
            affected_assets = [action.get("target", "unknown")]
        elif action_type == "revoke_iam_permission":
            risk_reduction = 0.2
            affected_assets = [action.get("target", "unknown")]
        
        return {
            "action_id": action.get("id"),
            "success": True,
            "risk_reduction": risk_reduction,
            "affected_assets": affected_assets,
            "simulation_notes": f"Simulated {action_type} on {action.get('target')}"
        }
    
    def _generate_simulation_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations based on simulation results."""
        recommendations = []
        
        successful_actions = [r for r in results if r.get("success", False)]
        if len(successful_actions) == len(results):
            recommendations.append("All remediation actions are safe to implement")
        
        high_impact_actions = [r for r in successful_actions if r.get("risk_reduction", 0) > 0.3]
        if high_impact_actions:
            recommendations.append(f"{len(high_impact_actions)} high-impact actions identified")
        
        return recommendations
    
    def _generate_sg_rule_removal(self, action: Dict) -> Dict[str, Any]:
        """Generate Terraform for security group rule removal."""
        return {
            "resource_type": "aws_security_group_rule",
            "action": "destroy",
            "resource_name": f"sg_rule_{action.get('target')}",
            "terraform_code": f"""
# Remove public ingress rule
resource "aws_security_group_rule" "sg_rule_{action.get('target')}" {{
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.{action.get('target')}.id
  # This rule will be removed
}}
""",
            "description": f"Remove public ingress from {action.get('target')}"
        }
    
    def _generate_patch_action(self, action: Dict) -> Dict[str, Any]:
        """Generate patch management action."""
        return {
            "resource_type": "aws_ssm_patch_baseline",
            "action": "create",
            "resource_name": f"patch_{action.get('target')}",
            "terraform_code": f"""
# Apply security patches
resource "aws_ssm_patch_baseline" "patch_{action.get('target')}" {{
  name             = "security-patches-{action.get('target')}"
  description      = "Security patches for {action.get('target')}"
  operating_system = "AMAZON_LINUX_2"
  
  approval_rule {{
    approve_after_days = 0
    compliance_level   = "CRITICAL"
  }}
}}
""",
            "description": f"Apply security patches to {action.get('target')}"
        }
    
    def _generate_iam_revocation(self, action: Dict) -> Dict[str, Any]:
        """Generate IAM permission revocation."""
        return {
            "resource_type": "aws_iam_policy",
            "action": "update",
            "resource_name": f"policy_{action.get('target')}",
            "terraform_code": f"""
# Revoke excessive permissions
resource "aws_iam_policy" "policy_{action.get('target')}" {{
  name = "restricted-policy-{action.get('target')}"
  
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::specific-bucket/*"
      }}
    ]
  }})
}}
""",
            "description": f"Revoke excessive permissions from {action.get('target')}"
        }
    
    def _generate_mfa_enforcement(self, action: Dict) -> Dict[str, Any]:
        """Generate MFA enforcement policy."""
        return {
            "resource_type": "aws_iam_policy",
            "action": "create",
            "resource_name": f"mfa_policy_{action.get('target')}",
            "terraform_code": f"""
# Enforce MFA
resource "aws_iam_policy" "mfa_policy_{action.get('target')}" {{
  name = "mfa-enforcement-{action.get('target')}"
  
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Deny"
        NotAction = [
          "iam:CreateVirtualMFADevice",
          "iam:EnableMFADevice",
          "iam:GetUser",
          "iam:ListMFADevices",
          "iam:ListVirtualMFADevices",
          "iam:ResyncMFADevice"
        ]
        Resource = "*"
        Condition = {{
          "BoolIfExists": {{
            "aws:MultiFactorAuthPresent": "false"
          }}
        }}
      }}
    ]
  }})
}}
""",
            "description": f"Enforce MFA for {action.get('target')}"
        }
    
    def _generate_network_segmentation(self, action: Dict) -> Dict[str, Any]:
        """Generate network segmentation rules."""
        return {
            "resource_type": "aws_security_group",
            "action": "create",
            "resource_name": f"segmented_sg_{action.get('target')}",
            "terraform_code": f"""
# Network segmentation
resource "aws_security_group" "segmented_sg_{action.get('target')}" {{
  name_prefix = "segmented-{action.get('target')}"
  vpc_id      = var.vpc_id
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.private_subnet_cidr]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}
""",
            "description": f"Create network segmentation for {action.get('target')}"
        }
    
    def _generate_iac_summary(self, changes: List[Dict]) -> str:
        """Generate summary of IaC changes."""
        total_changes = len(changes)
        resource_types = set(change.get("resource_type") for change in changes)
        
        return f"Generated {total_changes} Terraform changes across {len(resource_types)} resource types"
    
    def _generate_validation_commands(self, changes: List[Dict]) -> List[str]:
        """Generate validation commands for IaC changes."""
        return [
            "terraform plan -var-file=production.tfvars",
            "terraform validate",
            "terraform fmt -check",
            "terraform security scan"
        ]
