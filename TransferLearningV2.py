#dependencies
import numpy as np  
from keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img  
from keras.models import Sequential  
from keras.layers import Dropout, Flatten, Dense  
from keras import applications  
from keras.utils.np_utils import to_categorical  
import matplotlib.pyplot as plt  
import math  
import cv2  

# dimensions of our images.  
img_width, img_height = 224, 224  

top_model_weights_path = 'bottleneck_fc_model_weights.h5'  
model_h5 = 'bottleneck_fc_model.h5'
train_data_dir = '../dataset/train'  
validation_data_dir = '../dataset/validation'  

# number of epochs to train top model  
epochs = 25  
# batch size used by flow_from_directory and predict_generator  
batch_size = 16

#modelo que cargamos sin las top layers
model = applications.VGG16(include_top=False, weights='imagenet')

#We then create the data generator for training images, and run them on the VGG16 model to save the bottleneck features for training.
def save_bottlebeck_features():
	datagen = ImageDataGenerator(rescale=1. / 255)  

	generator = datagen.flow_from_directory(  
	 train_data_dir,  
	 target_size=(img_width, img_height),  
	 batch_size=batch_size,  
	 class_mode=None,  
	 shuffle=False)  

	nb_train_samples = len(generator.filenames)  
	num_classes = len(generator.class_indices)  

	predict_size_train = int(math.ceil(nb_train_samples / batch_size))  

	print('Generando bottlenecks...')
	bottleneck_features_train = model.predict_generator(  
	 generator, predict_size_train)  

	np.save('bottleneck_features_train.npy', bottleneck_features_train)

	#lo mismo que antes para la validation data
	generator = datagen.flow_from_directory(  
	 validation_data_dir,  
	 target_size=(img_width, img_height),  
	 batch_size=batch_size,  
	 class_mode=None,  
	 shuffle=False)  

	nb_validation_samples = len(generator.filenames)  

	predict_size_validation = int(math.ceil(nb_validation_samples / batch_size))  

	bottleneck_features_validation = model.predict_generator(  
	 generator, predict_size_validation)  

	np.save('bottleneck_features_validation.npy', bottleneck_features_validation)  

#entrenamos el top model
def train_top_model():
	datagen_top = ImageDataGenerator(rescale=1./255)  
	generator_top = datagen_top.flow_from_directory(  
	     train_data_dir,  
	     target_size=(img_width, img_height),  
	     batch_size=batch_size,  
	     class_mode='categorical',  
	     shuffle=False)  

	nb_train_samples = len(generator_top.filenames)  
	num_classes = len(generator_top.class_indices)  

	# load the bottleneck features saved earlier  
	train_data = np.load('bottleneck_features_train.npy')  

	# get the class lebels for the training data, in the original order  
	train_labels = generator_top.classes  

	# convert the training labels to categorical vectors  
	train_labels = to_categorical(train_labels, num_classes=num_classes)

	#hacemos lo mismo con la validation data para el top mmodel
	generator_top = datagen_top.flow_from_directory(  
	     validation_data_dir,  
	     target_size=(img_width, img_height),  
	     batch_size=batch_size,  
	     class_mode=None,  
	     shuffle=False)  

	nb_validation_samples = len(generator_top.filenames)  

	validation_data = np.load('bottleneck_features_validation.npy')  

	validation_labels = generator_top.classes  
	validation_labels = to_categorical(validation_labels, num_classes=num_classes)

	#creamos top model para rellenar VGG16
	model = Sequential()  
	model.add(Flatten(input_shape=train_data.shape[1:]))  
	model.add(Dense(256, activation='relu'))  
	model.add(Dropout(0.5))  
	model.add(Dense(num_classes, activation='sigmoid'))  

	model.compile(optimizer='rmsprop',  
	          loss='categorical_crossentropy', metrics=['accuracy'])  

	history = model.fit(train_data, train_labels,  
	      epochs=epochs,  
	      batch_size=batch_size,  
	      validation_data=(validation_data, validation_labels))  

	model.save_weights('bottleneck_fc_model_weights.h5')
	model.save('bottleneck_fc_model.h5')  

	(eval_loss, eval_accuracy) = model.evaluate(  
	 validation_data, validation_labels, batch_size=batch_size, verbose=1)

	print("[INFO] accuracy: {:.2f}%".format(eval_accuracy * 100))  
	print("[INFO] Loss: {}".format(eval_loss))

	########ZONA DÓNDE VEO ENTRENAMIENTO######
	plt.figure(1)  

	# summarize history for accuracy  

	plt.subplot(211)  
	plt.plot(history.history['acc'])  
	plt.plot(history.history['val_acc'])  
	plt.title('model accuracy')  
	plt.ylabel('accuracy')  
	plt.xlabel('epoch')  
	plt.legend(['train', 'test'], loc='upper left')  

	# summarize history for loss  

	plt.subplot(212)  
	plt.plot(history.history['loss'])  
	plt.plot(history.history['val_loss'])  
	plt.title('model loss')  
	plt.ylabel('loss')  
	plt.xlabel('epoch')  
	plt.legend(['train', 'test'], loc='upper left')  
	plt.show()  
	######TERMINA ZONA DE VISUALIZACIÓN#######

	

#llamamos a las funciones
save_bottlebeck_features()  
train_top_model()  
  