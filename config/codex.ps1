param([Parameter(Mandatory = $true)][string]$PluginRoot)

$root = (Resolve-Path -LiteralPath $PluginRoot).Path
python -B (Join-Path $root 'scripts/build_package.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
codex plugin marketplace add $root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
codex plugin add tradingbot-intelligence@tradingbot-local
exit $LASTEXITCODE
