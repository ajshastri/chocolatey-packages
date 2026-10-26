$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.13.0.3/sapmachine-jdk-21.0.13.0.3_windows-x64_bin.msi'
  Checksum64     = '75bde21fca14b0d97d0ae7858b6228d871151880cb865912539fe40f86126ad1'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
