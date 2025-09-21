"""
Mock data for testing the frontend without Neo4j dependency.
"""
import random
from typing import Dict, List, Any

# Mock crown jewels data
MOCK_CROWN_JEWELS = [
    {"id": "crown-jewel-db-001", "name": "Production Database", "type": "database", "critical": True},
    {"id": "crown-jewel-app-001", "name": "Customer Portal", "type": "application", "critical": True},
    {"id": "crown-jewel-api-001", "name": "Payment API", "type": "api", "critical": True},
    {"id": "crown-jewel-vm-001", "name": "Admin Server", "type": "vm", "critical": True},
    {"id": "crown-jewel-storage-001", "name": "File Storage", "type": "storage", "critical": True},
]

# Mock attack paths data
MOCK_ATTACK_PATHS = {
    "crown-jewel-db-001": [
        {
            "path": ["external", "dmz-web", "internal-app", "crown-jewel-db-001"],
            "score": 0.92,
            "risk_score": 0.92,
            "length": 4,
            "algorithm": "hybrid",
            "vulnerabilities": ["CVE-2023-1234", "CVE-2023-5678"],
            "exploit_available": True,
            "explanation": "High-risk path through DMZ web server with known vulnerabilities. The path exploits a SQL injection vulnerability in the web application to gain access to the internal network and ultimately the database."
        },
        {
            "path": ["compromised-user", "admin-workstation", "crown-jewel-db-001"],
            "score": 0.87,
            "risk_score": 0.87,
            "length": 3,
            "algorithm": "hybrid",
            "vulnerabilities": ["CVE-2023-9999"],
            "exploit_available": True,
            "explanation": "Insider threat path through compromised admin credentials. This path represents a significant risk as it bypasses most external security controls."
        },
        {
            "path": ["iot-device", "internal-network", "crown-jewel-db-001"],
            "score": 0.78,
            "risk_score": 0.78,
            "length": 3,
            "algorithm": "hybrid",
            "vulnerabilities": ["CVE-2023-1111"],
            "exploit_available": False,
            "explanation": "IoT device compromise leading to lateral movement. The path exploits weak security on IoT devices to gain network access."
        }
    ],
    "crown-jewel-app-001": [
        {
            "path": ["external", "load-balancer", "crown-jewel-app-001"],
            "score": 0.85,
            "risk_score": 0.85,
            "length": 3,
            "algorithm": "hybrid",
            "vulnerabilities": ["CVE-2023-2222"],
            "exploit_available": True,
            "explanation": "Direct external access to application through load balancer. The path exploits a vulnerability in the application's authentication mechanism."
        },
        {
            "path": ["external", "cdn", "waf", "crown-jewel-app-001"],
            "score": 0.65,
            "risk_score": 0.65,
            "length": 4,
            "algorithm": "hybrid",
            "vulnerabilities": ["CVE-2023-3333"],
            "exploit_available": False,
            "explanation": "Path through CDN and WAF with some protection. The path has multiple security layers but still presents a moderate risk."
        }
    ],
    "crown-jewel-api-001": [
        {
            "path": ["external", "api-gateway", "crown-jewel-api-001"],
            "score": 0.88,
            "risk_score": 0.88,
            "length": 3,
            "algorithm": "hybrid",
            "vulnerabilities": ["CVE-2023-4444"],
            "exploit_available": True,
            "explanation": "API endpoint with insufficient authentication. The path exploits weak API key validation to gain access to sensitive payment data."
        }
    ]
}

# Mock algorithms
MOCK_ALGORITHMS = ["hybrid", "dijkstra", "pagerank", "motif", "gnn"]

# Mock metrics data
MOCK_METRICS = {
    "response_time": [
        {"time": "00:00", "ms": 120},
        {"time": "04:00", "ms": 95},
        {"time": "08:00", "ms": 180},
        {"time": "12:00", "ms": 150},
        {"time": "16:00", "ms": 200},
        {"time": "20:00", "ms": 110},
    ],
    "risk_distribution": [
        {"level": "High", "count": 12, "color": "#ef4444"},
        {"level": "Medium", "count": 28, "color": "#f59e0b"},
        {"level": "Low", "count": 45, "color": "#10b981"},
    ],
    "algorithm_performance": [
        {"algorithm": "GNN", "accuracy": 94, "speed": 120},
        {"algorithm": "Hybrid", "accuracy": 89, "speed": 85},
        {"algorithm": "Dijkstra", "accuracy": 76, "speed": 45},
        {"algorithm": "PageRank", "accuracy": 82, "speed": 60},
    ],
    "attack_paths": [
        {"path": "External → DMZ → DB", "count": 15, "risk": 0.9},
        {"path": "User → Admin → DB", "count": 8, "risk": 0.7},
        {"path": "IoT → Network → DB", "count": 12, "risk": 0.8},
    ]
}

def get_mock_attack_paths(target: str, algorithm: str = "hybrid", max_hops: int = 4, k: int = 5) -> List[Dict[str, Any]]:
    """Get mock attack paths for a target."""
    paths = MOCK_ATTACK_PATHS.get(target, [])
    
    # Filter by max_hops
    filtered_paths = [p for p in paths if p["length"] <= max_hops]
    
    # Sort by score (highest first) and take top k
    sorted_paths = sorted(filtered_paths, key=lambda x: x["score"], reverse=True)
    
    return sorted_paths[:k]

def get_mock_crown_jewels() -> List[Dict[str, Any]]:
    """Get mock crown jewels."""
    return MOCK_CROWN_JEWELS

def get_mock_algorithms() -> List[str]:
    """Get mock available algorithms."""
    return MOCK_ALGORITHMS

def get_mock_metrics() -> Dict[str, Any]:
    """Get mock metrics data."""
    return MOCK_METRICS

def get_mock_risk_explanation(path: List[str]) -> str:
    """Get mock risk explanation for a path."""
    explanations = [
        "This path represents a high-risk attack vector through multiple network segments.",
        "The attack path exploits known vulnerabilities in the infrastructure components.",
        "Lateral movement through this path could lead to data exfiltration.",
        "This path bypasses several security controls and monitoring systems.",
        "The attack vector has been observed in recent threat intelligence reports."
    ]
    return random.choice(explanations)
