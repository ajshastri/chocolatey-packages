$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\mvndaemon"

rm -r "$installDir\maven-mvnd-1.0.1-windows-amd64"
