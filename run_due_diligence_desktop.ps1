$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
$Host.UI.RawUI.WindowTitle = 'Global Intelligence - Due Diligence'

function Read-RequiredValue([string]$Prompt) {
    while ($true) {
        $value = (Read-Host $Prompt).Trim()
        if ($value) {
            return $value
        }
        Write-Host '此项必填，请重新输入。' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'Global Intelligence 对手方与制裁风险核验' -ForegroundColor Cyan
Write-Host '当前名单/企业登记源可能尚未接入；未核验会明确标记并要求人工复核。' -ForegroundColor Yellow
Write-Host ''

$query = Read-Host '核验事项（回车使用默认值：核验交易对手身份与制裁风险）'
if (-not $query.Trim()) {
    $query = '核验交易对手身份与制裁风险'
}

$name = Read-RequiredValue '交易对手法定名称'
while ($name -match '^\d+$' -or $name -notmatch '\p{L}') {
    Write-Host '不能使用纯数字作为公司名称；请输入真实法定名称。' -ForegroundColor Yellow
    $name = Read-RequiredValue '交易对手法定名称'
}
$country = Read-RequiredValue '注册国家/地区（例如 Kazakhstan）'
while ($country -match '^\d+$' -or $country -notmatch '\p{L}') {
    Write-Host '请输入国家/地区名称，不要使用纯数字占位。' -ForegroundColor Yellow
    $country = Read-RequiredValue '注册国家/地区（例如 Kazakhstan）'
}
$aliasesText = Read-Host '别名（可选，多个用英文逗号分隔）'
$registrationNumber = Read-Host '注册号（可选）'
$aliases = @()
if ($aliasesText.Trim()) {
    $aliases = @($aliasesText.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host '未找到 Python。请安装 Python 3.12，并将 python 加入 PATH。' -ForegroundColor Red
    Read-Host '按回车关闭窗口' | Out-Null
    exit 2
}

& $python.Source -c 'import fastapi' 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host '正在安装项目依赖……' -ForegroundColor Cyan
    & $python.Source -m pip install -r (Join-Path $projectRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        Write-Host '依赖安装失败。请检查网络或手动运行：python -m pip install -r requirements.txt' -ForegroundColor Red
        Read-Host '按回车关闭窗口' | Out-Null
        exit 2
    }
}

$request = @{
    query = $query.Trim()
    metadata = @{
        counterparties = @(@{
            name = $name
            aliases = $aliases
            country = $country
            registration_number = $registrationNumber.Trim()
        })
        sanctions_screening_required = $true
    }
}

$requestPath = Join-Path ([System.IO.Path]::GetTempPath()) ("global-intelligence-due-diligence-{0}.json" -f [guid]::NewGuid())
$json = $request | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($requestPath, $json, [System.Text.UTF8Encoding]::new($false))
$runId = 'desktop-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$previousRunId = $env:GITHUB_RUN_ID
$env:GITHUB_RUN_ID = $runId

if (-not $env:BING_SEARCH_KEY -and -not $env:BRAVE_SEARCH_API_KEY) {
    Write-Host '提示：BING_SEARCH_KEY/BRAVE_SEARCH_API_KEY 均未配置，Web 公司资料搜索可能无结果。' -ForegroundColor Yellow
}

try {
    Write-Host ''
    Write-Host '正在运行核验……' -ForegroundColor Cyan
    & $python.Source (Join-Path $projectRoot 'backend\workflows\run_due_diligence.py') --input $requestPath
    $runExitCode = $LASTEXITCODE
}
finally {
    Remove-Item $requestPath -Force -ErrorAction SilentlyContinue
    if ($null -eq $previousRunId) {
        Remove-Item Env:\GITHUB_RUN_ID -ErrorAction SilentlyContinue
    } else {
        $env:GITHUB_RUN_ID = $previousRunId
    }
}

Write-Host ''
Write-Host '记忆位置：memory\due_diligence_learning.json（只保存匿名状态与统计）'
Write-Host '详细报告目录：backend\reports\due_diligence'
if ($runExitCode -ne 0) {
    Write-Host '本次执行未完成，请查看上方错误信息。' -ForegroundColor Red
} else {
    Write-Host '运行结束。未决或不可用的权威来源需要人工复核。' -ForegroundColor Green
}
$markdownReport = Join-Path $projectRoot ("backend\reports\due_diligence\due_diligence_{0}.md" -f $runId)
if (Test-Path $markdownReport) {
    Write-Host '正在打开本次详细报告……' -ForegroundColor Cyan
    Start-Process -FilePath 'notepad.exe' -ArgumentList ('"' + $markdownReport + '"')
}
Read-Host '按回车关闭窗口' | Out-Null
exit $runExitCode