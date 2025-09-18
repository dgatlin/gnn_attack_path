"""
Data loading utilities for populating the Neo4j graph database.
"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path
from graph.connection import get_connection, close_connection
import structlog

logger = structlog.get_logger(__name__)


class GraphDataLoader:
    """Handles loading data into the Neo4j graph database."""
    
    def __init__(self):
        self.conn = get_connection()
    
    def load_schema(self):
        """Load the database schema and constraints."""
        schema_file = Path(__file__).parent / "schema.cypher"
        with open(schema_file, 'r') as f:
            schema_queries = f.read().split(';')
        
        for query in schema_queries:
            query = query.strip()
            if query:
                try:
                    self.conn.execute_write_query(query)
                    logger.info("Executed schema query", query=query[:100])
                except Exception as e:
                    logger.warning("Schema query failed", query=query[:100], error=str(e))
    
    def load_assets(self, assets: List[Dict[str, Any]]):
        """Load asset nodes into the graph."""
        query = """
        UNWIND $assets AS asset
        CREATE (a:Asset {
            id: asset.id,
            type: asset.type,
            critical: asset.critical,
            name: asset.name,
            region: asset.region,
            environment: asset.environment,
            ip_address: asset.ip_address,
            status: asset.status
        })
        """
        
        count = self.conn.execute_write_query(query, {"assets": assets})
        logger.info("Loaded assets", count=count)
    
    def load_software(self, software: List[Dict[str, Any]]):
        """Load software nodes into the graph."""
        query = """
        UNWIND $software AS sw
        CREATE (s:Software {
            id: sw.id,
            cpe: sw.cpe,
            version: sw.version,
            vendor: sw.vendor,
            name: sw.name
        })
        """
        
        count = self.conn.execute_write_query(query, {"software": software})
        logger.info("Loaded software", count=count)
    
    def load_vulnerabilities(self, vulns: List[Dict[str, Any]]):
        """Load vulnerability nodes into the graph."""
        query = """
        UNWIND $vulns AS vuln
        CREATE (v:Vuln {
            cve: vuln.cve,
            cvss: vuln.cvss,
            exploit_available: vuln.exploit_available,
            published_date: vuln.published_date,
            description: vuln.description
        })
        """
        
        count = self.conn.execute_write_query(query, {"vulns": vulns})
        logger.info("Loaded vulnerabilities", count=count)
    
    def load_findings(self, findings: List[Dict[str, Any]]):
        """Load finding nodes into the graph."""
        query = """
        UNWIND $findings AS finding
        CREATE (f:Finding {
            id: finding.id,
            severity: finding.severity,
            first_seen: finding.first_seen,
            last_seen: finding.last_seen,
            status: finding.status,
            description: finding.description
        })
        """
        
        count = self.conn.execute_write_query(query, {"findings": findings})
        logger.info("Loaded findings", count=count)
    
    def load_controls(self, controls: List[Dict[str, Any]]):
        """Load control nodes into the graph."""
        query = """
        UNWIND $controls AS control
        CREATE (c:Control {
            id: control.id,
            type: control.type,
            status: control.status,
            description: control.description,
            created_date: control.created_date
        })
        """
        
        count = self.conn.execute_write_query(query, {"controls": controls})
        logger.info("Loaded controls", count=count)
    
    def load_tags(self, tags: List[Dict[str, Any]]):
        """Load tag nodes into the graph."""
        query = """
        UNWIND $tags AS tag
        CREATE (t:Tag {
            id: tag.id,
            env: tag.env,
            owner: tag.owner,
            system: tag.system,
            cost_center: tag.cost_center,
            compliance: tag.compliance
        })
        """
        
        count = self.conn.execute_write_query(query, {"tags": tags})
        logger.info("Loaded tags", count=count)
    
    def create_relationships(self, relationships: List[Dict[str, Any]]):
        """Create relationships between nodes."""
        for rel in relationships:
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:{rel['type']} $properties]->(b)
            """
            
            try:
                self.conn.execute_write_query(query, {
                    "source_id": rel["source_id"],
                    "target_id": rel["target_id"],
                    "properties": rel.get("properties", {})
                })
            except Exception as e:
                logger.warning("Failed to create relationship", 
                             type=rel["type"], 
                             source=rel["source_id"], 
                             target=rel["target_id"],
                             error=str(e))
    
    def load_from_file(self, file_path: str):
        """Load data from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Load nodes
        if "assets" in data:
            self.load_assets(data["assets"])
        if "software" in data:
            self.load_software(data["software"])
        if "vulnerabilities" in data:
            self.load_vulnerabilities(data["vulnerabilities"])
        if "findings" in data:
            self.load_findings(data["findings"])
        if "controls" in data:
            self.load_controls(data["controls"])
        if "tags" in data:
            self.load_tags(data["tags"])
        
        # Load relationships
        if "relationships" in data:
            self.create_relationships(data["relationships"])
    
    def get_attack_paths(self, target_id: str, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Query attack paths to a specific target."""
        query = """
        MATCH (start:Asset {type: "vm"})<-[:APPLIES_TO]-(sg:Asset {type: "sg"})-[:ALLOWS]->(ingress {cidr: "0.0.0.0/0"})
        MATCH (start)-[:RUNS]->(software)-[:HAS_VULN]->(vuln {exploit_available: true})
        MATCH path = (start)-[:CONNECTS_TO*1..$max_hops]->(target:Asset {id: $target_id, critical: true})
        RETURN path, vuln, length(path) as path_length
        ORDER BY path_length ASC
        LIMIT 10
        """
        
        return self.conn.execute_query(query, {
            "target_id": target_id,
            "max_hops": max_hops
        })


def main():
    """Main function for loading data."""
    loader = GraphDataLoader()
    
    try:
        # Load schema
        loader.load_schema()
        
        # Load synthetic data if available
        data_file = Path(__file__).parent.parent / "data" / "synthetic_data.json"
        if data_file.exists():
            loader.load_from_file(str(data_file))
            logger.info("Loaded synthetic data")
        else:
            logger.warning("No synthetic data file found")
        
        # Display database info
        info = loader.conn.get_database_info()
        logger.info("Database loaded", info=info)
        
    except Exception as e:
        logger.error("Failed to load data", error=str(e))
        raise
    finally:
        close_connection()


if __name__ == "__main__":
    main()
