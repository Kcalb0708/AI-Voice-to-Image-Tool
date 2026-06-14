param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$frontendUrl = "http://127.0.0.1:5173/"

function U {
    param([string]$Escaped)
    return [System.Text.RegularExpressions.Regex]::Unescape($Escaped)
}

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================"
    Write-Host " $Message"
    Write-Host "========================================"
    Write-Host ""
}

function Assert-Path {
    param(
        [string]$Path,
        [string]$Message
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        throw $Message
    }
}

function Assert-Command {
    param(
        [string]$Command,
        [string]$Message
    )
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        throw $Message
    }
}

function Test-PortBusy {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-CmdWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )
    $cmd = "title $Title && cd /d `"$WorkingDirectory`" && $Command"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd
}

try {
    Write-Section (U '\u8bed\u97f3\u7ed8\u56fe\u4e00\u952e\u542f\u52a8')

    Assert-Path -Path (Join-Path $backendDir "pyproject.toml") -Message ((U '\u672a\u627e\u5230\u540e\u7aef\u76ee\u5f55\uff1a') + $backendDir)
    Assert-Path -Path (Join-Path $frontendDir "package.json") -Message ((U '\u672a\u627e\u5230\u524d\u7aef\u76ee\u5f55\uff1a') + $frontendDir)
    Assert-Path -Path (Join-Path $root ".env") -Message (U '\u672a\u627e\u5230 .env\u3002\u8bf7\u5148\u4ece .env.example \u590d\u5236\u5e76\u586b\u5199 ASR/LLM \u914d\u7f6e\u3002')
    Assert-Command -Command "uv" -Message (U '\u672a\u68c0\u6d4b\u5230 uv\u3002\u8bf7\u5148\u5b89\u88c5 uv\uff0c\u6216\u786e\u8ba4 uv \u5df2\u52a0\u5165 PATH\u3002')
    Assert-Command -Command "npm" -Message (U '\u672a\u68c0\u6d4b\u5230 npm\u3002\u8bf7\u5148\u5b89\u88c5 Node.js/npm\uff0c\u6216\u786e\u8ba4 npm \u5df2\u52a0\u5165 PATH\u3002')

    if ($Check) {
        Write-Host (U '[\u901a\u8fc7] \u542f\u52a8\u524d\u68c0\u67e5\u901a\u8fc7\u3002')
        exit 0
    }

    if (Test-PortBusy -Port 8000) {
        Write-Host (U '[\u63d0\u793a] \u540e\u7aef\u7aef\u53e3 8000 \u5df2\u88ab\u5360\u7528\uff0c\u8df3\u8fc7\u540e\u7aef\u542f\u52a8\u3002')
    } else {
        Write-Host (U '[\u542f\u52a8] \u540e\u7aef\u670d\u52a1\uff1ahttp://127.0.0.1:8000')
        Start-CmdWindow -Title (U '\u8bed\u97f3\u7ed8\u56fe \u540e\u7aef 8000') -WorkingDirectory $backendDir -Command "uv sync && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000"
    }

    if (Test-PortBusy -Port 5173) {
        Write-Host (U '[\u63d0\u793a] \u524d\u7aef\u7aef\u53e3 5173 \u5df2\u88ab\u5360\u7528\uff0c\u8df3\u8fc7\u524d\u7aef\u542f\u52a8\u3002')
    } else {
        Write-Host (U '[\u542f\u52a8] \u524d\u7aef\u670d\u52a1\uff1ahttp://127.0.0.1:5173')
        Start-CmdWindow -Title (U '\u8bed\u97f3\u7ed8\u56fe \u524d\u7aef 5173') -WorkingDirectory $frontendDir -Command "npm install && npm run dev -- --port 5173"
    }

    Write-Host ""
    Write-Host (U '[\u63d0\u793a] \u670d\u52a1\u542f\u52a8\u9700\u8981\u51e0\u79d2\u949f\u3002\u5c06\u6253\u5f00\u524d\u7aef\u9875\u9762\uff1a')
    Write-Host "       $frontendUrl"
    Start-Sleep -Seconds 3
    Start-Process $frontendUrl

    Write-Host ""
    Write-Host (U '\u5df2\u53d1\u9001\u542f\u52a8\u547d\u4ee4\u3002\u540e\u7aef\u548c\u524d\u7aef\u65e5\u5fd7\u5206\u522b\u5728\u65b0\u6253\u5f00\u7684\u547d\u4ee4\u884c\u7a97\u53e3\u4e2d\u663e\u793a\u3002')
    Write-Host (U '\u5173\u95ed\u5bf9\u5e94\u547d\u4ee4\u884c\u7a97\u53e3\u5373\u53ef\u505c\u6b62\u670d\u52a1\u3002')
    Write-Host ""
    Read-Host (U '\u6309 Enter \u5173\u95ed\u542f\u52a8\u5668')
    exit 0
} catch {
    Write-Host ""
    Write-Host ((U '[\u9519\u8bef] ') + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
