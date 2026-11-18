$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.1+5/bellsoft-jre25.0.5.1+5-windows-amd64-full.msi'
  Checksum64 = '36cd3bfb128b8ec0b647862454af2218df0ac2587d5e3637acf0a747f6c99998'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
