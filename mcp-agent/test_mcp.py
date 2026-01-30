"""
Microsoft Foundry Agent with MCP (Model Context Protocol) Integration

This module demonstrates how to create an AI agent that connects to the
SP500 MCP server for portfolio analysis, tariff exposure, and company data.

Usage:
    uv run python test_mcp.py
    uv run python test_mcp.py --query "What companies have high tariff exposure?"
    uv run python test_mcp.py --interactive
"""

import argparse
import asyncio
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from agent_framework import HostedMCPTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential


@dataclass
class MCPConfig:
    """Configuration for an MCP server connection."""
    name: str
    url: str
    instructions: str
    default_query: str


# SP500 MCP Server configuration
SP500_CONFIG = MCPConfig(
    name="SP500 MCP",
    url="https://sp500-mcp-server-v2.wonderfulsand-23ca85b9.eastus.azurecontainerapps.io/mcp",
    instructions="""You are a Portfolio Retrieval Agent. Use the connected SP500 MCP tools for all questions about this portfolio's companies, sectors, and tariff exposure. Do **not** make up numbers; always rely on tool outputs.

Available tools (when to use them):

- `query_sp500_portfolio`  
  Use for lists of companies with filters.  
  Examples: "tech companies with high exposure", "consumer names importing from China", "largest retail companies by revenue".  
  Map intent to parameters like `sector`, `industry`, `exposure_level`, `imports_into_us`, `min_revenue`, `sort_by`.

- `get_company_details`  
  Use when the user asks about a **specific company** by name or ticker.  
  Example: "Tell me about ApexTech", "What's the exposure for APEX0?".

- `get_sector_analysis`  
  Use for **sector-level** questions or comparisons.  
  Examples: "Which sectors are most exposed?", "What's happening in technology vs consumer?".

- `get_exposure_summary`  
  Use for **portfolio-wide** exposure and risk.  
  Examples: "What's the overall tariff exposure?", "Give me a portfolio risk summary."

Response style: 
1. Call the most appropriate tool (or 2 tools if needed) without asking the user to restate their question.  
2. Summarize results in clear English: counts, key metrics (revenue, exposure %, imports_from_us), and where risk is concentrated.  
3. If you interpret a vague phrase (e.g., "consumer companies"), briefly state your assumption (e.g., using sector Consumer Discretionary).""",
    default_query="Which S&P 500 companies have the highest tariff exposure? Show me the top 5.",
)


async def create_mcp_agent(
    chat_client: AzureAIAgentClient,
    config: MCPConfig,
    approval_mode: str = "never_require",
):
    """
    Create an agent with an MCP tool attached.
    
    Args:
        chat_client: The Azure AI chat client
        config: Configuration for the MCP server
        approval_mode: Tool approval mode ("never_require", "always_require")
    
    Returns:
        Configured agent with MCP tool
    """
    return chat_client.as_agent(
        name="SP500 Portfolio Agent",
        instructions=config.instructions,
        tools=HostedMCPTool(
            name=config.name,
            url=config.url,
            approval_mode=approval_mode,
        ),
    )


async def run_agent_query(
    query: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """
    Run a query against the SP500 MCP-enabled agent.
    
    Args:
        query: The query to run (uses default if not provided)
        verbose: Whether to print progress messages
    
    Returns:
        The agent's response text
    """
    query = query or SP500_CONFIG.default_query
    
    if verbose:
        print(f"Connecting to {SP500_CONFIG.name}...")
    
    async with AzureCliCredential() as credential:
        async with AzureAIAgentClient(credential=credential) as chat_client:
            if verbose:
                print("Creating agent...")
            
            agent = await create_mcp_agent(chat_client, SP500_CONFIG)
            
            if verbose:
                print(f"Running query: {query[:50]}...")
            
            result = await agent.run(query)
            
            if result.messages:
                return result.messages[0].text
            return "No response received"


async def interactive_mode():
    """Run in interactive mode, allowing multiple queries."""
    print(f"\nInteractive Mode - {SP500_CONFIG.name}")
    print("=" * 50)
    print("Type 'quit' or 'exit' to stop\n")
    
    async with AzureCliCredential() as credential:
        async with AzureAIAgentClient(credential=credential) as chat_client:
            agent = await create_mcp_agent(chat_client, SP500_CONFIG)
            print(f"Connected to {SP500_CONFIG.name}\n")
            
            while True:
                try:
                    query = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break
                
                if not query:
                    continue
                if query.lower() in ("quit", "exit"):
                    print("Goodbye!")
                    break
                
                print("Thinking...\n")
                result = await agent.run(query)
                
                if result.messages:
                    print(f"Agent: {result.messages[0].text}\n")
                else:
                    print("Agent: No response received\n")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run SP500 Portfolio Agent with MCP tool integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                              # Run with default query
  %(prog)s --query "What sectors are most exposed?"     # Custom query
  %(prog)s --interactive                                # Interactive chat mode
  %(prog)s -v --query "Tell me about ApexTech"          # Verbose mode
        """,
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query to run (uses default if not provided)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive chat mode",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show progress messages",
    )
    return parser.parse_args()


async def main():
    """Main entry point."""
    load_dotenv()
    args = parse_args()
    
    if args.interactive:
        await interactive_mode()
    else:
        response = await run_agent_query(
            query=args.query,
            verbose=args.verbose,
        )
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
