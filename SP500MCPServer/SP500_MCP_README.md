# SP500 MCP Server V2 - Complete Guide

## 📋 Table of Contents
- [What is This MCP Server?](#what-is-this-mcp-server)
- [Available Tools](#available-tools)
- [Example Outputs](#example-outputs)
- [Agent-to-MCP Communication](#agent-to-mcp-communication)
- [Deployment to Azure Container Apps](#deployment-to-azure-container-apps)

---

## 🎯 What is This MCP Server?

The **SP500 MCP Server V2** is a Model Context Protocol (MCP) server that provides AI agents with access to SP500 portfolio data and tariff exposure analysis. It acts as a **data access layer** that agents can query using natural language.

### Key Features:
- ✅ **Azure AI Foundry Compatible** - Uses simplified JSON schemas (no `anyOf`/`oneOf`/`allOf`)
- ✅ **4 Specialized Tools** - Query portfolio, get company details, analyze sectors, get exposure summaries
- ✅ **60 Companies** - Real-style SP500 portfolio data with tariff exposure metrics
- ✅ **FastMCP Framework** - Built on FastMCP with streamable-http transport
- ✅ **Production Ready** - Deployed to Azure Container Apps with health checks

### What Data Does It Provide?

The server reads from `sp500_style_portfolio_60.csv` containing:
- **Company Information**: Ticker, name, sector, industry
- **Financial Metrics**: Revenue, COGS, gross margin, investment amount
- **Tariff Exposure**: Affected COGS percentage, exposure level (high/medium/low/none)
- **Import Status**: Whether company imports from China
- **Confidence Scores**: Data reliability metrics

### How It Works:

```
User asks question in natural language
         ↓
AI Agent (GPT-5-mini) interprets the question
         ↓
Agent calls MCP Server tool with parameters
         ↓
MCP Server queries CSV data
         ↓
Returns structured JSON response
         ↓
Agent formats response for user
```

---

## 🔧 Available Tools

The MCP server provides **4 tools** that agents can call:

### 1️⃣ **query_sp500_portfolio**
**Purpose**: Query the portfolio with flexible filters

**When to Use**:
- "Show me technology companies"
- "Which companies have high exposure?"
- "Find retail companies importing from China"
- "Show me companies with revenue over $100B"

**Parameters**:
- `sector` (string): Filter by sector (e.g., "Information Technology")
- `industry` (string): Filter by industry (e.g., "Software")
- `exposure_level` (string): Filter by exposure: "high", "medium", "low", "none"
- `imports_filter` (string): "yes" for importers, "no" for non-importers
- `min_revenue` (float): Minimum revenue in USD
- `max_revenue` (float): Maximum revenue in USD
- `min_affected_cogs_pct` (float): Minimum affected COGS percentage (0.0-1.0)
- `company_name` (string): Search by company name (partial match)
- `ticker` (string): Filter by ticker symbol
- `limit` (int): Max results to return (default: 20)
- `sort_by` (string): Sort field ("revenue_usd", "affected_cogs_pct", etc.)
- `sort_desc` (bool): Sort descending (default: true)

**Returns**:
```json
{
  "request_id": "rq_abc123",
  "status": "success",
  "total_matches": 13,
  "returned_count": 5,
  "companies": [
    {
      "ticker": "APEX0",
      "company_name": "ApexTech Solutions",
      "sector": "Information Technology",
      "industry": "Software",
      "investment_usd": 1000000,
      "revenue_usd": 89234567890,
      "cogs_usd": 26770370367,
      "gross_margin_pct": 0.7,
      "imports_into_us": true,
      "affected_cogs_pct": 0.45,
      "exposure_level": "high",
      "confidence": 0.85
    }
    // ... more companies
  ],
  "processing_time_ms": 12.34
}
```

---

### 2️⃣ **get_company_details**
**Purpose**: Get detailed information about a specific company

**When to Use**:
- "Tell me about ApexTech"
- "What's the exposure for APEX0?"
- "Show me Nike's tariff risk"

**Parameters**:
- `ticker` (string): Company ticker symbol
- `company_name` (string): Company name (partial match)
- *Note: Provide at least one parameter*

**Returns**:
```json
{
  "request_id": "rq_def456",
  "status": "success",
  "company": {
    "ticker": "APEX0",
    "company_name": "ApexTech Solutions",
    "sector": "Information Technology",
    "industry": "Software",
    "investment_usd": 1000000,
    "revenue_usd": 89234567890,
    "cogs_usd": 26770370367,
    "gross_margin_pct": 0.7,
    "imports_into_us": true,
    "affected_cogs_pct": 0.45,
    "exposure_level": "high",
    "confidence": 0.85
  },
  "calculated_metrics": {
    "affected_cogs_usd": 12046666665.15,
    "potential_tariff_impact_usd": 3011666666.29,
    "revenue_to_cogs_ratio": 3.33,
    "exposure_risk_score": 0.45
  },
  "processing_time_ms": 8.21
}
```

---

### 3️⃣ **get_sector_analysis**
**Purpose**: Analyze portfolio by sector with aggregated metrics

**When to Use**:
- "Which sectors are most exposed?"
- "Show me sector breakdown"
- "Analyze the technology sector"
- "What's the exposure by industry?"

**Parameters**:
- `sector` (string): Specific sector to analyze (empty = all sectors)

**Returns**:
```json
{
  "request_id": "rq_ghi789",
  "status": "success",
  "sector_count": 11,
  "sectors": [
    {
      "sector": "Information Technology",
      "company_count": 13,
      "total_investment_usd": 13000000,
      "total_revenue_usd": 789456123456,
      "total_cogs_usd": 234567890123,
      "total_affected_cogs_usd": 81098765432,
      "average_exposure_pct": 0.3456,
      "importers_count": 13,
      "top_exposed_companies": [
        // Top 5 most exposed companies in sector
      ]
    }
    // ... more sectors
  ],
  "processing_time_ms": 15.67
}
```

---

### 4️⃣ **get_exposure_summary**
**Purpose**: Get comprehensive portfolio-wide exposure summary

**When to Use**:
- "What's the overall exposure?"
- "Give me a portfolio summary"
- "How exposed is the portfolio to tariffs?"
- "Show me the big picture"

**Parameters**: None

**Returns**:
```json
{
  "request_id": "rq_jkl012",
  "status": "success",
  "portfolio_overview": {
    "total_companies": 60,
    "total_investment_usd": 60000000,
    "total_revenue_usd": 3456789012345,
    "total_cogs_usd": 1234567890123,
    "total_affected_cogs_usd": 456789012345,
    "overall_exposure_pct": 0.37,
    "companies_importing_from_china": 54
  },
  "exposure_level_breakdown": {
    "high": 28,
    "medium": 20,
    "low": 6,
    "none": 6
  },
  "top_exposed_companies": [
    // Top 10 most exposed companies
  ],
  "sector_exposure_ranking": [
    {
      "sector": "Consumer Discretionary",
      "exposure_pct": 0.52
    }
    // ... more sectors ranked by exposure
  ],
  "processing_time_ms": 18.92
}
```

---

## 🤖 Agent-to-MCP Communication

### How Agents Call the MCP Server

When an AI agent needs data, it sends an HTTP POST request to the MCP server endpoint.

**MCP Server URL**: `<container-app-name>.<container-app-environment>.<region>.azurecontainerapps.io/mcp`

### Example 1: User Asks "Show me technology companies with high exposure"

**Step 1: User Question**
```
User: "Show me technology companies with high exposure"
```

**Step 2: Agent Interprets & Calls MCP Tool**

The agent (GPT-5-mini) automatically:
- Understands the user wants technology sector companies
- Recognizes "high exposure" means `exposure_level="high"`
- Calls the `query_sp500_portfolio` tool

**MCP Request (JSON-RPC)**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_sp500_portfolio",
    "arguments": {
      "sector": "Information Technology",
      "exposure_level": "high",
      "limit": 10,
      "sort_by": "affected_cogs_pct",
      "sort_desc": true
    }
  }
}
```

**Step 3: MCP Server Response**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "request_id": "rq_a1b2c3d4",
    "status": "success",
    "total_matches": 8,
    "returned_count": 8,
    "companies": [
      {
        "ticker": "APEX0",
        "company_name": "ApexTech Solutions",
        "sector": "Information Technology",
        "industry": "Software",
        "revenue_usd": 89234567890,
        "affected_cogs_pct": 0.45,
        "exposure_level": "high",
        "imports_into_us": true
      },
      {
        "ticker": "CHIP1",
        "company_name": "ChipMaker Inc",
        "sector": "Information Technology",
        "industry": "Semiconductors",
        "revenue_usd": 67890123456,
        "affected_cogs_pct": 0.42,
        "exposure_level": "high",
        "imports_into_us": true
      }
      // ... 6 more companies
    ],
    "processing_time_ms": 12.34
  }
}
```

**Step 4: Agent Formats Response for User**
```
Agent: "I found 8 technology companies with high tariff exposure:

1. **ApexTech Solutions (APEX0)** - Software
   - 45% of COGS affected by tariffs
   - Revenue: $89.2B
   - Imports from China: Yes

2. **ChipMaker Inc (CHIP1)** - Semiconductors
   - 42% of COGS affected by tariffs
   - Revenue: $67.9B
   - Imports from China: Yes

[... continues with other companies ...]

These companies are at high risk from tariff changes due to their
significant reliance on imported components from China."
```

---

### Example 2: User Asks "What's the overall portfolio exposure?"

**Step 1: User Question**
```
User: "What's the overall portfolio exposure to tariffs?"
```

**Step 2: Agent Calls MCP Tool**

**MCP Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_exposure_summary",
    "arguments": {}
  }
}
```

**Step 3: MCP Server Response**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "request_id": "rq_e5f6g7h8",
    "status": "success",
    "portfolio_overview": {
      "total_companies": 60,
      "total_investment_usd": 60000000,
      "total_revenue_usd": 3456789012345,
      "total_cogs_usd": 1234567890123,
      "total_affected_cogs_usd": 456789012345,
      "overall_exposure_pct": 0.37,
      "companies_importing_from_china": 54
    },
    "exposure_level_breakdown": {
      "high": 28,
      "medium": 20,
      "low": 6,
      "none": 6
    },
    "top_exposed_companies": [
      {
        "ticker": "RETAIL5",
        "company_name": "RetailGiant Corp",
        "sector": "Consumer Discretionary",
        "exposure_level": "high",
        "affected_cogs_pct": 0.58
      }
      // ... 9 more companies
    ],
    "sector_exposure_ranking": [
      {
        "sector": "Consumer Discretionary",
        "exposure_pct": 0.52
      },
      {
        "sector": "Information Technology",
        "exposure_pct": 0.35
      }
      // ... more sectors
    ],
    "processing_time_ms": 18.92
  }
}
```

**Step 4: Agent Formats Response**
```
Agent: "Here's your portfolio's tariff exposure summary:

📊 **Portfolio Overview:**
- Total Companies: 60
- Total Investment: $60M
- Companies Importing from China: 54 (90%)
- Overall Exposure: 37% of COGS affected

⚠️ **Exposure Breakdown:**
- High Risk: 28 companies (47%)
- Medium Risk: 20 companies (33%)
- Low Risk: 6 companies (10%)
- No Risk: 6 companies (10%)

🔝 **Most Exposed Sectors:**
1. Consumer Discretionary - 52% exposure
2. Information Technology - 35% exposure

🎯 **Top Exposed Company:**
RetailGiant Corp (RETAIL5) - 58% of COGS affected

Your portfolio has significant tariff exposure, with nearly half
of your companies in the high-risk category."
```

---

### Example 3: User Asks "Tell me about ApexTech"

**MCP Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_company_details",
    "arguments": {
      "company_name": "ApexTech"
    }
  }
}
```

**MCP Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "request_id": "rq_i9j0k1l2",
    "status": "success",
    "company": {
      "ticker": "APEX0",
      "company_name": "ApexTech Solutions",
      "sector": "Information Technology",
      "industry": "Software",
      "investment_usd": 1000000,
      "revenue_usd": 89234567890,
      "cogs_usd": 26770370367,
      "gross_margin_pct": 0.7,
      "imports_into_us": true,
      "affected_cogs_pct": 0.45,
      "exposure_level": "high",
      "confidence": 0.85
    },
    "calculated_metrics": {
      "affected_cogs_usd": 12046666665.15,
      "potential_tariff_impact_usd": 3011666666.29,
      "revenue_to_cogs_ratio": 3.33,
      "exposure_risk_score": 0.45
    },
    "processing_time_ms": 8.21
  }
}
```

**Agent Response**:
```
Agent: "Here's the detailed analysis for ApexTech Solutions (APEX0):

💼 **Company Profile:**
- Sector: Information Technology
- Industry: Software
- Revenue: $89.2B
- Gross Margin: 70%

⚠️ **Tariff Exposure:**
- Exposure Level: HIGH
- 45% of COGS affected by tariffs
- Affected COGS: $12.0B
- Potential Tariff Impact (25% rate): $3.0B
- Imports from China: Yes

📊 **Risk Assessment:**
- Exposure Risk Score: 0.45
- Revenue-to-COGS Ratio: 3.33x
- Data Confidence: 85%

ApexTech has high tariff exposure with nearly half of its cost
structure vulnerable to tariff changes. A 25% tariff could impact
profits by approximately $3B."
```

---

## 🚀 Deployment to Azure Container Apps

### Prerequisites

Before deploying, ensure you have:
- ✅ **Azure CLI** installed ([Download](https://aka.ms/installazurecliwindows))
- ✅ **Azure subscription** with appropriate permissions
- ✅ **Docker** (optional, ACR builds the image for you)
- ✅ **PowerShell** (Windows) or **Bash** (Mac/Linux)

### Quick Deployment (5 Minutes)

#### PowerShell (Windows)

```powershell
# Navigate to the tools_agentservice directory
cd 

# Run the deployment script
.\deploy_to_aca_v2.ps1
```


### What the Deployment Script Does

The script automatically:

1. ✅ **Checks Azure CLI** - Verifies Azure CLI is installed
2. ✅ **Logs into Azure** - Ensures you're authenticated
3. ✅ **Creates Resource Group** - Creates `rg-sp500-mcp` in East US
4. ✅ **Creates Azure Container Registry** - Creates `acrsp500mcp` (if not exists)
5. ✅ **Builds Docker Image** - Builds image using `Dockerfile.v2`
6. ✅ **Pushes to ACR** - Pushes `sp500-mcp-server-v2:latest` to registry
7. ✅ **Creates Container App Environment** - Creates `sp500-mcp-env` (if not exists)
8. ✅ **Deploys Container App** - Creates/updates `sp500-mcp-server-v2`
9. ✅ **Outputs URL** - Displays your MCP server URL

### Expected Output

```
🚀 Deploying SP500 MCP Server V2 (Azure-Compatible) to Azure Container Apps
================================================================================
✨ This version uses Azure AI Foundry compatible schemas (no anyOf/oneOf/allOf)
================================================================================

✅ Azure CLI found: 2.xx.x
✅ Logged in as: your-email@microsoft.com
   Subscription: Your Subscription Name

📦 Step 1: Verifying Resource Group...
✅ Resource group 'rg-sp500-mcp' verified

🏗️ Step 2: Verifying Azure Container Registry...
✅ ACR 'acrsp500mcp' verified

🐳 Step 3: Building and pushing Docker image (V2)...
   Using Dockerfile.v2 with sp500_mcp_server_v2.py
   This may take a few minutes...
✅ Docker image V2 built and pushed to ACR

🌐 Step 4: Verifying Container Apps Environment...
✅ Container Apps environment 'sp500-mcp-env' verified

🚢 Step 5: Deploying Container App V2...
   Creating new Container App V2...
✅ Container App V2 deployed successfully

================================================================================
✅ DEPLOYMENT SUCCESSFUL!
================================================================================

📊 MCP Server V2 Details:
   Resource Group: rg-sp500-mcp
   Container App: sp500-mcp-server-v2
   MCP Server URL: https://sp500-mcp-server-v2.wonderfulsand-23ca85b9.eastus.azurecontainerapps.io/mcp
   Server Name: sp500-portfolio-analysis-v2

🧪 Test your server:
   Invoke-RestMethod -Uri "https://sp500-mcp-server-v2.wonderfulsand-23ca85b9.eastus.azurecontainerapps.io/mcp" `
     -Method POST `
     -ContentType "application/json" `
     -Body '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

📚 Next Steps:
   1. Test the MCP server with the command above
   2. Create an Azure AI agent that uses this MCP server
   3. Configure agent with server URL and allowed tools

================================================================================
```

### Deployment Configuration

The deployment uses these settings:

| Setting | Value | Description |
|---------|-------|-------------|
| **Resource Group** | `rg-sp500-mcp` | Azure resource group |
| **Location** | `eastus` | Azure region |
| **Container App** | `sp500-mcp-server-v2` | Container app name |
| **Environment** | `sp500-mcp-env` | Container Apps environment |
| **ACR** | `acrsp500mcp` | Azure Container Registry |
| **Image** | `sp500-mcp-server-v2:latest` | Docker image |
| **Port** | `8001` | Internal container port |
| **Ingress** | `external` | Public HTTPS endpoint |
| **Min Replicas** | `1` | Minimum instances |
| **Max Replicas** | `3` | Maximum instances (auto-scale) |
| **CPU** | `0.5` cores | CPU allocation |
| **Memory** | `1.0 Gi` | Memory allocation |

### Environment Variables Set

```bash
FASTMCP_TRANSPORT=streamable-http
FASTMCP_PORT=8001
FASTMCP_HOST=0.0.0.0
MCP_FASTMCP_SERVER_NAME=sp500-portfolio-analysis-v2
```

---

