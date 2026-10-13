$ErrorActionPreference  = 'Stop'
if ((Get-OSArchitectureWidth 32) -or ($env:chocolateyForceX86 -eq 'true')) { throw "Temurin11jre is 64-bit only: Adoptium does not publish a 32-bit Windows build of this release." }
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin11jre'
  fileType        = 'msi'
  Url64bit        = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.32.1%2B1/OpenJDK11U-jre_x64_windows_hotspot_11.0.32.1_1.msi'
  Checksum64      = '2ee24ab2946b0454463bb38f5d9b2d7e4d2620af7f4fb46df6f313f32635ccdd'
  ChecksumType64  = 'sha256'
  SilentArgs      = $pp
}

if ($parameters.both) { Write-Warning "/both is no longer supported: no 32-bit build is published." }
Install-ChocolateyPackage @packageArgs




