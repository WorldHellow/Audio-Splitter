#!/bin/sh

#GOOGLE_APPLICATION_CREDENTIALS="/home/atahir/work/speech_api/My-Project-50260-86c2e205a557.json"
#export GOOGLE_APPLICATION_CREDENTIALS
#echo $GOOGLE_APPLICATION_CREDENTIALS	

#echo $1

#base64 $1 -w 0 > base64-audio

#{ <sync-request.json.p1 head -c -1 && cat base64-audio && cat sync-request.json.p2; } > sync-request.json


#curl -s -H "Content-Type: application/json" \
#    -H "Authorization: Bearer "$(gcloud auth application-default print-access-token) \
#    https://speech.googleapis.com/v1/speech:recognize \
#    -d @sync-request.json > result.txt

#f2=$(echo $1 | sed 's/.wav//g');
#cat result.txt | grep transcript | sed 's/.* \"//g' | sed 's/\",//g' | tr '\n' ' '
#cat result.txt | grep transcript | sed 's/.* \"//g' | sed 's/\",//g' | tr '\n' ' ' > ${f2}.txt


  

