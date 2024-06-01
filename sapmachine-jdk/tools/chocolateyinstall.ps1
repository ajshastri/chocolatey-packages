$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.3/sapmachine-jdk-21.0.3_windows-x64_bin.msi'
  Checksum64 = '539d0a6bd6ec7c51ccc0c1b840cba72462f0fa3e8ce99a54d839ee1a6076cb00'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
