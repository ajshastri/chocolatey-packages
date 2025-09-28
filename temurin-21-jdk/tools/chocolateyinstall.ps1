$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName    = 'Temurin21'
  Url64bit       = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.8%2B9/OpenJDK21U-jdk_x64_windows_hotspot_21.0.8_9.msi'
  Checksum64     = 'd82030e8689b19efedfbce50ce38351ca81b302c06936584c6a27bda18339df8'
  ChecksumType64 = 'sha256'
  fileType       = 'msi'
  SilentArgs     = $pp
}

Install-ChocolateyPackage @packageArgs
