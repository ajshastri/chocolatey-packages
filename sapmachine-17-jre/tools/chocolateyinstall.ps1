$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.13/sapmachine-jre-17.0.13_windows-x64_bin.msi'
  Checksum64 = 'ec1da756d99a13a3c8764b009c57e2500e228a6fa9be7859450618d08d321467'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
