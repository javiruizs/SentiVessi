if ( $args.Count -ne 3 )
{
    Write-Output "Username and password is needed."
    Write-Output ".\preview_downloader.ps1 <username> <password> <input_dir>"
    exit
}

$username=$args[0]
$password=$args[1]
$dir=$args[2]

$old_dir=$pwd

cd $dir

conda activate sentinel

$command="sentinelsat -u $username -p $password --quicklook"

$products=(Get-ChildItem -Filter "*.zip")

if ( $products -eq $null )
{
    Write-Output "No ZIP files found in $pwd."
    exit
}

foreach($product in $products)
{
    $command="$($command) --name $($product.BaseName)"
}

Invoke-Expression $command

cd $old_dir
