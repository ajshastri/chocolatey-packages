$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin17jre'
  fileType        = 'msi'
  Url             = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.17%2B10/OpenJDK17U-jre_x86-32_windows_hotspot_17.0.17_10.msi'
  Url64bit        = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.20%2B8/OpenJDK17U-jre_x64_windows_hotspot_17.0.20_8.msi'
  Checksum        = '7aa6462a0d258f21d1bf324a80a2eb5ab8fa7707fd520b875f5c129d45c3ac92'
  ChecksumType    = 'sha256'
  Checksum64      = '45ca8db42fb8bbfbf35b68121cf74e1f9fe36ba982b59d38f0da7802902fbace'
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
