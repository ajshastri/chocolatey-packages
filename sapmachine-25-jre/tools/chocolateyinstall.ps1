$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-25.0.5.0.3/sapmachine-jre-25.0.5.0.3_windows-x64_bin.msi'
  Checksum64     = '6dfc7b67494a979be1163d3f3996ac8f975c935c2faf017887eaf26c8b9dfbc3'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
