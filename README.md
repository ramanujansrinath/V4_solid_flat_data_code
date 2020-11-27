# Early Emergence of Solid Shape Coding in Natural and Deep Network Vision
This is a repository for public access of data and matlab code to generate the figures from Srinath et al, 2020. For any further requests or clarifications, please contact the corresponding author.

## Electrophysiology
The "ep" folder contains all the data collected during the single electrode electrophysiology recordings. It contains data from 169 neurons in V4 studied with 80-800 stimuli each. For each stimulus, (1) the "id" identifies the neuron, generation, lineage, and stimulus number, (2) "col" refers to the color, (3) "tex" contains information about the object surface (SPECULAR=polished, SHADE=matte, TWOD=planar), (4) "spec" contains the XML specifications of each stimulus, and (5) "resp" contains the trial-averaged response of the neuron for that stimulus. The script "ep_data_img" loads the data, and regenerates the image for a given stimulus. It uses a custom java package to do so.

## Photorealistic Stimuli Generation
The "photo" folder contains the script to generate random stimuli with a custom made Java package and then create photorealistic images used in the paper to study whether V4 neurons encode solid shapes consistently across 3D cues like reflectivity and refraction. This requires Java 1.8 and Blender 2.79. Execute genShape.sh to create an example. This will take several minites. You could reduce the sampling rate and/or image resolution in V4Cycles_latest.py (Line 952-953 and 979) to make it faster. A set of full resolution images are in examples.png.

![exmaples.png](https://github.com/ramanujansrinath/V4_solid_flat_data_code/blob/master/photo/examples_small.png)

## Shape Analysis
(Coming soon...)

## Two-photon Imaging
(Coming soon...)

## Deep Convolutional Network Analysis
(Coming soon...)
