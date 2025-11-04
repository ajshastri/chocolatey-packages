$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName    = 'Temurin25'
  Url64bit       = 'https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.1%2B8/OpenJDK25U-jdk_x64_windows_hotspot_25.0.1_8.msi'
  Checksum64     = 'c49e19ba5b47bf119402b1e0a0a71ce5b19ddd9e4ac3e038ea99fe648bd0b3f9'
  ChecksumType64 = 'sha256'
  fileType       = 'msi'
  SilentArgs     = $pp
}

Install-ChocolateyPackage @packageArgs
