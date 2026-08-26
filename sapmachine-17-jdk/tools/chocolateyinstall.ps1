$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.20.1/sapmachine-jdk-17.0.20.1_windows-x64_bin.msi'
  Checksum64     = 'f030f04efb6dfda606a4129e3222fc1a69e15e15080452a5e26d75670961eea3'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
