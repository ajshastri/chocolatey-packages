$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.3/sapmachine-jre-21.0.3_windows-x64_bin.msi'
  Checksum64 = '2f8f67851d7f343fed84ada7e589d7856fd5f7b6c087bad4380f84141998256f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
