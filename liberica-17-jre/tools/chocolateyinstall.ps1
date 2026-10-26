$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.2+5/bellsoft-jre17.0.21.0.2+5-windows-amd64.msi'
  Checksum64 = '9861f15fb5f4fe974b83039e4d2c37fe666c322460dd4dbbfe60dd5472ad746b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
