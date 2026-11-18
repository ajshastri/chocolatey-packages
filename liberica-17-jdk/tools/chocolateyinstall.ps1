$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.1+5/bellsoft-jdk17.0.21.1+5-windows-amd64.msi'
  Checksum64 = 'f2097e70a3fdd208a4165032c299dac9e67bb4aa7c3cdab218c0dc57e1e48450'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
