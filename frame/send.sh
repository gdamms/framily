FILE_DIR=$(dirname "$0")
SSH_ENTRY=framily@10.42.0.1

scp -r $FILE_DIR $SSH_ENTRY:/home/framily/
