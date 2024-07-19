$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.4/sapmachine-jre-21.0.4_windows-x64_bin.msi'
  Checksum64 = '1d37dc224bc1c83892cd3cfb3825b3f48ab717862ac5bc4bdcc80e46d4fb1c01'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
