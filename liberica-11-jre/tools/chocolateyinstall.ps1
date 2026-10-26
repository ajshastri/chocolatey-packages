$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.2+5/bellsoft-jre11.0.33.0.2+5-windows-amd64.msi'
  Checksum64 = 'fb60db8b704d1ba48c6aea4ca21007096f340f466a50be30dd6e6d5304830ea0'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
