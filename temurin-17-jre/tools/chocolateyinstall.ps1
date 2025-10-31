$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin17jre'
  fileType        = 'msi'
  Url             = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.16%2B8/OpenJDK17U-jre_x86-32_windows_hotspot_17.0.16_8.msi'
  Url64bit        = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.17%2B10/OpenJDK17U-jre_x64_windows_hotspot_17.0.17_10.msi'
  Checksum        = '47ac8df108d911103a053880a401fc18302b4b9a098814436716deba86cdfb76'
  ChecksumType    = 'sha256'
  Checksum64      = '23eea3080b9545915b5af64807fd310ee7227688a179b33859530912cca4c1e6'
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
