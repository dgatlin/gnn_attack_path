"""
Neo4j connection management and database operations.
"""
import os
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase
import structlog

logger = structlog.get_logger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connections and operations."""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        
    def connect(self):
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j", uri=self.uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e))
            raise
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error("Query execution failed", query=query, error=str(e))
            raise
    
    def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> int:
        """Execute a write query and return the number of affected records."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                summary = result.consume()
                return summary.counters.nodes_created + summary.counters.relationships_created
        except Exception as e:
            logger.error("Write query execution failed", query=query, error=str(e))
            raise
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        logger.warning("Clearing entire Neo4j database")
        self.execute_write_query("MATCH (n) DETACH DELETE n")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic information about the database."""
        node_counts = self.execute_query("""
            MATCH (n) 
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
        """)
        
        relationship_counts = self.execute_query("""
            MATCH ()-[r]->() 
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        
        return {
            "nodes": node_counts,
            "relationships": relationship_counts
        }


# Global connection instance
_connection: Optional[Neo4jConnection] = None


def get_connection() -> Neo4jConnection:
    """Get the global Neo4j connection instance."""
    global _connection
    if _connection is None:
        _connection = Neo4jConnection()
        _connection.connect()
    return _connection


def close_connection():
    """Close the global Neo4j connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
