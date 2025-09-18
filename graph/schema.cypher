// GNN Attack Path Demo - Neo4j Schema
// This schema models a realistic cyber asset graph for attack path analysis

// Create constraints and indexes for performance
CREATE CONSTRAINT asset_id IF NOT EXISTS FOR (a:Asset) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT software_id IF NOT EXISTS FOR (s:Software) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT vuln_id IF NOT EXISTS FOR (v:Vuln) REQUIRE v.cve IS UNIQUE;
CREATE CONSTRAINT finding_id IF NOT EXISTS FOR (f:Finding) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT control_id IF NOT EXISTS FOR (c:Control) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT tag_id IF NOT EXISTS FOR (t:Tag) REQUIRE t.id IS UNIQUE;

// Create indexes for common query patterns
CREATE INDEX asset_type IF NOT EXISTS FOR (a:Asset) ON (a.type);
CREATE INDEX asset_critical IF NOT EXISTS FOR (a:Asset) ON (a.critical);
CREATE INDEX vuln_exploit IF NOT EXISTS FOR (v:Vuln) ON (v.exploit_available);
CREATE INDEX finding_severity IF NOT EXISTS FOR (f:Finding) ON (f.severity);
CREATE INDEX control_status IF NOT EXISTS FOR (c:Control) ON (c.status);

// Node labels and properties
// Asset nodes represent infrastructure components
// Properties: id, type, critical, name, region, environment
// Types: vm, db, bucket, sg, subnet, user, role, policy, ci_job, vpn, domain

// Software nodes represent installed software
// Properties: id, cpe, version, vendor, name
// CPE format: cpe:2.3:a:vendor:product:version:update:edition:language

// Vulnerability nodes represent CVEs
// Properties: cve, cvss, exploit_available, published_date, description
// CVSS scores: 0.0-10.0, exploit_available: boolean

// Finding nodes represent security findings
// Properties: id, severity, first_seen, last_seen, status, description
// Severity: critical, high, medium, low, info

// Control nodes represent security controls
// Properties: id, type, status, description, created_date
// Types: sg_rule, iam_policy, patch, waf_rule, mfa_requirement

// Tag nodes for asset categorization
// Properties: id, env, owner, system, cost_center, compliance

// Relationship types and properties
// RUNS: (vm)-[:RUNS {version, installed_date}]->(software)
// IN_SUBNET: (vm)-[:IN_SUBNET {ip_address}]->(subnet)
// APPLIES_TO: (sg)-[:APPLIES_TO {priority}]->(vm)
// ALLOWS: (sg)-[:ALLOWS {port, protocol, cidr, direction}]->(ingress)
// CONNECTS_TO: (vm)-[:CONNECTS_TO {protocol, port, encrypted, last_seen}]->(db|vm|bucket)
// ASSUMES: (user)-[:ASSUMES {assumed_at, expires_at}]->(role)
// ALLOWS: (role)-[:ALLOWS {action, resource, condition}]->(policy)
// HAS_VULN: (software)-[:HAS_VULN {detected_at, status}]->(vuln)
// HAS_FINDING: (vuln)-[:HAS_FINDING {detected_at, status}]->(finding)
// PROTECTS_WITH: (asset)-[:PROTECTS_WITH {enabled, last_updated}]->(control)
// TAGGED: (asset)-[:TAGGED {applied_at}]->(tag)

// Crown jewel identification
// Assets with critical=true are considered crown jewels
// These are the primary targets for attack path analysis

// Attack path scoring weights
// Edge weights are calculated based on:
// - Exploitability (CVSS exploitability score)
// - Exposure (public vs private, network segmentation)
// - Privilege gain (IAM permissions, lateral movement potential)
// - Recency (time since last finding, patch status)

// Example queries for attack path analysis:
// 1. Find public-facing VMs with exploitable vulnerabilities
// MATCH (vm:Asset {type: "vm"})<-[:APPLIES_TO]-(sg:Asset {type: "sg"})-[:ALLOWS]->(ingress {cidr: "0.0.0.0/0"})
// MATCH (vm)-[:RUNS]->(software)-[:HAS_VULN]->(vuln {exploit_available: true})
// RETURN vm, vuln, software

// 2. Find attack paths to crown jewels
// MATCH (start:Asset {type: "vm"})<-[:APPLIES_TO]-(sg:Asset {type: "sg"})-[:ALLOWS]->(ingress {cidr: "0.0.0.0/0"})
// MATCH (start)-[:RUNS]->(software)-[:HAS_VULN]->(vuln {exploit_available: true})
// MATCH path = (start)-[:CONNECTS_TO*1..4]->(target:Asset {critical: true})
// RETURN path, vuln, length(path) as path_length
// ORDER BY path_length ASC
// LIMIT 10
