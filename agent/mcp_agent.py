"""
Enhanced AI Agent with MCP Integration

This module provides an enhanced AI agent that uses MCP (Model Context Protocol)
for seamless tool integration and communication with the graph database.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agent.mcp_client import GNNAttackPathMCPClient, MCPClientConfig, MCPToolWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPTool(BaseTool):
    """LangChain tool wrapper for MCP tools"""
    
    name: str
    description: str
    mcp_wrapper: MCPToolWrapper
    tool_method: str
    
    def _run(self, **kwargs) -> str:
        """Synchronous run method"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Asynchronous run method"""
        try:
            method = getattr(self.mcp_wrapper, self.tool_method)
            result = await method(**kwargs)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error in MCP tool {self.name}: {str(e)}")
            return f"Error: {str(e)}"


class MCPEnhancedAgent:
    """Enhanced AI Agent with MCP tool integration"""
    
    def __init__(self, 
                 openai_api_key: str,
                 mcp_config: Optional[MCPClientConfig] = None,
                 model_name: str = "gpt-4"):
        self.openai_api_key = openai_api_key
        self.mcp_config = mcp_config or MCPClientConfig()
        self.model_name = model_name
        
        # Initialize components
        self.mcp_client = None
        self.mcp_wrapper = None
        self.llm = None
        self.tools = []
        self.agent_executor = None
        
    async def initialize(self):
        """Initialize the agent with MCP connection and tools"""
        try:
            # Initialize MCP client
            self.mcp_client = GNNAttackPathMCPClient(self.mcp_config)
            await self.mcp_client.connect()
            self.mcp_wrapper = MCPToolWrapper(self.mcp_client)
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model_name=self.model_name,
                temperature=0.1
            )
            
            # Create MCP tools
            await self._create_mcp_tools()
            
            # Create agent executor
            self._create_agent_executor()
            
            logger.info("MCP Enhanced Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise
    
    async def _create_mcp_tools(self):
        """Create LangChain tools from MCP capabilities"""
        self.tools = [
            MCPTool(
                name="find_attack_paths",
                description="Find and score attack paths between two assets in the cybersecurity graph",
                mcp_wrapper=self.mcp_wrapper,
                tool_method="find_attack_paths"
            ),
            MCPTool(
                name="get_risky_assets",
                description="Get the most risky assets in the cybersecurity graph",
                mcp_wrapper=self.mcp_wrapper,
                tool_method="get_risky_assets"
            ),
            MCPTool(
                name="assess_asset",
                description="Assess the risk level and vulnerabilities of a specific asset",
                mcp_wrapper=self.mcp_wrapper,
                tool_method="assess_asset"
            ),
            MCPTool(
                name="suggest_fixes",
                description="Suggest remediation fixes for identified security issues",
                mcp_wrapper=self.mcp_wrapper,
                tool_method="suggest_fixes"
            ),
            MCPTool(
                name="get_graph_overview",
                description="Get a high-level overview of the cybersecurity graph statistics",
                mcp_wrapper=self.mcp_wrapper,
                tool_method="get_graph_overview"
            )
        ]
    
    def _create_agent_executor(self):
        """Create the agent executor with tools"""
        system_prompt = """You are an expert cybersecurity AI agent specializing in attack path analysis and remediation.

Your capabilities include:
- Analyzing attack paths between assets using Graph Neural Networks
- Identifying high-risk assets and vulnerabilities
- Proposing intelligent remediation strategies
- Providing contextual security insights based on graph relationships

When analyzing security issues:
1. First understand the context by examining the graph structure
2. Identify potential attack paths and their risk scores
3. Assess the impact and blast radius of vulnerabilities
4. Propose specific, actionable remediation steps
5. Consider the trade-offs between security and operational impact

Always provide clear explanations for your recommendations and cite specific evidence from the graph analysis."""

        prompt = f"""{system_prompt}

You have access to the following tools:
{self.tools}

Use these tools to analyze cybersecurity threats and provide actionable recommendations.
Always explain your reasoning and provide specific evidence from the graph analysis."""

        # Create agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
    
    async def analyze_security_query(self, query: str) -> str:
        """Analyze a security-related query using MCP tools"""
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            result = await self.agent_executor.ainvoke({"input": query})
            return result["output"]
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return f"Error analyzing query: {str(e)}"
    
    async def find_attack_paths(self, source: str, target: str) -> Dict[str, Any]:
        """Find attack paths between two assets"""
        if not self.mcp_wrapper:
            raise RuntimeError("Agent not initialized")
        
        return await self.mcp_wrapper.find_attack_paths(source, target)
    
    async def get_risky_assets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most risky assets"""
        if not self.mcp_wrapper:
            raise RuntimeError("Agent not initialized")
        
        return await self.mcp_wrapper.get_risky_assets(limit)
    
    async def assess_asset_risk(self, asset_id: str) -> Dict[str, Any]:
        """Assess risk for a specific asset"""
        if not self.mcp_wrapper:
            raise RuntimeError("Agent not initialized")
        
        return await self.mcp_wrapper.assess_asset(asset_id)
    
    async def suggest_remediation(self, path_id: str, issue_type: str) -> Dict[str, Any]:
        """Suggest remediation for a security issue"""
        if not self.mcp_wrapper:
            raise RuntimeError("Agent not initialized")
        
        return await self.mcp_wrapper.suggest_fixes(path_id, issue_type)
    
    async def get_graph_insights(self) -> Dict[str, Any]:
        """Get high-level graph insights"""
        if not self.mcp_wrapper:
            raise RuntimeError("Agent not initialized")
        
        return await self.mcp_wrapper.get_graph_overview()
    
    async def close(self):
        """Close the agent and disconnect from MCP server"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
        logger.info("MCP Enhanced Agent closed")


# Example usage and testing
async def main():
    """Example usage of MCP Enhanced Agent"""
    import os
    
    # Configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    mcp_config = MCPClientConfig()
    agent = MCPEnhancedAgent(openai_api_key, mcp_config)
    
    try:
        await agent.initialize()
        
        # Example queries
        queries = [
            "What are the most risky assets in our network?",
            "Find attack paths from external servers to our database",
            "Assess the risk level of server-001 and suggest fixes",
            "Give me an overview of our security posture"
        ]
        
        for query in queries:
            print(f"\n{'='*50}")
            print(f"Query: {query}")
            print(f"{'='*50}")
            
            response = await agent.analyze_security_query(query)
            print(f"Response: {response}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
