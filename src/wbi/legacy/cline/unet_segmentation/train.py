import numpy as np
import tensorflow as tf
from wbi.legacy.cline.unet_segmentation import unet_model
from wbi.legacy.cline.unet_segmentation import load_data
from pathlib import Path
import os

# set image size
img_size = 1024

proj_dir = Path(__file__).parent.parent.parent


# Load dataset from a data folder
train_generator, val_generator = load_data.generators(f"{proj_dir}/unet_training_data", size=img_size)

# Using the previously defined unet_model function
model = unet_model.unet_model(input_shape=(img_size, img_size, 1))

adam = tf.keras.optimizers.Adam(learning_rate=1e-5)

model.compile(optimizer=adam, loss='binary_crossentropy', metrics=['accuracy'])

# Callback for early stopping to prevent overfitting
early_stopping = tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)

# Train the model
model.fit(train_generator,  
          steps_per_epoch=30,
          validation_data=val_generator, 
          validation_steps=30,
          epochs=300,
          batch_size=4,
          callbacks=[early_stopping])


# save model in the model directory
model_dir = proj_dir/"model"
if not os.path.exists(model_dir):
        os.makedirs(model_dir)

model.save(f"{model_dir}/best_model.h5")

# evaluation
loss, accuracy = model.evaluate(val_generator, steps=8)
print(f"Validation Loss: {loss:.4f}")
print(f"Validation Accuracy: {accuracy:.4f}")



