from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test API is working"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/crown-jewels")
async def crown_jewels():
    return {
        "crown_jewels": [
            {"id": "crown-jewel-db-001", "name": "Production Database", "type": "database"},
            {"id": "crown-jewel-app-001", "name": "Customer Portal", "type": "application"},
        ],
        "count": 2
    }

@app.post("/api/v1/paths")
async def attack_paths(request: dict):
    return {
        "target": request.get("target", "crown-jewel-db-001"),
        "paths": [
            {
                "path": ["external", "dmz", "internal", "crown-jewel-db-001"],
                "score": 0.92,
                "risk_score": 0.92,
                "length": 4,
                "algorithm": "hybrid",
                "vulnerabilities": ["CVE-2023-1234"],
                "exploit_available": True,
                "explanation": "High-risk path through DMZ with known vulnerabilities."
            }
        ],
        "latency_ms": 150.0,
        "algorithm": "hybrid"
    }

@app.post("/api/v1/query")
async def process_query(request: dict):
    """Process natural language queries using AI."""
    query = request.get("query", "").lower()
    
    # AI responses based on query content
    if "riskiest" in query and ("path" in query or "database" in query):
        return {
            "results": {
                "text": "I found 3 high-risk attack paths to your crown jewel database:",
                "details": [
                    "Path 1: External → DMZ → Internal → Database (Risk: 94%)",
                    "Path 2: Compromised User → Admin → Root → Database (Risk: 87%)",
                    "Path 3: IoT Device → Network → Database (Risk: 82%)"
                ],
                "recommendations": [
                    "Apply security patches to DMZ servers",
                    "Enable multi-factor authentication for admin accounts",
                    "Isolate IoT devices from critical networks"
                ]
            },
            "status": "success",
            "latency_ms": 1200.0
        }
    elif ("fix" in query or "remediate" in query or "reduce" in query) and ("risk" in query or "80%" in query):
        return {
            "results": {
                "text": "Here are the top remediation actions to reduce risk:",
                "details": [
                    "1. Remove public ingress from security groups (Risk reduction: 45%)",
                    "2. Apply critical security patches (Risk reduction: 30%)",
                    "3. Enable MFA for all admin accounts (Risk reduction: 25%)"
                ],
                "recommendations": [
                    "Start with removing public access - highest impact, lowest effort",
                    "Schedule patching during maintenance window",
                    "Implement MFA gradually to avoid user disruption"
                ]
            },
            "status": "success",
            "latency_ms": 1100.0
        }
    elif "vulnerable" in query or "vulnerability" in query or "ransomware" in query:
        return {
            "results": {
                "text": "I've identified the most vulnerable assets in your network:",
                "details": [
                    "Database servers (3 critical vulnerabilities)",
                    "Web application servers (2 high-risk vulnerabilities)",
                    "Administrative workstations (1 zero-day vulnerability)"
                ],
                "recommendations": [
                    "Prioritize database server patching immediately",
                    "Implement web application firewall rules",
                    "Isolate admin workstations from production networks"
                ]
            },
            "status": "success",
            "latency_ms": 1300.0
        }
    elif "paths" in query and "external" in query:
        return {
            "results": {
                "text": "I found 4 attack paths from external servers to your database:",
                "details": [
                    "External → Load Balancer → Web App → Database (Risk: 88%)",
                    "External → CDN → WAF → Database (Risk: 65%)",
                    "External → VPN → Internal → Database (Risk: 72%)",
                    "External → API Gateway → Database (Risk: 91%)"
                ],
                "recommendations": [
                    "Implement network segmentation between external and internal zones",
                    "Add additional authentication layers for external access",
                    "Monitor and log all external-to-internal communications"
                ]
            },
            "status": "success",
            "latency_ms": 1400.0
        }
    elif "improve" in query or "posture" in query:
        return {
            "results": {
                "text": "Here's how to improve your overall security posture:",
                "details": [
                    "1. Implement Zero Trust Architecture (Reduces risk by 60%)",
                    "2. Deploy Endpoint Detection and Response (EDR) (Reduces risk by 40%)",
                    "3. Establish Security Awareness Training (Reduces risk by 25%)",
                    "4. Implement Continuous Vulnerability Management (Reduces risk by 35%)"
                ],
                "recommendations": [
                    "Start with Zero Trust - it provides the highest security improvement",
                    "Focus on user training to reduce social engineering risks",
                    "Automate vulnerability scanning and patching processes",
                    "Implement 24/7 security monitoring and incident response"
                ]
            },
            "status": "success",
            "latency_ms": 1600.0
        }
    else:
        return {
            "results": {
                "text": "I can help you analyze attack paths, identify vulnerabilities, and recommend remediation actions. Try asking about:",
                "details": [
                    "• Risk assessment of specific assets",
                    "• Attack path analysis",
                    "• Security remediation recommendations",
                    "• Vulnerability prioritization"
                ],
                "recommendations": [
                    "Be specific about what you want to analyze",
                    "Mention specific assets or attack scenarios",
                    "Ask for actionable recommendations"
                ]
            },
            "status": "success",
            "latency_ms": 800.0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
