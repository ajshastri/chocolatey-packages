$ErrorActionPreference  = 'Stop'
if ((Get-OSArchitectureWidth 32) -or ($env:chocolateyForceX86 -eq 'true')) { throw "Temurin11 is 64-bit only: Adoptium does not publish a 32-bit Windows build of this release." }
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin11'
  fileType        = 'msi'
  Url64bit        = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.32.1%2B1/OpenJDK11U-jdk_x64_windows_hotspot_11.0.32.1_1.msi'
  Checksum64      = '253989adc3097a52f81560e32986d829bdec6b949b4595a3489220f74d801cdb'
  ChecksumType64  = 'sha256'
  SilentArgs      = $pp
}

if ($parameters.both) { Write-Warning "/both is no longer supported: no 32-bit build is published." }
Install-ChocolateyPackage @packageArgs




