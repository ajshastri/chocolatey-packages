$ErrorActionPreference = 'Stop';
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://dn3.freedownloadmanager.org/6/latest/fdm_x86_setup.exe'
$url64      = 'https://dn3.freedownloadmanager.org/6/latest/fdm_x64_setup.exe'

$packageArgs = @{
  packageName   = 'FreeDownloadManager'
  unzipLocation = $toolsDir
  fileType      = 'EXE'
  url           = $url
  url64bit      = $url64
  softwareName  = 'FreeDownloadManager*'
  checksum      = 'aca9718dc2d77224dcf9f8e530162d51150865d49e5a2b1b7da1bee515dc2eed'
  checksumType  = 'sha256'
  checksum64    = '0c4950be3e7d765fad2a533a75ee0b4a6541a35220624aadbee3d6ac5434cd36'
  checksumType64= 'sha256'
  
  validExitCodes= @(0, 3010, 1641)
  silentArgs   = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-'
}

Install-ChocolateyPackage @packageArgs










    








