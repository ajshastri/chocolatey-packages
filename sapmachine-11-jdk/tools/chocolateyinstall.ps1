$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.25/sapmachine-jdk-11.0.25_windows-x64_bin.msi'
  Checksum64 = '35c9e4f580b8869700b75c57cac8f98b3c61693cbd261d4afeab293ab95eeaa2'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
