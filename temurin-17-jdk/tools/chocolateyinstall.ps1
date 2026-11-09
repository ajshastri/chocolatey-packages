$ErrorActionPreference  = 'Stop'
if ((Get-OSArchitectureWidth 32) -or ($env:chocolateyForceX86 -eq 'true')) { throw "Temurin17 is 64-bit only: Adoptium does not publish a 32-bit Windows build of this release." }
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin17'
  fileType        = 'msi'
  Url64bit        = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/OpenJDK17U-jdk_x64_windows_hotspot_17.0.21_9.msi'
  Checksum64      = '9f06b736ef2bd07aaf82f1bd575dc92108b442b97f5d4308eb3816613c086977'
  ChecksumType64  = 'sha256'
  SilentArgs      = $pp
}

if ($parameters.both) { Write-Warning "/both is no longer supported: no 32-bit build is published." }
Install-ChocolateyPackage @packageArgs




