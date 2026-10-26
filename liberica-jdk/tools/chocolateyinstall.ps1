$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.0.3+5/bellsoft-jdk25.0.5.0.3+5-windows-amd64.msi'
  Checksum64 = 'f86bdc0d45b9d14ae2baa836950ba4b01c6800b30bf9ffa62f7f4fd1603f53ee'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
