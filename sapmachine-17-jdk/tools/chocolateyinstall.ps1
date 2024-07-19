$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.12/sapmachine-jdk-17.0.12_windows-x64_bin.msi'
  Checksum64 = 'ce036b86c5d2eac8e6988a0b79c79d6093e71e52d9db18c3f63081c799b9e7d2'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
