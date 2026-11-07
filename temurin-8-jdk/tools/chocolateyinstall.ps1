$ErrorActionPreference  = 'Stop'
if ((Get-OSArchitectureWidth 32) -or ($env:chocolateyForceX86 -eq 'true')) { throw "Temurin8 is 64-bit only: Adoptium does not publish a 32-bit Windows build of this release." }
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin8'
  fileType        = 'msi'
  Url64bit        = 'https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u512-b09/OpenJDK8U-jdk_x64_windows_hotspot_8u512b09.msi'
  Checksum64      = '77a730e65149c4cc426209672c7bd1b996ba6423e04c563c381ba083278cf165'
  ChecksumType64  = 'sha256'
  SilentArgs      = $pp
}

if ($parameters.both) { Write-Warning "/both is no longer supported: no 32-bit build is published." }
Install-ChocolateyPackage @packageArgs




