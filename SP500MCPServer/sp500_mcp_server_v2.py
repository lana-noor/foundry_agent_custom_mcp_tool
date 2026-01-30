"""SP500 Portfolio Analysis MCP Server V2 - Azure AI Foundry Compatible

This version generates Azure-compatible JSON schemas by avoiding:
- anyOf, oneOf, allOf
- Nullable union types (e.g., string | null)
- Complex validation logic

All optional parameters use empty strings/defaults instead of Optional types.
"""

import argparse
import csv
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Annotated, Any, Dict, List

from fastmcp import Context, FastMCP

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
SERVER_NAME = os.environ.get("MCP_FASTMCP_SERVER_NAME", "sp500-portfolio-analysis-v2")
PORTFOLIO_CSV_PATH = Path(__file__).parent / "sp500_style_portfolio_60.csv"

server = FastMCP(SERVER_NAME)

# Cache for portfolio data
_portfolio_cache: List[Dict[str, Any]] = []


def load_portfolio_data() -> List[Dict[str, Any]]:
    """Load and cache SP500 portfolio data from CSV."""
    global _portfolio_cache
    
    if _portfolio_cache:
        return _portfolio_cache
    
    if not PORTFOLIO_CSV_PATH.exists():
        logger.error(f"Portfolio CSV not found at {PORTFOLIO_CSV_PATH}")
        return []
    
    portfolio_data = []
    with open(PORTFOLIO_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            numeric_fields = [
                'investment_usd', 'revenue_usd', 'cogs_usd', 
                'gross_margin_pct', 'fiscal_year', 'affected_cogs_pct', 'confidence'
            ]
            for field in numeric_fields:
                if field in row and row[field]:
                    try:
                        row[field] = float(row[field])
                    except (ValueError, TypeError):
                        row[field] = 0.0
            
            # Convert boolean fields
            if 'imports_into_us' in row:
                row['imports_into_us'] = row['imports_into_us'].upper() == 'TRUE'
            
            portfolio_data.append(row)
    
    _portfolio_cache = portfolio_data
    logger.info(f"✅ Loaded {len(portfolio_data)} companies from SP500 portfolio CSV")
    return portfolio_data


@server.tool(
    name="query_sp500_portfolio",
    title="Query SP500 Portfolio",
    description="""Query the SP500 portfolio dataset with flexible filtering options.

    Use this tool when the user asks about:
    - Companies in specific sectors (e.g., "tech companies", "consumer discretionary")
    - Companies in specific industries (e.g., "software", "semiconductors")
    - Exposure levels (e.g., "high exposure", "companies at risk")
    - Companies that import from China
    - Financial metrics (revenue, COGS, margins)
    - Specific companies by name or ticker
    
    Returns matching companies with all their data fields.
    All filter parameters are optional - use empty strings to skip filtering.
    """
)
async def query_sp500_portfolio(
    sector: Annotated[str, "Filter by sector (e.g., 'Information Technology', 'Consumer Discretionary'). Use empty string to skip."] = "",
    industry: Annotated[str, "Filter by industry (e.g., 'Software', 'Semiconductors', 'Retail'). Use empty string to skip."] = "",
    exposure_level: Annotated[str, "Filter by exposure level: 'high', 'medium', 'low', or 'none'. Use empty string to skip."] = "",
    imports_filter: Annotated[str, "Filter by import status: 'yes' for importers, 'no' for non-importers, empty string to skip."] = "",
    min_revenue: Annotated[float, "Minimum revenue in USD. Use 0 to skip."] = 0.0,
    max_revenue: Annotated[float, "Maximum revenue in USD. Use 0 to skip."] = 0.0,
    min_affected_cogs_pct: Annotated[float, "Minimum percentage of COGS affected by tariffs (0.0 to 1.0). Use 0 to skip."] = 0.0,
    company_name: Annotated[str, "Search by company name (partial match). Use empty string to skip."] = "",
    ticker: Annotated[str, "Filter by ticker symbol. Use empty string to skip."] = "",
    limit: Annotated[int, "Maximum number of results to return"] = 20,
    sort_by: Annotated[str, "Sort results by field: 'revenue_usd', 'affected_cogs_pct', 'confidence', 'investment_usd'. Use empty string for default."] = "",
    sort_desc: Annotated[bool, "Sort in descending order"] = True,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    Query SP500 portfolio with flexible filtering and sorting.
    Returns matching companies with all their data fields.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"🔧 TOOL CALLED: query_sp500_portfolio [ID: {request_id}]")
    logger.info(f"   └─ Filters: sector={sector}, industry={industry}, exposure={exposure_level}, limit={limit}")
    
    try:
        data = load_portfolio_data()
        results = data.copy()
        
        # Apply filters (only if not empty/zero)
        if sector:
            results = [c for c in results if c.get('sector', '').lower() == sector.lower()]
        
        if industry:
            results = [c for c in results if c.get('industry', '').lower() == industry.lower()]
        
        if exposure_level:
            results = [c for c in results if c.get('exposure_level', '').lower() == exposure_level.lower()]
        
        if imports_filter:
            if imports_filter.lower() == 'yes':
                results = [c for c in results if c.get('imports_into_us')]
            elif imports_filter.lower() == 'no':
                results = [c for c in results if not c.get('imports_into_us')]
        
        if min_revenue > 0:
            results = [c for c in results if float(c.get('revenue_usd', 0)) >= min_revenue]

        if max_revenue > 0:
            results = [c for c in results if float(c.get('revenue_usd', 0)) <= max_revenue]

        if min_affected_cogs_pct > 0:
            results = [c for c in results if float(c.get('affected_cogs_pct', 0)) >= min_affected_cogs_pct]

        if company_name:
            results = [c for c in results if company_name.lower() in c.get('company_name', '').lower()]

        if ticker:
            results = [c for c in results if c.get('ticker', '').upper() == ticker.upper()]

        total_matches = len(results)

        # Sort results
        if sort_by and sort_by in ['revenue_usd', 'affected_cogs_pct', 'confidence', 'investment_usd']:
            results = sorted(results, key=lambda x: float(x.get(sort_by, 0)), reverse=sort_desc)

        # Limit results
        results = results[:limit]

        elapsed_time = time.time() - start_time

        result = {
            "request_id": f"rq_{request_id}",
            "status": "success",
            "total_matches": total_matches,
            "returned_count": len(results),
            "companies": results,
            "processing_time_ms": round(elapsed_time * 1000, 2)
        }

        logger.info(f"✅ TOOL SUCCESS: query_sp500_portfolio [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.info(f"   └─ Returned {len(results)} of {total_matches} matches")

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ TOOL ERROR: query_sp500_portfolio [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.error(f"   └─ Error: {type(e).__name__}: {str(e)}")
        raise


@server.tool(
    name="get_company_details",
    title="Get Company Details",
    description="""Get detailed information about a specific company by ticker or name.

    Use this when the user asks about a specific company:
    - "Tell me about ApexTech"
    - "What's the exposure for APEX0?"
    - "Show me details for Nike"

    Provide either ticker OR company_name (at least one must be non-empty).
    """
)
async def get_company_details(
    ticker: Annotated[str, "Company ticker symbol. Use empty string if searching by name."] = "",
    company_name: Annotated[str, "Company name (partial match allowed). Use empty string if searching by ticker."] = "",
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific company.
    Returns all available data fields for the company.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"🔧 TOOL CALLED: get_company_details [ID: {request_id}]")
    logger.info(f"   └─ Ticker: {ticker}, Company Name: {company_name}")

    try:
        if not ticker and not company_name:
            return {
                "request_id": f"rq_{request_id}",
                "status": "error",
                "error": "Must provide either ticker or company_name",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        data = load_portfolio_data()
        company = None

        # Search by ticker first (exact match)
        if ticker:
            for c in data:
                if c.get('ticker', '').upper() == ticker.upper():
                    company = c
                    break

        # If not found, search by name (partial match)
        if not company and company_name:
            for c in data:
                if company_name.lower() in c.get('company_name', '').lower():
                    company = c
                    break

        if not company:
            return {
                "request_id": f"rq_{request_id}",
                "status": "not_found",
                "message": f"No company found matching ticker='{ticker}' or name='{company_name}'",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Calculate additional metrics
        revenue = float(company.get('revenue_usd', 0))
        cogs = float(company.get('cogs_usd', 0))
        affected_pct = float(company.get('affected_cogs_pct', 0))
        affected_cogs_usd = cogs * affected_pct
        potential_impact_usd = affected_cogs_usd * 0.25  # Assuming 25% tariff

        elapsed_time = time.time() - start_time

        result = {
            "request_id": f"rq_{request_id}",
            "status": "success",
            "company": company,
            "calculated_metrics": {
                "affected_cogs_usd": affected_cogs_usd,
                "potential_tariff_impact_usd": potential_impact_usd,
                "revenue_to_cogs_ratio": revenue / cogs if cogs > 0 else 0,
                "exposure_risk_score": affected_pct * (1 if company.get('imports_into_us') else 0)
            },
            "processing_time_ms": round(elapsed_time * 1000, 2)
        }

        logger.info(f"✅ TOOL SUCCESS: get_company_details [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.info(f"   └─ Found: {company.get('company_name')} ({company.get('ticker')})")

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ TOOL ERROR: get_company_details [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.error(f"   └─ Error: {type(e).__name__}: {str(e)}")
        raise


@server.tool(
    name="get_sector_analysis",
    title="Get Sector Analysis",
    description="""Analyze portfolio holdings by sector with aggregated metrics.

    Use this when the user asks about:
    - "Which sectors are most exposed?"
    - "Show me sector breakdown"
    - "Analyze by sector"
    - "What's the technology sector exposure?"

    Leave sector empty to analyze all sectors, or specify a sector name to analyze just that sector.
    """
)
async def get_sector_analysis(
    sector: Annotated[str, "Specific sector to analyze. Use empty string for all sectors."] = "",
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    Analyze portfolio by sector with aggregated exposure and financial metrics.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"🔧 TOOL CALLED: get_sector_analysis [ID: {request_id}]")
    logger.info(f"   └─ Sector: {sector or 'All sectors'}")

    try:
        data = load_portfolio_data()

        # Filter by sector if specified
        if sector:
            data = [c for c in data if c.get('sector', '').lower() == sector.lower()]
            if not data:
                return {
                    "request_id": f"rq_{request_id}",
                    "status": "not_found",
                    "message": f"No companies found in sector '{sector}'",
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2)
                }

        # Group by sector
        sectors_data = {}
        for company in data:
            sec = company.get('sector', 'Unknown')
            if sec not in sectors_data:
                sectors_data[sec] = {
                    'companies': [],
                    'total_investment': 0,
                    'total_revenue': 0,
                    'total_cogs': 0,
                    'total_affected_cogs': 0,
                    'importers_count': 0
                }

            sectors_data[sec]['companies'].append(company)
            sectors_data[sec]['total_investment'] += float(company.get('investment_usd', 0))
            sectors_data[sec]['total_revenue'] += float(company.get('revenue_usd', 0))

            cogs = float(company.get('cogs_usd', 0))
            affected_pct = float(company.get('affected_cogs_pct', 0))
            sectors_data[sec]['total_cogs'] += cogs
            sectors_data[sec]['total_affected_cogs'] += cogs * affected_pct

            if company.get('imports_into_us'):
                sectors_data[sec]['importers_count'] += 1

        # Build sector summaries
        sector_summaries = []
        for sec_name, sec_data in sectors_data.items():
            total_cogs = sec_data['total_cogs']
            avg_exposure = (sec_data['total_affected_cogs'] / total_cogs) if total_cogs > 0 else 0

            sector_summaries.append({
                'sector': sec_name,
                'company_count': len(sec_data['companies']),
                'total_investment_usd': sec_data['total_investment'],
                'total_revenue_usd': sec_data['total_revenue'],
                'total_cogs_usd': total_cogs,
                'total_affected_cogs_usd': sec_data['total_affected_cogs'],
                'average_exposure_pct': avg_exposure,
                'importers_count': sec_data['importers_count'],
                'top_exposed_companies': sorted(
                    sec_data['companies'],
                    key=lambda x: float(x.get('affected_cogs_pct', 0)),
                    reverse=True
                )[:5]
            })

        # Sort by total investment
        sector_summaries = sorted(sector_summaries, key=lambda x: x['total_investment_usd'], reverse=True)

        elapsed_time = time.time() - start_time

        result = {
            "request_id": f"rq_{request_id}",
            "status": "success",
            "sector_count": len(sector_summaries),
            "sectors": sector_summaries,
            "processing_time_ms": round(elapsed_time * 1000, 2)
        }

        logger.info(f"✅ TOOL SUCCESS: get_sector_analysis [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.info(f"   └─ Analyzed {len(sector_summaries)} sectors")

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ TOOL ERROR: get_sector_analysis [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.error(f"   └─ Error: {type(e).__name__}: {str(e)}")
        raise


@server.tool(
    name="get_exposure_summary",
    title="Get Tariff Exposure Summary",
    description="""Get comprehensive summary of tariff exposure across the entire SP500 portfolio.

    Use this when the user asks about:
    - "What's the overall exposure?"
    - "Give me a portfolio summary"
    - "How exposed is the portfolio to tariffs?"
    - "Show me the exposure breakdown"

    This tool takes no parameters and returns a complete portfolio overview.
    """
)
async def get_exposure_summary(
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    Get comprehensive tariff exposure summary for the entire SP500 portfolio.
    Includes exposure levels, sector breakdown, top exposed companies, and risk metrics.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"🔧 TOOL CALLED: get_exposure_summary [ID: {request_id}]")

    try:
        data = load_portfolio_data()

        # Overall metrics
        total_companies = len(data)
        total_investment = sum(float(c.get('investment_usd', 0)) for c in data)
        total_revenue = sum(float(c.get('revenue_usd', 0)) for c in data)
        total_cogs = sum(float(c.get('cogs_usd', 0)) for c in data)

        importers = [c for c in data if c.get('imports_into_us')]

        # Calculate total affected COGS
        total_affected_cogs = sum(
            float(c.get('cogs_usd', 0)) * float(c.get('affected_cogs_pct', 0))
            for c in data
        )

        # Exposure level breakdown
        exposure_breakdown = {
            'high': len([c for c in data if c.get('exposure_level', '').lower() == 'high']),
            'medium': len([c for c in data if c.get('exposure_level', '').lower() == 'medium']),
            'low': len([c for c in data if c.get('exposure_level', '').lower() == 'low']),
            'none': len([c for c in data if c.get('exposure_level', '').lower() == 'none'])
        }

        # Sector exposure ranking
        sectors = {}
        for company in data:
            sector = company.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = {'total_cogs': 0, 'affected_cogs': 0}

            cogs = float(company.get('cogs_usd', 0))
            affected_pct = float(company.get('affected_cogs_pct', 0))
            sectors[sector]['total_cogs'] += cogs
            sectors[sector]['affected_cogs'] += cogs * affected_pct

        sector_exposure_sorted = [
            {
                'sector': sec,
                'exposure_pct': (data['affected_cogs'] / data['total_cogs']) if data['total_cogs'] > 0 else 0
            }
            for sec, data in sectors.items()
        ]
        sector_exposure_sorted = sorted(sector_exposure_sorted, key=lambda x: x['exposure_pct'], reverse=True)

        # Top exposed companies
        top_exposed = sorted(data, key=lambda x: float(x.get('affected_cogs_pct', 0)), reverse=True)[:10]

        elapsed_time = time.time() - start_time

        result = {
            "request_id": f"rq_{request_id}",
            "status": "success",
            "portfolio_overview": {
                "total_companies": total_companies,
                "total_investment_usd": total_investment,
                "total_revenue_usd": total_revenue,
                "total_cogs_usd": total_cogs,
                "total_affected_cogs_usd": total_affected_cogs,
                "overall_exposure_pct": total_affected_cogs / total_cogs if total_cogs > 0 else 0,
                "companies_importing_from_china": len(importers)
            },
            "exposure_level_breakdown": exposure_breakdown,
            "top_exposed_companies": [
                {
                    "ticker": c.get('ticker'),
                    "company_name": c.get('company_name'),
                    "sector": c.get('sector'),
                    "exposure_level": c.get('exposure_level'),
                    "affected_cogs_pct": c.get('affected_cogs_pct'),
                    "imports_into_us": c.get('imports_into_us')
                }
                for c in top_exposed
            ],
            "sector_exposure_ranking": sector_exposure_sorted,
            "processing_time_ms": round(elapsed_time * 1000, 2)
        }

        logger.info(f"✅ TOOL SUCCESS: get_exposure_summary [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.info(f"   └─ Portfolio: {len(data)} companies, {len(importers)} importing from China")

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ TOOL ERROR: get_exposure_summary [ID: {request_id}] ({elapsed_time:.3f}s)")
        logger.error(f"   └─ Error: {type(e).__name__}: {str(e)}")
        raise


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="SP500 Portfolio Analysis MCP Server V2 (Azure-Compatible)")
    parser.add_argument("--transport", default="streamable-http", help="Transport type")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--show-banner", action="store_true", help="Show FastMCP banner")

    args = parser.parse_args()

    transport = args.transport
    show_banner = args.show_banner

    run_kwargs = {}
    if transport == "streamable-http":
        run_kwargs["port"] = args.port
        run_kwargs["host"] = args.host

    # Pre-load data to verify CSV exists
    logger.info("🚀 Starting SP500 Portfolio Analysis MCP Server V2 (Azure-Compatible)...")
    load_portfolio_data()

    logger.info(f"📊 Server Name: {SERVER_NAME}")
    logger.info(f"📁 Data Source: {PORTFOLIO_CSV_PATH.absolute()}")
    logger.info(f"🔧 Available Tools:")
    logger.info(f"   - query_sp500_portfolio: Query portfolio with flexible filters")
    logger.info(f"   - get_company_details: Get detailed company information")
    logger.info(f"   - get_sector_analysis: Analyze portfolio by sector")
    logger.info(f"   - get_exposure_summary: Get comprehensive exposure summary")
    logger.info(f"✨ Schema: Azure AI Foundry compatible (no anyOf/oneOf/allOf)")

    server.run(transport=transport, show_banner=show_banner, **run_kwargs)


if __name__ == "__main__":
    main()


