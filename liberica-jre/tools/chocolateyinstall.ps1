$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/bellsoft-jre21.0.13.0.2+5-windows-amd64.msi'
  Checksum64 = '72d996c9189462d71c6ec1d9cab854f0e2c33e0c8ddccb4c1c0dabc4b84fe321'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
