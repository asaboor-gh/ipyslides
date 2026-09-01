param(
    [switch]$DryRun,      # Simulate everything without changing
    [string]$GitBranch = "main"
)

$ErrorActionPreference = "Stop"

$versionFile = "ipyslides/__version__.py"

if ($DryRun) {
    Write-Host "`n=== DRY RUN: Nothing will be changed ===`n" -ForegroundColor Green
}

# Read current version from __version__.py
$currentVersionLine = Get-Content $versionFile | Where-Object { $_ -match '__version__' }
if (-not $currentVersionLine) {
    Write-Error "Could not find __version__ in $versionFile"
    exit 1
}

$match = [regex]::Match($currentVersionLine, '__version__\s*=\s*["''](.+)["'']')
if (-not $match.Success) {
    Write-Error "Failed to parse version from line: $currentVersionLine"
    exit 1
}

$currentVersion = $match.Groups[1].Value
Write-Host "Current version: $currentVersion"

# Suggest new version by incrementing patch
$parts = $currentVersion.Split('.')
if ($parts.Count -lt 3) {
    Write-Error "Current version '$currentVersion' is not in X.Y.Z format"
    exit 1
}

$defaultPatch = [int]$parts[-1] + 1
$defaultVersion = "$($parts[0]).$($parts[1]).$defaultPatch"

$newVersion = Read-Host "Enter new version (press Enter to use $defaultVersion)"
if (-not $newVersion) {
    $newVersion = $defaultVersion
} else {
    $newVersion = $newVersion.Trim()
}

Write-Host "Bumping version to: $newVersion"

if (-not $newVersion -match '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format: $newVersion. Expected format: X.Y.Z"
    exit 1
}

# Update version in __version__.py
if (-not $DryRun) {
    (Get-Content $versionFile) -replace '__version__\s*=\s*["''].+["'']', "__version__ = `"$newVersion`"" |
        Set-Content $versionFile
} else {
    Write-Host "Would update $versionFile to version $newVersion"
}

# Clean old builds
foreach ($dir in @("dist", "build")) {
    if (Test-Path $dir) {
        if (-not $DryRun) {
            Remove-Item $dir -Recurse -Force
        } else {
            Write-Host "Would remove $dir"
        }
    }
}

Get-ChildItem -Recurse -Directory -Filter "*.egg-info" | ForEach-Object {
    if (-not $DryRun) {
        Remove-Item $_.FullName -Recurse -Force
    } else {
        Write-Host "Would remove $($_.FullName)"
    }
}

# Build package with uv
if (-not $DryRun) {
    uv build --wheel --sdist
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nBuild failed with exit code $LASTEXITCODE"
        exit 1
    }
} else {
    Write-Host "Would run uv build --wheel --sdist"
}

# Upload to PyPI with uv
$uploadSucceeded = $false
if (-not $DryRun) {
    uv publish dist/*
    if ($LASTEXITCODE -eq 0) {
        $uploadSucceeded = $true
    } else {
        Write-Host "`nPyPI upload failed with exit code $LASTEXITCODE"
        exit 1
    }
} else {
    Write-Host "Would upload with uv publish dist/*"
    $uploadSucceeded = $true
}

# Git commit & optional tag only if upload succeeded
if ($uploadSucceeded) {
    $defaultCommitMsg = "Release v$newVersion"
    $commitMsg = Read-Host "Enter commit message (press Enter to use '$defaultCommitMsg')"
    if (-not $commitMsg) {
        $commitMsg = $defaultCommitMsg
    }

    if (-not $DryRun) {
        git add .
        git commit -m "$commitMsg"

        # Optional tag
        $tagAnswer = Read-Host "Tag release v$newVersion ? (y/N, press Enter to skip)"
        if ($tagAnswer -match '^(?i)y(?:es)?$') {
            git tag "v$newVersion"
            git push origin "v$newVersion"
            Write-Host "Tagged release v$newVersion"
        }

        git push origin $GitBranch
    } else {
        Write-Host "Would add all changes and commit with message: '$commitMsg'"
        Write-Host "Would ask to tag release v$newVersion"
        Write-Host "Would push branch $GitBranch"
    }
}

if ($DryRun) {
    Write-Host "`n=== DRY RUN COMPLETE: No changes were made ===" -ForegroundColor Green
} else {
    Write-Host "`nPublish complete!"
}