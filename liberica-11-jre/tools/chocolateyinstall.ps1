$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.3+7/bellsoft-jre11.0.33.0.3+7-windows-amd64.msi'
  Checksum64 = 'ccd3583efad502423b757cca0eb9b1f8da821e68f66d18c018330d3ea3395c62'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
