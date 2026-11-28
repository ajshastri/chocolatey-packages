$ErrorActionPreference  = 'Stop'
if ((Get-OSArchitectureWidth 32) -or ($env:chocolateyForceX86 -eq 'true')) { throw "Temurin11jre is 64-bit only: Adoptium does not publish a 32-bit Windows build of this release." }
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin11jre'
  fileType        = 'msi'
  Url64bit        = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.33.1%2B1/OpenJDK11U-jre_x64_windows_hotspot_11.0.33.1_1.msi'
  Checksum64      = 'e2b1104ddacaaf3482482ca3b7a52729b89cd51d074eb35173daf8c1133b66c5'
  ChecksumType64  = 'sha256'
  SilentArgs      = $pp
}

if ($parameters.both) { Write-Warning "/both is no longer supported: no 32-bit build is published." }
Install-ChocolateyPackage @packageArgs




