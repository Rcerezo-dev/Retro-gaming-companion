param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$python = 'C:\Users\rammu\anaconda3\envs\rom_manager\python.exe'

if (-not (Test-Path $python)) {
    Write-Error "Python not found at $python"
    exit 1
}

$env:PYTHONPATH = 'src'
& $python -m rom_manager @Args
exit $LASTEXITCODE
