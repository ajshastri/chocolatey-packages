$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.25/sapmachine-jre-11.0.25_windows-x64_bin.msi'
  Checksum64 = '3328fb6b54a8a48ec3c527eefb9f5157171e4ae2adbd22f2a1e61abf3d7338a3'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
