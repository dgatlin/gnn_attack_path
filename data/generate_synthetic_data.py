"""
Synthetic data generator for creating realistic cyber asset graphs.
Generates assets, vulnerabilities, relationships, and attack paths for demo purposes.
"""
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class SyntheticDataGenerator:
    """Generates realistic synthetic cyber asset data for demo purposes."""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.assets = []
        self.software = []
        self.vulnerabilities = []
        self.findings = []
        self.controls = []
        self.tags = []
        self.relationships = []
        
        # Predefined data for realism
        self.software_catalog = [
            {"name": "Apache HTTP Server", "vendor": "apache", "cpe": "cpe:2.3:a:apache:http_server:2.4.41"},
            {"name": "nginx", "vendor": "nginx", "cpe": "cpe:2.3:a:nginx:nginx:1.18.0"},
            {"name": "MySQL", "vendor": "mysql", "cpe": "cpe:2.3:a:mysql:mysql:8.0.21"},
            {"name": "PostgreSQL", "vendor": "postgresql", "cpe": "cpe:2.3:a:postgresql:postgresql:12.4"},
            {"name": "Redis", "vendor": "redis", "cpe": "cpe:2.3:a:redis:redis:6.0.8"},
            {"name": "Docker", "vendor": "docker", "cpe": "cpe:2.3:a:docker:docker:20.10.0"},
            {"name": "Kubernetes", "vendor": "kubernetes", "cpe": "cpe:2.3:a:kubernetes:kubernetes:1.19.0"},
            {"name": "Node.js", "vendor": "nodejs", "cpe": "cpe:2.3:a:nodejs:node.js:14.15.0"},
            {"name": "Python", "vendor": "python", "cpe": "cpe:2.3:a:python:python:3.8.5"},
            {"name": "OpenSSH", "vendor": "openssh", "cpe": "cpe:2.3:a:openssh:openssh:8.2"},
        ]
        
        self.cve_database = [
            {"cve": "CVE-2021-44228", "cvss": 10.0, "exploit_available": True, "description": "Log4j RCE vulnerability"},
            {"cve": "CVE-2021-45046", "cvss": 9.0, "exploit_available": True, "description": "Log4j RCE vulnerability"},
            {"cve": "CVE-2021-41773", "cvss": 7.5, "exploit_available": True, "description": "Apache HTTP Server path traversal"},
            {"cve": "CVE-2021-23017", "cvss": 7.5, "exploit_available": True, "description": "nginx DNS resolver vulnerability"},
            {"cve": "CVE-2021-22205", "cvss": 9.8, "exploit_available": True, "description": "GitLab RCE vulnerability"},
            {"cVE": "CVE-2021-34527", "cvss": 9.8, "exploit_available": True, "description": "Windows Print Spooler RCE"},
            {"cve": "CVE-2021-26855", "cvss": 9.1, "exploit_available": True, "description": "Microsoft Exchange Server RCE"},
            {"cve": "CVE-2021-21972", "cvss": 9.8, "exploit_available": True, "description": "VMware vCenter Server RCE"},
            {"cve": "CVE-2021-20016", "cvss": 9.8, "exploit_available": True, "description": "SonicWall SMA RCE"},
            {"cve": "CVE-2021-1675", "cvss": 8.8, "exploit_available": True, "description": "Windows Print Spooler privilege escalation"},
        ]
        
        self.regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        self.environments = ["production", "staging", "development", "testing"]
        self.severities = ["critical", "high", "medium", "low", "info"]
    
    def generate_assets(self, count: int = 200) -> List[Dict[str, Any]]:
        """Generate synthetic asset nodes."""
        asset_types = ["vm", "db", "bucket", "sg", "subnet", "user", "role", "policy", "ci_job", "vpn", "domain"]
        
        for i in range(count):
            asset_type = random.choice(asset_types)
            critical = random.random() < 0.05  # 5% are crown jewels
            
            asset = {
                "id": f"asset-{i:03d}",
                "type": asset_type,
                "critical": critical,
                "name": f"{asset_type}-{i:03d}",
                "region": random.choice(self.regions),
                "environment": random.choice(self.environments),
                "ip_address": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
                "status": random.choice(["active", "inactive", "maintenance"])
            }
            
            # Special naming for crown jewels
            if critical:
                asset["name"] = f"crown-jewel-{asset_type}-{i:03d}"
            
            self.assets.append(asset)
        
        logger.info("Generated assets", count=len(self.assets))
        return self.assets
    
    def generate_software(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate synthetic software nodes."""
        for i in range(count):
            sw = random.choice(self.software_catalog)
            software = {
                "id": f"software-{i:03d}",
                "cpe": sw["cpe"],
                "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                "vendor": sw["vendor"],
                "name": sw["name"]
            }
            self.software.append(software)
        
        logger.info("Generated software", count=len(self.software))
        return self.software
    
    def generate_vulnerabilities(self, count: int = 30) -> List[Dict[str, Any]]:
        """Generate synthetic vulnerability nodes."""
        for i in range(count):
            vuln = random.choice(self.cve_database)
            vulnerability = {
                "cve": vuln["cve"],
                "cvss": vuln["cvss"],
                "exploit_available": vuln["exploit_available"],
                "published_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "description": vuln["description"]
            }
            self.vulnerabilities.append(vulnerability)
        
        logger.info("Generated vulnerabilities", count=len(self.vulnerabilities))
        return self.vulnerabilities
    
    def generate_findings(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate synthetic security findings."""
        for i in range(count):
            finding = {
                "id": f"finding-{i:03d}",
                "severity": random.choice(self.severities),
                "first_seen": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "last_seen": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
                "status": random.choice(["open", "in_progress", "resolved", "false_positive"]),
                "description": f"Security finding {i:03d} - {random.choice(['vulnerability detected', 'misconfiguration found', 'anomaly detected'])}"
            }
            self.findings.append(finding)
        
        logger.info("Generated findings", count=len(self.findings))
        return self.findings
    
    def generate_controls(self, count: int = 40) -> List[Dict[str, Any]]:
        """Generate synthetic security controls."""
        control_types = ["sg_rule", "iam_policy", "patch", "waf_rule", "mfa_requirement"]
        
        for i in range(count):
            control = {
                "id": f"control-{i:03d}",
                "type": random.choice(control_types),
                "status": random.choice(["active", "inactive", "pending"]),
                "description": f"Security control {i:03d} - {random.choice(['firewall rule', 'IAM policy', 'patch requirement', 'WAF rule', 'MFA requirement'])}",
                "created_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            }
            self.controls.append(control)
        
        logger.info("Generated controls", count=len(self.controls))
        return self.controls
    
    def generate_tags(self, count: int = 20) -> List[Dict[str, Any]]:
        """Generate synthetic tags."""
        owners = ["team-alpha", "team-beta", "team-gamma", "team-delta"]
        systems = ["payment-system", "user-management", "analytics", "monitoring", "logging"]
        cost_centers = ["engineering", "security", "operations", "finance"]
        
        for i in range(count):
            tag = {
                "id": f"tag-{i:03d}",
                "env": random.choice(self.environments),
                "owner": random.choice(owners),
                "system": random.choice(systems),
                "cost_center": random.choice(cost_centers),
                "compliance": random.choice(["pci", "sox", "gdpr", "hipaa", "none"])
            }
            self.tags.append(tag)
        
        logger.info("Generated tags", count=len(self.tags))
        return self.tags
    
    def generate_relationships(self) -> List[Dict[str, Any]]:
        """Generate realistic relationships between nodes."""
        # VMs run software
        vm_assets = [a for a in self.assets if a["type"] == "vm"]
        for vm in vm_assets:
            if random.random() < 0.8:  # 80% of VMs have software
                software = random.choice(self.software)
                self.relationships.append({
                    "type": "RUNS",
                    "source_id": vm["id"],
                    "target_id": software["id"],
                    "properties": {
                        "version": software["version"],
                        "installed_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
                    }
                })
        
        # Software has vulnerabilities
        for software in self.software:
            if random.random() < 0.3:  # 30% of software has vulnerabilities
                vuln = random.choice(self.vulnerabilities)
                self.relationships.append({
                    "type": "HAS_VULN",
                    "source_id": software["id"],
                    "target_id": vuln["cve"],
                    "properties": {
                        "detected_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "status": random.choice(["confirmed", "investigating", "false_positive"])
                    }
                })
        
        # Vulnerabilities have findings
        for vuln in self.vulnerabilities:
            if random.random() < 0.7:  # 70% of vulnerabilities have findings
                finding = random.choice(self.findings)
                self.relationships.append({
                    "type": "HAS_FINDING",
                    "source_id": vuln["cve"],
                    "target_id": finding["id"],
                    "properties": {
                        "detected_at": finding["first_seen"],
                        "status": finding["status"]
                    }
                })
        
        # Create network connectivity (attack paths)
        self._create_attack_paths()
        
        # Create IAM relationships
        self._create_iam_relationships()
        
        # Create security group relationships
        self._create_sg_relationships()
        
        # Create tagging relationships
        self._create_tagging_relationships()
        
        logger.info("Generated relationships", count=len(self.relationships))
        return self.relationships
    
    def _create_attack_paths(self):
        """Create realistic attack paths through the network."""
        # Find public-facing VMs (with public security groups)
        public_vms = []
        for vm in self.assets:
            if vm["type"] == "vm" and random.random() < 0.2:  # 20% are public-facing
                public_vms.append(vm)
        
        # Find crown jewels (critical assets)
        crown_jewels = [a for a in self.assets if a["critical"]]
        
        # Create attack paths from public VMs to crown jewels
        for vm in public_vms:
            for target in crown_jewels:
                if random.random() < 0.3:  # 30% chance of direct path
                    # Direct connection
                    self.relationships.append({
                        "type": "CONNECTS_TO",
                        "source_id": vm["id"],
                        "target_id": target["id"],
                        "properties": {
                            "protocol": random.choice(["tcp", "udp"]),
                            "port": random.randint(1, 65535),
                            "encrypted": random.choice([True, False]),
                            "last_seen": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
                        }
                    })
                elif random.random() < 0.5:  # 50% chance of multi-hop path
                    # Find intermediate hop
                    intermediate = random.choice([a for a in self.assets if a["type"] == "vm" and a != vm])
                    
                    # VM to intermediate
                    self.relationships.append({
                        "type": "CONNECTS_TO",
                        "source_id": vm["id"],
                        "target_id": intermediate["id"],
                        "properties": {
                            "protocol": "tcp",
                            "port": random.randint(1, 65535),
                            "encrypted": random.choice([True, False]),
                            "last_seen": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
                        }
                    })
                    
                    # Intermediate to target
                    self.relationships.append({
                        "type": "CONNECTS_TO",
                        "source_id": intermediate["id"],
                        "target_id": target["id"],
                        "properties": {
                            "protocol": "tcp",
                            "port": random.randint(1, 65535),
                            "encrypted": random.choice([True, False]),
                            "last_seen": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
                        }
                    })
    
    def _create_iam_relationships(self):
        """Create IAM relationships between users, roles, and policies."""
        users = [a for a in self.assets if a["type"] == "user"]
        roles = [a for a in self.assets if a["type"] == "role"]
        policies = [a for a in self.assets if a["type"] == "policy"]
        
        # Users assume roles
        for user in users:
            if random.random() < 0.8:  # 80% of users have roles
                role = random.choice(roles)
                self.relationships.append({
                    "type": "ASSUMES",
                    "source_id": user["id"],
                    "target_id": role["id"],
                    "properties": {
                        "assumed_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "expires_at": (datetime.now() + timedelta(days=random.randint(1, 365))).isoformat()
                    }
                })
        
        # Roles have policies
        for role in roles:
            if random.random() < 0.9:  # 90% of roles have policies
                policy = random.choice(policies)
                self.relationships.append({
                    "type": "ALLOWS",
                    "source_id": role["id"],
                    "target_id": policy["id"],
                    "properties": {
                        "action": random.choice(["read", "write", "execute", "admin"]),
                        "resource": random.choice(["*", "s3://*", "ec2:*", "rds:*"]),
                        "condition": random.choice(["", "time-based", "ip-based"])
                    }
                })
    
    def _create_sg_relationships(self):
        """Create security group relationships."""
        sgs = [a for a in self.assets if a["type"] == "sg"]
        vms = [a for a in self.assets if a["type"] == "vm"]
        
        # Security groups apply to VMs
        for vm in vms:
            if random.random() < 0.9:  # 90% of VMs have security groups
                sg = random.choice(sgs)
                self.relationships.append({
                    "type": "APPLIES_TO",
                    "source_id": sg["id"],
                    "target_id": vm["id"],
                    "properties": {
                        "priority": random.randint(1, 100)
                    }
                })
        
        # Security groups allow ingress
        for sg in sgs:
            if random.random() < 0.7:  # 70% of SGs have ingress rules
                self.relationships.append({
                    "type": "ALLOWS",
                    "source_id": sg["id"],
                    "target_id": "ingress-rule",
                    "properties": {
                        "port": random.randint(1, 65535),
                        "protocol": random.choice(["tcp", "udp", "icmp"]),
                        "cidr": random.choice(["0.0.0.0/0", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]),
                        "direction": "ingress"
                    }
                })
    
    def _create_tagging_relationships(self):
        """Create tagging relationships between assets and tags."""
        for asset in self.assets:
            if random.random() < 0.8:  # 80% of assets have tags
                tag = random.choice(self.tags)
                self.relationships.append({
                    "type": "TAGGED",
                    "source_id": asset["id"],
                    "target_id": tag["id"],
                    "properties": {
                        "applied_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                })
    
    def generate_all(self) -> Dict[str, Any]:
        """Generate all synthetic data."""
        logger.info("Starting synthetic data generation")
        
        # Generate nodes
        self.generate_assets(200)
        self.generate_software(50)
        self.generate_vulnerabilities(30)
        self.generate_findings(100)
        self.generate_controls(40)
        self.generate_tags(20)
        
        # Generate relationships
        self.generate_relationships()
        
        # Compile all data
        data = {
            "assets": self.assets,
            "software": self.software,
            "vulnerabilities": self.vulnerabilities,
            "findings": self.findings,
            "controls": self.controls,
            "tags": self.tags,
            "relationships": self.relationships
        }
        
        logger.info("Synthetic data generation complete", 
                   assets=len(self.assets),
                   software=len(self.software),
                   vulnerabilities=len(self.vulnerabilities),
                   findings=len(self.findings),
                   controls=len(self.controls),
                   tags=len(self.tags),
                   relationships=len(self.relationships))
        
        return data
    
    def save_to_file(self, file_path: str):
        """Save generated data to a JSON file."""
        data = self.generate_all()
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info("Data saved to file", file_path=file_path)


def main():
    """Main function for generating synthetic data."""
    generator = SyntheticDataGenerator()
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent
    data_dir.mkdir(exist_ok=True)
    
    # Generate and save data
    output_file = data_dir / "synthetic_data.json"
    generator.save_to_file(str(output_file))
    
    print(f"Synthetic data generated and saved to {output_file}")
    print(f"Generated {len(generator.assets)} assets, {len(generator.software)} software, {len(generator.vulnerabilities)} vulnerabilities")


if __name__ == "__main__":
    main()
