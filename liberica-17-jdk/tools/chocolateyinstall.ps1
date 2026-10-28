$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.3+5/bellsoft-jdk17.0.21.0.3+5-windows-amd64.msi'
  Checksum64 = '93ff81ca52cc9206a4e60b65dcafe32362953c5eff0c71434354093b730acd55'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
