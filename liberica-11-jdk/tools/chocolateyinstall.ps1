$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.3+7/bellsoft-jdk11.0.33.0.3+7-windows-amd64.msi'
  Checksum64 = '694972e57c4c634db0e9e4b29614053662f74ec8f34cea5033a105be451787f2'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
