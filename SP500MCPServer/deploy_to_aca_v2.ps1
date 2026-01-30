# PowerShell script to deploy SP500 MCP Server V2 (Azure-Compatible) to Azure Container Apps
# Usage: .\deploy_to_aca_v2.ps1

param(
    [string]$ResourceGroup = "rg-sp500-mcp",  # Same resource group as V1
    [string]$Location = "eastus",
    [string]$ContainerAppName = "sp500-mcp-server-v2",  # Different name from V1
    [string]$EnvironmentName = "sp500-mcp-env",  # Same environment as V1
    [string]$AcrName = "acrsp500mcp",  # Same ACR as V1
    [string]$ImageName = "sp500-mcp-server-v2",  # Different image name
    [string]$ImageTag = "latest"
)

Write-Host "🚀 Deploying SP500 MCP Server V2 (Azure-Compatible) to Azure Container Apps" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✨ This version uses Azure AI Foundry compatible schemas (no anyOf/oneOf/allOf)" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Cyan

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✅ Azure CLI found: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "   Download from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
Write-Host "`n📋 Checking Azure login status..." -ForegroundColor Cyan
$account = az account show 2>$null
if (-not $account) {
    Write-Host "❌ Not logged in to Azure. Running 'az login'..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Azure login failed" -ForegroundColor Red
        exit 1
    }
}

$accountInfo = az account show | ConvertFrom-Json
Write-Host "✅ Logged in as: $($accountInfo.user.name)" -ForegroundColor Green
Write-Host "   Subscription: $($accountInfo.name)" -ForegroundColor White

# Step 1: Verify Resource Group exists (should already exist from V1)
Write-Host "`n📦 Step 1: Verifying Resource Group..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Resource group '$ResourceGroup' verified" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to verify resource group" -ForegroundColor Red
    exit 1
}

# Step 2: Verify Azure Container Registry exists (should already exist from V1)
Write-Host "`n📦 Step 2: Verifying Azure Container Registry..." -ForegroundColor Cyan
$acrExists = az acr show --name $AcrName --resource-group $ResourceGroup 2>$null
if (-not $acrExists) {
    Write-Host "⚠️  ACR '$AcrName' doesn't exist. Creating it..." -ForegroundColor Yellow
    az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true --output none
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ ACR '$AcrName' created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create ACR" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ ACR '$AcrName' already exists" -ForegroundColor Green
}

# Step 3: Build and Push Docker Image (V2)
Write-Host "`n🐳 Step 3: Building and pushing Docker image (V2)..." -ForegroundColor Cyan
Write-Host "   Using Dockerfile.v2 with sp500_mcp_server_v2.py" -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Yellow

az acr build --registry $AcrName --image "${ImageName}:${ImageTag}" --file Dockerfile.v2 .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker image V2 built and pushed to ACR" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to build/push Docker image" -ForegroundColor Red
    exit 1
}

# Step 4: Get ACR credentials
Write-Host "`n🔑 Step 4: Getting ACR credentials..." -ForegroundColor Cyan
$acrServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer --output tsv
$acrUsername = az acr credential show --name $AcrName --resource-group $ResourceGroup --query username --output tsv
$acrPassword = az acr credential show --name $AcrName --resource-group $ResourceGroup --query "passwords[0].value" --output tsv

Write-Host "✅ ACR Server: $acrServer" -ForegroundColor Green

# Step 5: Verify Container Apps Environment exists (should already exist from V1)
Write-Host "`n🌍 Step 5: Verifying Container Apps Environment..." -ForegroundColor Cyan
$envExists = az containerapp env show --name $EnvironmentName --resource-group $ResourceGroup 2>$null
if (-not $envExists) {
    Write-Host "⚠️  Environment doesn't exist. Creating it..." -ForegroundColor Yellow
    az containerapp env create --name $EnvironmentName --resource-group $ResourceGroup --location $Location --output none
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container Apps Environment '$EnvironmentName' created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create Container Apps Environment" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Container Apps Environment '$EnvironmentName' already exists" -ForegroundColor Green
}

# Step 6: Deploy Container App V2
Write-Host "`n🚢 Step 6: Deploying Container App V2..." -ForegroundColor Cyan
Write-Host "   App Name: $ContainerAppName" -ForegroundColor Yellow

$fullImageName = "${acrServer}/${ImageName}:${ImageTag}"

# Check if V2 app already exists
$appExists = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup 2>$null

if (-not $appExists) {
    Write-Host "   Creating new Container App V2..." -ForegroundColor Yellow
    az containerapp create `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --environment $EnvironmentName `
        --image $fullImageName `
        --registry-server $acrServer `
        --registry-username $acrUsername `
        --registry-password $acrPassword `
        --target-port 8001 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --cpu 0.5 `
        --memory 1.0Gi `
        --env-vars "FASTMCP_TRANSPORT=streamable-http" "FASTMCP_PORT=8001" "FASTMCP_HOST=0.0.0.0" "MCP_FASTMCP_SERVER_NAME=sp500-portfolio-analysis-v2" `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container App V2 deployed successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to deploy Container App V2" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   Updating existing Container App V2..." -ForegroundColor Yellow
    az containerapp update `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --image $fullImageName `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container App V2 updated successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to update Container App V2" -ForegroundColor Red
        exit 1
    }
}

# Step 7: Get the URL
Write-Host "`n🌐 Step 7: Getting Container App V2 URL..." -ForegroundColor Cyan
$appUrl = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv

Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "`n📊 MCP Server V2 Details:" -ForegroundColor Cyan
Write-Host "   Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "   Container App: $ContainerAppName" -ForegroundColor White
Write-Host "   MCP Server URL: https://$appUrl/mcp" -ForegroundColor Yellow
Write-Host "   Server Name: sp500-portfolio-analysis-v2" -ForegroundColor White
Write-Host "`n✨ Key Differences from V1:" -ForegroundColor Cyan
Write-Host "   ✅ Azure AI Foundry compatible schemas" -ForegroundColor Green
Write-Host "   ✅ No anyOf/oneOf/allOf in JSON schemas" -ForegroundColor Green
Write-Host "   ✅ All optional parameters use empty strings/defaults" -ForegroundColor Green
Write-Host "   ✅ Works with Azure AI Foundry portal and SDK" -ForegroundColor Green
Write-Host "`n🔗 Use this URL in your agent configuration:" -ForegroundColor Cyan
Write-Host "   MCP_SERVER_URL=https://$appUrl/mcp" -ForegroundColor Green
Write-Host "   MCP_SERVER_LABEL=sp500_portfolio_analysis_v2" -ForegroundColor Green
Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Test the server:" -ForegroundColor White
Write-Host "      Invoke-RestMethod -Uri 'https://$appUrl/mcp' -Method POST -ContentType 'application/json' -Body '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}'" -ForegroundColor Gray
Write-Host "   2. Update your agent configuration to use the V2 URL" -ForegroundColor White
Write-Host "   3. Monitor logs:" -ForegroundColor White
Write-Host "      az containerapp logs show --name $ContainerAppName --resource-group $ResourceGroup --follow" -ForegroundColor Gray
Write-Host "`n💡 Comparison:" -ForegroundColor Cyan
Write-Host "   V1 URL: https://sp500-mcp-server.wonderfulsand-23ca85b9.eastus.azurecontainerapps.io/mcp" -ForegroundColor Gray
Write-Host "   V2 URL: https://$appUrl/mcp" -ForegroundColor Yellow
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan


