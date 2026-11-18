$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.1+5/bellsoft-jdk11.0.33.1+5-windows-amd64-full.msi'
  Checksum64 = '6c21ee06869101e90400dcf3d1cfe320227f4c7e6294aed7dc44c098f67e54ed'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
