# -*- coding: utf-8 -*-
"""Complete Code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jw-PIu03Gg9wEBpL0uvAbYb2j7_U0uMr
"""

## Search and Downlaod videos for detecting target actions

!pip install pytube

from pytube import YouTube

# Commented out IPython magic to ensure Python compatibility.
from google.colab import drive
drive.mount('/content/gdrive')
# %cd /

save_path = "content/gdrive/My Drive/CSCE636_Deep_Learning/Action Detection"

#Search for videos
links=[]

from youtubesearchpython import VideosSearch

search = VideosSearch('people clap',limit=20)

num_videosearch=8 

for i in range(num_videosearch):
  for link in search.result()['result']:
    links.append(link['link'])
  search.next()

search = VideosSearch('hand clapping people',limit=20)

num_videosearch=8 

for i in range(num_videosearch):
  for link in search.result()['result']:
    links.append(link['link'])
  search.next()

search = VideosSearch('hand clapp people',limit=20)

num_videosearch=8 

for i in range(num_videosearch):
  for link in search.result()['result']:
    links.append(link['link'])
  search.next()

len(links)

links=list(set(links))
len(links)

#Download Videos
import time
import os

save_links=[]

for link in links:
  yt = YouTube(link) 
  video=yt.streams.get_highest_resolution()
  if (yt.length<=900):
    save_links.append(link)
    video.download(save_path)
    os.rename(save_path+'/'+video.default_filename, save_path+'/'+yt.video_id+'.mp4')
    print(yt.watch_url)
    print(yt.streams.get_highest_resolution())
  print ("Start : %s" % time.ctime())
  time.sleep(60)
  print ("End : %s" % time.ctime())



##Training and test the Model

# install the package for videogenerator used in training
!pip install keras-video-generators

# Commented out IPython magic to ensure Python compatibility.
#get access from google drive
from google.colab import drive
drive.mount('/content/gdrive')
# %cd /

#set the directory for training data
train_dir='/content/gdrive/My Drive/CSCE636_Deep_Learning/Model/Custom_Dataset/Custom_Dataset4/{classname}/*'

import keras
from keras_video import VideoFrameGenerator

#global parameters for training
size = (224, 224)    # the input image size is (224,224,4)
channels = 3
N_frames = 8       # each video is cut into 8 frames
Batch_size = 8
classes=2          #two classes: one for target action, the other is for other actions
train_validate_split=0.3  #30% data used for validation

# for data augmentation
from keras_preprocessing.image import ImageDataGenerator
data_aug = ImageDataGenerator(
    zoom_range=.1,
    horizontal_flip=True,
    rotation_range=8,
    width_shift_range=.2,
    height_shift_range=.2)

#set the videogenerator for the training process
train_gen = VideoFrameGenerator( 
    glob_pattern=train_dir,
    nb_frames=N_frames,
    split_val=train_validate_split, 
    shuffle=True,     #shuffle the sample for training
    batch_size=Batch_size,
    target_shape=size,
    nb_channel=channels,
    transformation=data_aug,  #apply data augmentaion for the generated frames
    use_frame_cache=False)

#set the videogenerator for the validation process
validation_gen= train_gen.get_validation_generator()

#show some sample frames generated from videogenerator
from keras_video import utils as ku
ku.show_sample(train_gen, random=True)



# fine tuning MobileNetV2
def build_mobilenet(shape=(224, 224, 3), nbout=2):
    model = keras.applications.MobileNetV2(
        include_top=False,
        input_shape=shape,
        weights='imagenet')
    # Keep 9 layers to train
    trainable = 9
    for layer in model.layers[:-trainable]:
        layer.trainable = False
    for layer in model.layers[-trainable:]:
        layer.trainable = True
    output = keras.layers.GlobalMaxPool2D()
    return keras.Sequential([model, output])

# the sturctue of the Neural Network 
from keras.layers import TimeDistributed, GRU, LSTM, Dense, Dropout
def action_model(shape=(8, 224, 224, 3), nbout=2):
    # create the convnet with (224, 224, 3) input shape
    convnet = build_mobilenet(shape[1:])
    
    # create the final model
    model = keras.Sequential()
    # add the convnet with (8, 224, 224, 3) shape
    model.add(TimeDistributed(convnet, input_shape=shape))
    # add GRU
    model.add(GRU(64))
    # add the classification layers
    model.add(Dense(1024, activation='relu'))
    model.add(Dropout(.5))
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(.5))
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(nbout, activation='softmax'))
    return model

from keras import optimizers
Inshape=(N_frames,) + size + (channels,) #(8, 224, 224, 3)
model = action_model(Inshape, classes)
optimizer = optimizers.Adam(0.001)     #Use Adam as optimizers, set learning rate as 0.001
model.compile(
    optimizer,
    'binary_crossentropy',        #use binary crossentropy as the loss function
    metrics=['acc',keras.metrics.FalsePositives(),keras.metrics.FalseNegatives()]
)



#training the model
epochs=30                                              # set the epochs=30 since longer training causes over-fitting
callbacks = [            
    keras.callbacks.ModelCheckpoint(
        '/content/gdrive/My Drive/CSCE636_Deep_Learning/Model/chkp/weight_custom.hdf5',   #save the weights with best performance
        verbose=1,
        save_weights_only=True,
        save_best_only=True,),
]
#train the model and see the performance on training and validation set
history=model.fit_generator(
    train_gen,
    validation_data=validation_gen,       
    verbose=1,
    epochs=epochs,
    callbacks=callbacks
)
model.save('/content/gdrive/My Drive/CSCE636_Deep_Learning/Model/chkp/model_custom.h5')       #save the trained model

#plot the results
import matplotlib.pyplot as plt
acc = history.history['acc']
val_acc = history.history['val_acc']
loss = history.history['loss']
val_loss =history.history['val_loss']

epochs=range(1,len(acc)+1)

plt.plot(epochs, acc, 'r', label='Training acc')
plt.plot(epochs, val_acc, 'b', label='Validation acc')
plt.title('Training and validation accuracy')
plt.legend()

plt.figure()

plt.plot(epochs, loss, 'r', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.legend()

plt.show()



## Apply to video to find the video clips which contain the target action

##Trim the video to video clips

# install the package moviepy 
!pip install moviepy

# Commented out IPython magic to ensure Python compatibility.
# get access from the google drive
from google.colab import drive
drive.mount('/content/gdrive')
# %cd /

# Import everything needed to edit video clips
from moviepy.editor import *

#set the video's original directory and the directory for the video clips
import os
import numpy as np
import math

base_dir='content/gdrive/My Drive/CSCE636_Deep_Learning/Action Detection_1'   #video's original directory
video_list=os.listdir(base_dir)
dst_dir='content/gdrive/My Drive/CSCE636_Deep_Learning/Action_Detect_Clips/Test1/Test1'  #two recursive test folders are needed because the videogenerator I used requires them
os.mkdir(dst_dir)

# clip video to video clips every 6 seconds  
i=0
interval=6
for video in video_list:
  video_src_dir=os.path.join(base_dir,video)
  myclip = VideoFileClip(video_src_dir,audio=False)
  i +=1
  for time in np.arange(myclip.duration // interval):
    video_dst=video.split(".")[0]+"+"+str(time*interval)+"+"+str(time*interval+2)+'.mp4'    #rename the video clips as videoId+start time+end time
    video_dst_dir=os.path.join(dst_dir,video_dst)
    output_clip=myclip.subclip(t_start=time*interval, t_end=time*interval+2)
    output_clip.write_videofile(video_dst_dir) 
    print('Clipping:',i,' Duration:',myclip.duration)
    print('Clipping time:',time*interval,time*interval+2)

## Predict on the videos

#install the package for the video generators
!pip install keras-video-generators

# Commented out IPython magic to ensure Python compatibility.
#get access from google drive
from google.colab import drive
drive.mount('/content/gdrive')
# %cd /

#set the directory of training data and test data
train_dir='/content/gdrive/My Drive/CSCE636_Deep_Learning/Model/Custom_Dataset/Custom_Dataset4/{classname}/*'

testset_name='Test1'
test_dir='content/gdrive/My Drive/CSCE636_Deep_Learning/Action_Detect_Clips/'+testset_name+'/{classname}/*'

#import the model I trained
import keras 
model_name='model_custom4_1'
model = keras.models.load_model('content/gdrive/My Drive/CSCE636_Deep_Learning/Model/chkp/'+model_name+'.h5')

#keep the global parameters as the training model
size = (224, 224)
channels = 3
N_frames = 8
Batch_size = 8
classes=2
train_validate_split=0.3

# from training data generator to get labels
from keras_video import VideoFrameGenerator
from keras_preprocessing.image import ImageDataGenerator

data_aug = ImageDataGenerator(
    zoom_range=.1,
    horizontal_flip=True,
    rotation_range=8,
    width_shift_range=.2,
    height_shift_range=.2)

train_gen = VideoFrameGenerator( 
    glob_pattern=train_dir,
    nb_frames=N_frames,
    split_val=train_validate_split, 
    shuffle=True,
    batch_size=Batch_size,
    target_shape=size,
    nb_channel=channels,
    transformation=data_aug,
    use_frame_cache=False)

#set test data generator for testing
test_gen = VideoFrameGenerator(
    glob_pattern=test_dir,
    nb_frames=N_frames, 
    batch_size=1,
    target_shape=size,
    nb_channel=channels,
    shuffle=False,
    use_frame_cache=False)

#show the number of video clips for testing
len(test_gen.files)

#prediction using test data
predict = model.predict_generator(test_gen)

#show the prediction results
preds_cls_idx = predict.argmax(axis=-1)
print(preds_cls_idx)

#show the prediction files' dimension
predict.shape

#show the classes order 
train_gen.classes

#make a dictionary for the labels and classes generated by model
class_names = sorted(train_gen.classes) # Sorting them
name_id_map = dict(zip(class_names, range(len(class_names))))

#show the dictionary of lables
name_id_map

#show the testing data
from pandas import DataFrame
FileName=DataFrame(test_gen.files, columns=['FileName'])
FileName

#show the prediction results
ClassName=DataFrame(preds_cls_idx, columns=['ClassName'])
ClassName.columns

#combine the testing data with their prediciton results
import pandas as pd

output=pd.concat([FileName, ClassName], axis=1)
output

#keep the target action for output
output_json=output[output.ClassName==0]
output_json.FileName

## Write to json files

# Commented out IPython magic to ensure Python compatibility.
# get access from google drive
from google.colab import drive
drive.mount('/content/gdrive')
# %cd /

# set the directory for the output json file
import os
json_dir='/content/gdrive/My Drive/CSCE636_Deep_Learning/Output/Submission2'
try: 
  os.mkdir(json_dir)
except:
  print("Folder exists")

import json
import os
import numpy as np
import pandas as pd

#show the number of videoclips which contain the target action (Clapping_hands)
len(output_json)

#show the the videoId, start time and end time of the output videoclips
for address in output_json['FileName']:
  video_name=address.split("/")[-1]
  print(video_name.split("+")[0],video_name.split("+")[1],video_name.split("+")[2].split(".")[0])

#output the json file
## the information of every 300 videoclips are combined in a json file
df=[]
nick_name="CSCE636Spring2021-RZ241-2"
label="Clapping-hands"

max_number=300
file_num=0
name_base="ResultOfDetection_RZ241_submission2_"+model_name+"_"+testset_name
video_count=0

for address in output_json['FileName']:
  video_count +=1
  video_name=address.split("/")[-1]
  videoid=video_name.split("+")[0]
  video_start=video_name.split("+")[1]
  video_end=video_name.split("+")[2].split(".")[0]
  df_tmp={"videoId":videoid,"type":"segment","startTime":float(video_start),"endTime":float(video_end),"observer":nick_name,"isHuman":False,
       "confirmedBySomeone": False,"rejectedBySomeone": False,"observation":{"label": label,"labelConfidence": 0.85}}
  df.append(df_tmp)
  
  if (video_count % max_number==0):
    file_num +=1
    filename=name_base+str(file_num)+".json"
    with open(os.path.join(json_dir,filename), 'w',encoding='utf-8') as f:
      json.dump(df, f,ensure_ascii=False, indent=4)
    df=[]

if (video_count % max_number>0):
  file_num +=1
  filename=name_base+str(file_num)+".json"
  with open(os.path.join(json_dir,filename), 'w',encoding='utf-8') as f:
    json.dump(df, f,ensure_ascii=False, indent=4)