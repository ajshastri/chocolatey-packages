$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/bellsoft-jdk21.0.13.0.2+5-windows-amd64-full.msi'
  Checksum64 = '138af8f85fc1153170c067045a10c8d5457a4324d52e0dd413fddb846a2f2b8f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
