$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.20.1+1/bellsoft-jre17.0.20.1+1-windows-amd64-full.msi'
  Checksum64 = 'ae8c1079826e3d7851a57951f19188112c65b6ec5a337e432747892a347ea6ed'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
