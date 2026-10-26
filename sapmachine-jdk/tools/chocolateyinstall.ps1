$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-25.0.5.0.3/sapmachine-jdk-25.0.5.0.3_windows-x64_bin.msi'
  Checksum64     = 'adb0d58f0c3919ba713db65cec827f5ef537b14665f59d492b0d8f34d8517f1b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
