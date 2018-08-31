#!/bin/bash

FILE_PATH=/data/jar/nohup.out
BACK_PATH=/data/backlog/
DATETIME=`date "+%Y-%m-%d"`

if [ ! -e ${BACK_PATH} -o ! -d ${BACK_PATH} ]; then
  mkdir -p ${BACK_PATH}
fi
   
echo "----------------- 正在切割 ${FILE_PATH} 文件 ------------------------"
cat ${FILE_PATH} >> ${BACK_PATH}nohup-${DATETIME}.out
echo '' > ${FILE_PATH}
echo "---------------- ${FILE_PATH} 文件切割完毕 ----------------------"

exit $?