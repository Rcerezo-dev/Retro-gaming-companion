param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$python = 'C:\Users\rammu\AppData\Local\Programs\Python\Python312\python.exe'

if (-not (Test-Path $python)) {
    Write-Error "Python not found at $python"
    exit 1
}

$env:PYTHONPATH = 'src'
& $python -m rom_manager @Args
exit $LASTEXITCODE
