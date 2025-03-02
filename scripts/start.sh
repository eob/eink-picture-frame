#!/bin/bash

pid=$(lsof -i :80| awk '/python/ { pid=$2 } END { print pid }')
currentDir=$(pwd)


currentFolder=${PWD##*/} 


# do a sudo check!
if [ "$EUID" -ne 0 ]; then
  echo -e "\n[ERROR]: The PiInk start script requires root privileges. Please run it with sudo.\n"
  exit 1
fi

if [ "$currentFolder" == "scripts" ]; then
  cd ..
  currentDir=$(pwd)
fi


source env/bin/activate

echo "currentDir: $currentDir"
echo "currentFolder: $currentFolder"
echo "python is at: $(which python)"
echo "python_path is: $PYTHONPATH"

if [[ -z $pid ]]; then
  echo "No process found using port 80!"
else
  echo "Found PID using port 80: $pid."
  echo "Killing process $pid..."
  if sudo kill -9 "$pid" >/dev/null 2>&1; then
    echo "Process killed!"
  else
    echo "Failed to kill process $pid."
  fi
fi

echo "starting PiInk frame webserver!"

# We need to use the right python here so that  the sudo command doesn't use the wrong python outside of the venv
sudo $(which python) $currentDir/src/webserver.py
