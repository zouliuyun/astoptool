while getopts ":s:g:i:h:p:d:" optname
do
    case "$optname" in
        "s")
            servername="$OPTARG" #比如feiliu_1
            ;;
        "g")
            game="$OPTARG"
            ;;
        "i")
            wwwIp="$OPTARG"
            ;;
        "h")
            wwwHeader="$OPTARG"
            ;;
        "p")
            wwwPort="$OPTARG"
            ;;
        "d")
            wwwDir="$OPTARG"
            ;;
    esac
done

function exitError()
{
    if [ $? -ne 0 ];then
        echo "ERROR: ${1}"
        exit 1
    fi
}
function download()
{
    filename=${1}
    rm -f ${filename} && wget --header="host:${wwwHeader}" http://${wwwIp}:${wwwPort}/${game}/update/${wwwDir}/${filename}
    exitError "dowload ${filename} failed!"
}
