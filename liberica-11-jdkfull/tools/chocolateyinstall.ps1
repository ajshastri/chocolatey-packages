$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.32.1+1/bellsoft-jdk11.0.32.1+1-windows-amd64-full.msi'
  Checksum64 = 'e8885ea927596a61184f261ffc645619a708bec010ff6e4166c281e636e7c424'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
