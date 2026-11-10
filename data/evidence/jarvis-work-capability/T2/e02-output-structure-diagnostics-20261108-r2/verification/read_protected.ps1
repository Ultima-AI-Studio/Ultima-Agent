param([ValidateSet('before','after')][string]$Checkpoint='before')
$ErrorActionPreference='Stop'
$baselinePath='H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source-reference-schema-20261107-r1\inputs\protected-baseline.json'
$baseline=Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
$identities=@($baseline.protected5)+@($baseline.protected_listener_pair)
if($identities.Count -ne 7){throw 'Expected seven protected identities'}
$observed=@(foreach($identity in $identities){
    try {
        $process=Get-Process -Id $identity.pid -ErrorAction Stop
        $creation=$process.StartTime.ToUniversalTime().ToFileTimeUtc()
        $exe=$process.Path
        [pscustomobject]@{role=$identity.role;pid=$identity.pid;created_filetime=$creation;exe=$exe;matches=($creation -eq $identity.created_filetime -and $exe -ieq $identity.exe);error=$null}
    } catch {
        [pscustomobject]@{role=$identity.role;pid=$identity.pid;created_filetime=$null;exe=$null;matches=$false;error=$_.Exception.GetType().Name}
    }
})
$record=[pscustomobject]@{checkpoint=$Checkpoint;recorded_utc=(Get-Date).ToUniversalTime().ToString('o');baseline_sha256=(Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant();protected=$observed;count=$observed.Count;all_match=(@($observed | Where-Object {-not $_.matches}).Count -eq 0);continuous_liveness_measured=$false;service_operations=0;model_calls=0}
$target=Join-Path $PSScriptRoot ('protected-seven-'+$Checkpoint+'.json')
if(Test-Path -LiteralPath $target){throw 'Checkpoint already exists'}
[IO.File]::WriteAllText($target,($record | ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{checkpoint=$Checkpoint;count=$record.count;all_match=$record.all_match;service_operations=0} | ConvertTo-Json
