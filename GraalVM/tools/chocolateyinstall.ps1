$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\GraalVM"
$graalvmDir = "graalvm-community-25.5.5.0.3+1.1"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url64bit = 'https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.5.5.0.3/graalvm-community-jdk-25i5-25.0.5.0.3_windows-x64_bin.zip'
    Checksum64 = 'b02c3b162129fa8cbfa7ebd0fcc1ae6eba2fc736bf3bef8e40e5ace3e9d9a0d6'
    ChecksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyEnvironmentVariable 'JAVA_HOME' "$targetDir\$graalvmDir" 'Machine'
# The full path instead of the %JAVA_HOME% is needed so it can be removed with the Chocolatey Uninstall
Install-ChocolateyPath "$targetDir\$graalvmDir\bin" -PathType 'Machine'
