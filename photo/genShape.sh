jarf=$(pwd)/shapeGen/generateStimuli.jar
natdir=$(pwd)/shapeGen/native/macos
stimdir=$(pwd)/stim/

java -Djava.library.path=$natdir -jar $jarf $stimdir 1 1 20 True True True SHADE 1 1 1 1 0.3 0.3 0.3

blender --background --python testMakePhoto.py