$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.32.1+1/bellsoft-jdk11.0.32.1+1-windows-amd64.msi'
  Checksum64 = '876160940c67bf1e2803511141501766993b3ea50948707e19434f70fa04a737'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
