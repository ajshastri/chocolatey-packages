$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.22/sapmachine-jre-11.0.22_windows-x64_bin.msi'
  Checksum64 = '7dd9f45a109df0073d2579daac767cc8044240cbdc2303fd6665f44bb8976989'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
