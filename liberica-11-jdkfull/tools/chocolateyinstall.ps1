$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.2+5/bellsoft-jdk11.0.33.0.2+5-windows-amd64-full.msi'
  Checksum64 = 'fa2f4d9420fe57da86b00017352db4843e9f02adccbb13e506dd0df8f534b856'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
