$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.21.0.3/sapmachine-jre-17.0.21.0.3_windows-x64_bin.msi'
  Checksum64     = 'd4414ad64bd5c82be828fb6df7404c1e76ac7bf3dc5ee355bcb71ada36a66b9d'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
