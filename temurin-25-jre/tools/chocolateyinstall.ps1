$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName    = 'Temurin25jre'
  Url64bit       = 'https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.3%2B9/OpenJDK25U-jre_x64_windows_hotspot_25.0.3_9.msi'
  Checksum64     = '05975ec0d4df8722b30836af98d795a80f72d4cc37a2451943bd23304d5ac0fb'
  ChecksumType64 = 'sha256'
  fileType       = 'msi'
  SilentArgs     = $pp
}

Install-ChocolateyPackage @packageArgs
