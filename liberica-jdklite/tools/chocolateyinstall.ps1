$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.1+5/bellsoft-jdk25.0.5.1+5-windows-amd64-lite.msi'
  Checksum64 = '2a606ef9cb3c0794c66dc85f62f3320796e957aa97717c8e8e868ab646cbe60f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
