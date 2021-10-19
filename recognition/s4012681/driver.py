"""
Author: Richard Wainwright
Student ID: 40126812
Date: 05/10/2021

Driver for the UNet3d model for the classification of the Prostate 3D data set
"""

from unet import get_nifti_data, one_hot, normalise, unet, reshape, scheduler, dice
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import glob
from sklearn.model_selection import train_test_split
import nibabel
import skimage
from tensorflow.keras.utils import Sequence
from tensorflow.keras.optimizers import Adam
import math
import random
from scipy.ndimage import rotate


IMG_WIDTH = 128
IMG_HEIGHT = 256
IMG_DEPTH = 256
IMG_CHANNELS = 1
BATCH_SIZE = 1
FILTERS = 1
EPOCHS = 1


class MRISequence(Sequence):
    def __init__(self, x_set, y_set, batch_size):
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size
        self.indices = list(range(len(self.x)))

    def __len__(self):
        return math.ceil(len(self.x) / self.batch_size)

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) *
                                               self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) *
                                               self.batch_size]

        return np.array([reshape(1, 1, normalise(get_nifti_data(file_name))) for file_name in batch_x]), \
               np.array([reshape(1, 6, one_hot(file_name)) for file_name in batch_y])

    def on_epoch_end(self):
        np.random.shuffle(self.indices)


mri_location = "/home/Student/s4012681/semantic_MRs_anon/*.nii.gz"
label_location = "/home/Student/s4012681/semantic_labels_anon/*nii.gz"

n_mri = len(glob.glob(mri_location))
n_labels = len(glob.glob(label_location))

mri_names = sorted(glob.glob(mri_location))
labels_names = sorted(glob.glob(label_location))

# split 5% of the files off as a test set
x_train, x_test, y_train, y_test = train_test_split(mri_names, labels_names,
                                                    test_size=0.05)

# split 15% of the training data off for validation
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train,
                                                  test_size=0.15)

train = MRISequence(x_train, y_train, BATCH_SIZE)
test = MRISequence(x_test, y_test, BATCH_SIZE)
val = MRISequence(x_val, y_val, BATCH_SIZE)

# print(train.__getitem__(0)[0].shape)
# print(train.__getitem__(0))
# print(type(train[0]))
# print("")

# img = train[0][0][0]
# mask = train[0][1][0]
#
# print(type(img))
# print(type(mask))
#
# print(img.shape)
# print(mask.shape)
#
# fig1, (ax1, ax2) = plt.subplots(1, 2)
# ax1.imshow(img[img.shape[0] // 2], cmap='gray')
# ax2.imshow(mask[mask.shape[0] // 2], cmap='gray')
# fig1.show()
#
# # visualise all slices
# fig2, ax1 = plt.subplots(1, 1, figsize=(13, 20))
# ax1.imshow(skimage.util.montage(img))
# ax1.set_title('image')
# fig2.show()
#
# fig3, ax1 = plt.subplots(1, 1, figsize=(20, 20))
# ax1.imshow(skimage.util.montage(mask))
# ax1.set_title('mask')
# fig3.show()

model = unet(FILTERS)

# model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-04), loss='categorical_crossentropy', metrics=['accuracy'])
model.compile(optimizer=Adam(lr=1e-5, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.000000199),
              loss='binary_crossentropy', metrics=['accuracy'])
model.summary(line_length=120)

callback = tf.keras.callbacks.LearningRateScheduler(scheduler)

# Fit the training data and store for the plot
curves = model.fit(train, epochs=EPOCHS, validation_data=val, batch_size=BATCH_SIZE, callbacks=[callback])
# Evaluate the model with the test data
print()
print("Evaluation:")
model.evaluate(test)

# Plot
# plot accuracy
# fig, (ax1, ax2) = plt.subplots(1, 2)
# ax1.plot(curves.history['accuracy'])
# ax1.plot(curves.history['val_accuracy'])
# ax1.title('Accuracy History')
# ax1.ylabel('Accuracy')
# ax1.xlabel('Epoch')
# ax1.legend(['train', 'test'], loc='upper left')
# plot loss
# ax2.plot(curves.history['loss'])
# ax2.plot(curves.history['val_loss'])
# ax2.title('Loss History')
# ax2.ylabel('Loss')
# ax2.xlabel('Epoch')
# ax2.legend(['train', 'test'], loc='upper left')
# fig.savefig('acc_loss.png')

# Get the predictions generated by the model
classifications = model.predict(test)
print(classifications.shape)
print(type(classifications))

test_labels = np.empty((len(test), 128, 256, 256, 6))
for i in range(len(test)):
    test_labels[i] = test[i][1]

print("Body: ", dice(test_labels[..., 1], classifications[..., 1]))
print("Bones: ", dice(test_labels[..., 2], classifications[..., 2]))
print("Bladder: ", dice(test_labels[..., 3], classifications[..., 3]))
print("Rectum: ", dice(test_labels[..., 4], classifications[..., 4]))
print("Prostate: ", dice(test_labels[..., 5], classifications[..., 5]))
print("Overall (including background): ", dice(test_labels, classifications))

"""
LearningRateScheduler
automatically changes learning rate

custom callback function:
can do model.predict between epochs
"""
