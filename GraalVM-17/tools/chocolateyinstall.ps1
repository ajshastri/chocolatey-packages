$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\GraalVM"
$version = "17.0.9+9.1"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url64bit = 'https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-17.0.9/graalvm-community-jdk-17.0.9_windows-x64_bin.zip'
    Checksum64 = '285e045bfc0b87d2b61958fea97444c3c6c7e68fba3fdbbe146622328b52ec38'
    ChecksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyEnvironmentVariable 'JAVA_HOME' $targetDir\graalvm-community-openjdk-$version 'Machine'
# The full path instead of the %JAVA_HOME% is needed so it can be removed with the Chocolatey Uninstall
Install-ChocolateyPath $targetDir\graalvm-community-openjdk-$version\bin -PathType 'Machine'
