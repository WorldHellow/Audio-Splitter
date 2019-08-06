#!/bin/sh

for f in express_tothepoint_2.mp3; do
	echo $f;
	f2=$(echo $(basename $f) | sed 's/.wav//g' | sed 's/.mp3//g');
	sox $f -r 16000 -c 1 -b 16 ${f2}.wav
done

#exit

for f in express_tothepoint_2.wav; do
	file1=${f};
	echo "splitting file";
	echo $file1;
	f2=$(echo $file1 | sed 's/.wav//g');
	mkdir -p $f2;

	cd wav_splitter;
	mkdir -p tp data;
	cp ../$file1 data/demo.wav;


	python cmu-segment.py  -t data -a . -o data -n demo --no-clean-up data/demo.wav;
	python wav-splitter.py;
	chmod u=rwx wav-splitting-script.sh;
	./wav-splitting-script.sh;
	mv *.wav ../$f2/.;

	cd ..;
done;

for f in express_tothepoint_2/*.wav; do
	./recognize.sh $f
done;



