$ErrorActionPreference  = 'Stop'
 if(!$PSScriptRoot){ $PSScriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
. "$PSScriptRoot\helper.ps1"

# Get Package Parameters
$parameters = (Get-PackageParameters); $pp = ( Test-PackageParamaters $parameters ).ToString() -replace('""|="True"','') -replace(";", ' ') -replace("==", '=')

$packageArgs = @{
  PackageName     = 'Temurin11'
  fileType        = 'msi'
  Url             = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.22%2B7/OpenJDK11U-jdk_x86-32_windows_hotspot_11.0.22_7.msi'
  Url64bit        = 'https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.23%2B9/OpenJDK11U-jdk_x64_windows_hotspot_11.0.23_9.msi'
  Checksum        = 'd881a1c8fed4483133496fdd64e4531e5e913ef7e8d67eb3a468a333150ead6e'
  ChecksumType    = 'sha256'
  Checksum64      = 'cacbe31a3921e52f4ff6d031d6f37d8a7c58f20a136fccf1754565f8aa403ed8'
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
