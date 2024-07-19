$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.24/sapmachine-jdk-11.0.24_windows-x64_bin.msi'
  Checksum64 = 'f7774e7879c19683fcab9def54c6c9780ad6d50a780d4ec95663b3b5ca49a904'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
