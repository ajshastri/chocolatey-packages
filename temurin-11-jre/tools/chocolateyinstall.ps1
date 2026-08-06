$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin11jre'
  fileType        = 'msi'
  Url             = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.29%2B7/OpenJDK11U-jre_x86-32_windows_hotspot_11.0.29_7.msi'
  Url64bit        = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.32%2B9/OpenJDK11U-jre_x64_windows_hotspot_11.0.32_9.msi'
  Checksum        = 'dec292e1d6e90944d0c4592e3df26d19072025ed34657d67d3456281f7f3026a'
  ChecksumType    = 'sha256'
  Checksum64      = 'df081418748813e681157c616837a605d463c7a9cee631a3b6319ef838c4cc6e'
  ChecksumType64  = 'sha256'
  SilentArgs      = $pp
}

if ($parameters.both){
write-warning "Installing 32bit version"
Install-ChocolateyPackage $packageArgs.packageName $packageArgs.fileType $packageArgs.SilentArgs $packageArgs.url -checksum $packageArgs.checksum -checksumtype $packageArgs.ChecksumType
write-warning "Installing 64bit version"
Install-ChocolateyPackage $packageArgs.packageName $packageArgs.fileType $packageArgs.SilentArgs $packageArgs.Url64bit $packageArgs.Url64bit -checksum $packageArgs.Checksum64 -checksumtype $packageArgs.ChecksumType64
} else {
write-warning "Installing only Get-OSArchitectureWidth"
Install-ChocolateyPackage @packageArgs
}
