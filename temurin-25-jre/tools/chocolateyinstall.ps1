$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName    = 'Temurin25jre'
  Url64bit       = 'https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.4%2B7/OpenJDK25U-jre_x64_windows_hotspot_25.0.4_7.msi'
  Checksum64     = 'a0c56fbe62dd18a7da032c1e41fd1da027530ebd472e61b5ae64581ebdcfebc8'
  ChecksumType64 = 'sha256'
  fileType       = 'msi'
  SilentArgs     = $pp
}

Install-ChocolateyPackage @packageArgs
