$ErrorActionPreference = 'Stop'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$url64      = 'https://cdn.azul.com/zulu/bin/zulu8.76.0.17-ca-fx-jdk8.0.402-win_x64.msi'

$packageArgs = @{
  packageName   = $env:ChocolateyPackageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url           = $url
  url64bit      = $url64

  softwareName  = 'Zulu 8*'
  checksum64    = '24d5cf50ca85fdfcbfe055c668848535dd9781f6793bccbc8ef09d26306d9ef5'
  checksumType64= 'sha256'

  silentArgs    = "ADDLOCAL=ZuluInstallation,FeatureEnvironment /qn /norestart"
  validExitCodes= @(0)
}

Install-ChocolateyPackage @packageArgs
