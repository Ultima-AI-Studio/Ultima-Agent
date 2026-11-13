[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Write-Failure {
    param([Parameter(Mandatory = $true)][string]$Reason)

    Write-Output "SHIPPED_TASKS_RESULT=FAIL reason=$Reason"
    exit 1
}

try {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $manifestPath = Join-Path $projectRoot 'installer\shipped-tasks.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        Write-Failure 'manifest-missing'
    }

    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
    if ($manifest.schema -ne 'ultimaagent-shipped-tasks/v1') {
        Write-Failure 'schema-invalid'
    }

    if (-not ($manifest.PSObject.Properties.Name -contains 'shipped_tasks')) {
        Write-Failure 'shipped_tasks-missing'
    }

    if (-not ($manifest.shipped_tasks -is [System.Array])) {
        Write-Failure 'shipped_tasks-not-array'
    }

    if (@($manifest.shipped_tasks).Count -ne 0) {
        Write-Failure 'shipped_tasks-not-empty'
    }

    $schtasksPath = Join-Path $env:SystemRoot 'System32\schtasks.exe'
    if (-not (Test-Path -LiteralPath $schtasksPath -PathType Leaf)) {
        Write-Failure 'schtasks-missing'
    }

    $queryOutput = @(& $schtasksPath /query /v /fo csv 2>&1)
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "schtasks-query-exit-$LASTEXITCODE"
    }

    $csvLines = @($queryOutput | Where-Object {
        $_ -is [string] -and $_.TrimStart().StartsWith('"')
    })
    if ($csvLines.Count -eq 0) {
        Write-Failure 'schtasks-csv-empty'
    }

    $rows = @(($csvLines -join [Environment]::NewLine) | ConvertFrom-Csv)
    $taskNames = @()
    if ($rows.Count -gt 0) {
        $taskNameProperty = $rows[0].PSObject.Properties.Name[1]
        $taskNames = @($rows | ForEach-Object { [string]($_.$taskNameProperty) } |
            Where-Object { $_ -match '^\\?UltimaAgent' } |
            Sort-Object -Unique)
    }

    if ($taskNames.Count -ne 0) {
        $displayNames = ($taskNames | ForEach-Object { $_.TrimStart('\') }) -join ','
        Write-Failure "scheduled-tasks-present count=$($taskNames.Count) tasks=$displayNames"
    }

    Write-Output 'SHIPPED_TASKS_RESULT=PASS'
    exit 0
}
catch {
    $safeMessage = ($_.Exception.Message -replace '[^\x20-\x7E]', '?') -replace '\s+', '-'
    Write-Failure "exception-$safeMessage"
}
