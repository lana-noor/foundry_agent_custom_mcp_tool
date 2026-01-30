# SP500 Portfolio Agent with MCP

A Python agent that connects to an SP500 MCP (Model Context Protocol) server to analyze portfolio companies, sectors, and tariff exposure using Azure AI Foundry.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Azure CLI logged in (`az login`)
- MSFT Foundry project with a model deployment

## Dependencies

| Package | Version | Description |
|---------|---------|-------------|
| `agent-framework` | >=1.0.0b260128 | Microsoft Agent Framework for building AI agents |
| `azure-identity` | >=1.25.1 | Azure authentication library |
| `python-dotenv` | >=1.2.1 | Load environment variables from .env files |

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure your `.env` file:
   ```
   AZURE_AI_PROJECT_ENDPOINT=https://<your-hub>.services.ai.azure.com/api/projects/<your-project>
   AZURE_AI_MODEL_DEPLOYMENT_NAME=your-deployment-name
   ```

3. Ensure you're logged into Azure CLI:
   ```bash
   az login
   ```

## Usage

Run with default query:
```bash
uv run python test_mcp.py
```

Custom query:
```bash
uv run python test_mcp.py --query "What sectors are most exposed to tariffs?"
```

Interactive mode:
```bash
uv run python test_mcp.py --interactive
```

Verbose output:
```bash
uv run python test_mcp.py -v --query "Tell me about CloudForge Holdings"
```

## Available MCP Tools

The agent has access to these SP500 portfolio tools:

| Tool | Use Case |
|------|----------|
| `query_sp500_portfolio` | Filter companies by sector, industry, exposure level, revenue |
| `get_company_details` | Get details for a specific company by name or ticker |
| `get_sector_analysis` | Analyze and compare sectors |
| `get_exposure_summary` | Portfolio-wide tariff exposure and risk summary |

## Example Queries

- "Which companies have the highest tariff exposure?"
- "Show me tech companies importing from China"
- "What's the overall portfolio risk summary?"
- "Compare technology vs consumer discretionary sectors"
- "Tell me about NovaRetail Holdings"
