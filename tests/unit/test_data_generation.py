"""
Unit tests for data generation components.

Tests synthetic data generation in isolation with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

from data.generate_synthetic_data import SyntheticDataGenerator


class TestSyntheticDataGenerator:
    """Unit tests for SyntheticDataGenerator."""
    
    def setup_method(self):
        """Set up test data generator."""
        self.generator = SyntheticDataGenerator()
    
    def test_generator_initialization(self):
        """Test data generator initializes correctly."""
        assert self.generator.assets == []
        assert self.generator.software == []
        assert self.generator.vulnerabilities == []
        assert self.generator.findings == []
        assert self.generator.controls == []
        assert self.generator.tags == []
        assert self.generator.relationships == []
    
    def test_generate_assets(self):
        """Test asset generation."""
        assets = self.generator.generate_assets(count=10)
        
        assert isinstance(assets, list)
        assert len(assets) == 10
        
        # Check asset structure
        for asset in assets:
            assert "id" in asset
            assert "type" in asset
            assert "critical" in asset
            assert "name" in asset
            assert "region" in asset
            assert "environment" in asset
            assert "ip_address" in asset
            assert "status" in asset
    
    def test_generate_software(self):
        """Test software generation."""
        software = self.generator.generate_software(count=5)
        
        assert isinstance(software, list)
        assert len(software) == 5
        
        # Check software structure
        for sw in software:
            assert "id" in sw
            assert "cpe" in sw
            assert "version" in sw
            assert "vendor" in sw
            assert "name" in sw
    
    def test_generate_vulnerabilities(self):
        """Test vulnerability generation."""
        vulnerabilities = self.generator.generate_vulnerabilities(count=5)
        
        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) == 5
        
        # Check vulnerability structure
        for vuln in vulnerabilities:
            assert "cve" in vuln
            assert "cvss" in vuln
            assert "exploit_available" in vuln
            assert "published_date" in vuln
            assert "description" in vuln
    
    def test_generate_findings(self):
        """Test findings generation."""
        findings = self.generator.generate_findings(count=5)
        
        assert isinstance(findings, list)
        assert len(findings) == 5
        
        # Check finding structure
        for finding in findings:
            assert "id" in finding
            assert "severity" in finding
            assert "first_seen" in finding
            assert "last_seen" in finding
            assert "status" in finding
            assert "description" in finding
    
    def test_generate_controls(self):
        """Test controls generation."""
        controls = self.generator.generate_controls(count=5)
        
        assert isinstance(controls, list)
        assert len(controls) == 5
        
        # Check control structure
        for control in controls:
            assert "id" in control
            assert "type" in control
            assert "status" in control
            assert "description" in control
            assert "created_date" in control
    
    def test_generate_tags(self):
        """Test tags generation."""
        tags = self.generator.generate_tags(count=5)
        
        assert isinstance(tags, list)
        assert len(tags) == 5
        
        # Check tag structure
        for tag in tags:
            assert "id" in tag
            assert "env" in tag
            assert "owner" in tag
            assert "system" in tag
            assert "cost_center" in tag
            assert "compliance" in tag
    
    def test_generate_relationships(self):
        """Test relationships generation."""
        # First generate all required data
        self.generator.generate_assets(count=5)
        self.generator.generate_software(count=3)
        self.generator.generate_vulnerabilities(count=5)
        self.generator.generate_findings(count=5)
        self.generator.generate_controls(count=5)
        self.generator.generate_tags(count=5)
        
        relationships = self.generator.generate_relationships()
        
        assert isinstance(relationships, list)
        assert len(relationships) > 0
        
        # Check relationship structure
        for rel in relationships:
            assert "source_id" in rel
            assert "target_id" in rel
            assert "type" in rel
            assert "properties" in rel
    
    def test_generate_all(self):
        """Test complete data generation."""
        data = self.generator.generate_all()
        
        assert isinstance(data, dict)
        assert "assets" in data
        assert "software" in data
        assert "vulnerabilities" in data
        assert "findings" in data
        assert "controls" in data
        assert "tags" in data
        assert "relationships" in data
        
        # Check data consistency
        assert len(data["assets"]) > 0
        assert len(data["software"]) > 0
        assert len(data["vulnerabilities"]) > 0
        assert len(data["findings"]) > 0
        assert len(data["controls"]) > 0
        assert len(data["tags"]) > 0
        assert len(data["relationships"]) > 0
    
    def test_custom_count_parameters(self):
        """Test generator with custom count parameters."""
        # Test with different counts
        assets = self.generator.generate_assets(count=20)
        assert len(assets) == 20
        
        software = self.generator.generate_software(count=10)
        assert len(software) == 10
        
        vulnerabilities = self.generator.generate_vulnerabilities(count=15)
        assert len(vulnerabilities) == 15
    
    def test_asset_type_distribution(self):
        """Test that asset types are distributed correctly."""
        assets = self.generator.generate_assets(count=50)
        
        # Count asset types
        type_counts = {}
        for asset in assets:
            asset_type = asset["type"]
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        
        # Should have multiple types
        assert len(type_counts) > 1
        
        # Should include expected types
        expected_types = ["vm", "db", "bucket", "sg", "subnet", "user", "role", "policy", "ci_job", "vpn", "domain"]
        for asset_type in type_counts:
            assert asset_type in expected_types
    
    def test_critical_asset_identification(self):
        """Test critical asset identification."""
        assets = self.generator.generate_assets(count=100)
        
        critical_assets = [asset for asset in assets if asset["critical"]]
        non_critical_assets = [asset for asset in assets if not asset["critical"]]
        
        # Should have both critical and non-critical assets
        assert len(critical_assets) > 0
        assert len(non_critical_assets) > 0
        
        # Critical assets should have special naming
        for critical_asset in critical_assets:
            assert "crown-jewel" in critical_asset["name"]
    
    def test_vulnerability_cve_format(self):
        """Test CVE format in vulnerabilities."""
        vulnerabilities = self.generator.generate_vulnerabilities(count=10)
        
        for vuln in vulnerabilities:
            cve = vuln["cve"]
            # Should be in CVE format (CVE-YYYY-NNNN)
            assert cve.startswith("CVE-")
            assert len(cve.split("-")) == 3
            year = cve.split("-")[1]
            assert year.isdigit()
            assert 2000 <= int(year) <= 2024
    
    def test_cvss_score_range(self):
        """Test CVSS score range."""
        vulnerabilities = self.generator.generate_vulnerabilities(count=10)
        
        for vuln in vulnerabilities:
            cvss = vuln["cvss"]
            assert isinstance(cvss, float)
            assert 0.0 <= cvss <= 10.0
    
    def test_relationship_types(self):
        """Test relationship types."""
        # Generate all required data first - use generate_all to ensure all types are created
        data = self.generator.generate_all()
        
        relationships = data["relationships"]
        
        relationship_types = set(rel["type"] for rel in relationships)
        
        # Should have multiple relationship types
        assert len(relationship_types) > 1
        
        # Should include expected relationship types
        expected_types = ["RUNS", "IN_SUBNET", "APPLIES_TO", "ALLOWS", "CONNECTS_TO", "ASSUMES", "HAS_VULN", "HAS_FINDING", "PROTECTS_WITH", "TAGGED"]
        assert any(rt in expected_types for rt in relationship_types)
    
    def test_data_consistency(self):
        """Test data consistency across multiple generations."""
        # Generate data twice with different seeds
        gen1 = SyntheticDataGenerator(seed=42)
        gen2 = SyntheticDataGenerator(seed=123)
        
        data1 = gen1.generate_all()
        data2 = gen2.generate_all()
        
        # Should generate different data with different seeds (check IP addresses which are random)
        assert data1["assets"][0]["ip_address"] != data2["assets"][0]["ip_address"]
        
        # But structure should be consistent
        assert len(data1["assets"]) == len(data2["assets"])
        assert len(data1["software"]) == len(data2["software"])
        assert len(data1["vulnerabilities"]) == len(data2["vulnerabilities"])
    
    def test_empty_data_generation(self):
        """Test behavior with zero count."""
        assets = self.generator.generate_assets(count=0)
        assert assets == []
        
        software = self.generator.generate_software(count=0)
        assert software == []
        
        vulnerabilities = self.generator.generate_vulnerabilities(count=0)
        assert vulnerabilities == []
    
    def test_large_dataset_generation(self):
        """Test generation of larger datasets."""
        # Test with larger counts
        assets = self.generator.generate_assets(count=500)
        assert len(assets) == 500
        
        software = self.generator.generate_software(count=100)
        assert len(software) == 100
        
        vulnerabilities = self.generator.generate_vulnerabilities(count=50)
        assert len(vulnerabilities) == 50
    
    def test_software_catalog_usage(self):
        """Test that software catalog is used correctly."""
        software = self.generator.generate_software(count=20)
        
        # All software should come from the catalog
        catalog_names = {sw["name"] for sw in self.generator.software_catalog}
        generated_names = {sw["name"] for sw in software}
        
        assert generated_names.issubset(catalog_names)
    
    def test_cve_database_usage(self):
        """Test that CVE database is used correctly."""
        vulnerabilities = self.generator.generate_vulnerabilities(count=20)
        
        # All CVEs should come from the database
        database_cves = {vuln["cve"] for vuln in self.generator.cve_database}
        generated_cves = {vuln["cve"] for vuln in vulnerabilities}
        
        assert generated_cves.issubset(database_cves)
    
    def test_ip_address_format(self):
        """Test IP address format."""
        assets = self.generator.generate_assets(count=10)
        
        for asset in assets:
            ip = asset["ip_address"]
            # Should be in 10.x.x.x format
            assert ip.startswith("10.")
            parts = ip.split(".")
            assert len(parts) == 4
            for part in parts:
                assert part.isdigit()
                assert 0 <= int(part) <= 255
    
    def test_environment_distribution(self):
        """Test environment distribution."""
        assets = self.generator.generate_assets(count=100)
        
        environments = [asset["environment"] for asset in assets]
        unique_environments = set(environments)
        
        # Should have multiple environments
        assert len(unique_environments) > 1
        
        # Should include expected environments
        expected_envs = ["production", "staging", "development", "testing"]
        assert unique_environments.issubset(set(expected_envs))
    
    def test_region_distribution(self):
        """Test region distribution."""
        assets = self.generator.generate_assets(count=100)
        
        regions = [asset["region"] for asset in assets]
        unique_regions = set(regions)
        
        # Should have multiple regions
        assert len(unique_regions) > 1
        
        # Should include expected regions
        expected_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        assert unique_regions.issubset(set(expected_regions))