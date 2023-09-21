$ErrorActionPreference = 'Stop'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$url64      = 'https://cdn.azul.com/zulu/bin/zulu21.28.85-ca-fx-jdk21.0.0-win_x64.msi'

$packageArgs = @{
  packageName   = $env:ChocolateyPackageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url           = $url
  url64bit      = $url64

  softwareName  = 'Zulu 21*'
  checksum64    = '27d1b299c445a14483520bf8854c8a4081b6498af22bbe2acfa4dfb150128481'
  checksumType64= 'sha256'

  silentArgs    = "ADDLOCAL=ZuluInstallation,FeatureEnvironment /qn /norestart"
  validExitCodes= @(0)
}

Install-ChocolateyPackage @packageArgs
