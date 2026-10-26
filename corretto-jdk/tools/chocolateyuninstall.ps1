$ErrorActionPreference = 'Stop'
# Side by side: uninstall only the build of this package's major version. Other
# majors of the same vendor stay installed. tools\.skipAutoUninstall turns off
# Chocolatey's automatic uninstaller, which could remove another major's build.
$softwareName = 'Amazon Corretto (x64)'
$major        = '25'
[array]$keys = Get-UninstallRegistryKey -SoftwareName $softwareName |
  Where-Object { $_.DisplayVersion -like "$major.*" }
if ($keys.Count -eq 0) {
  Write-Warning "$softwareName $major is not installed; nothing to uninstall."
  return
}
foreach ($key in $keys) {
  $packageArgs = @{
    PackageName    = $env:ChocolateyPackageName
    FileType       = 'msi'
    SilentArgs     = "$($key.PSChildName) /qn /norestart"
    File           = ''
    ValidExitCodes = @(0, 1605, 1614, 1641, 3010)
  }
  Uninstall-ChocolateyPackage @packageArgs
}
