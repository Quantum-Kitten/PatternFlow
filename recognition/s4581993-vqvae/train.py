import numpy as np
from tensorflow import keras
import tensorflow as tf

from dataset import get_train_dataset
import modules
from modules import VQVAETrainer
from utils import models_directory, vqvae_weights_filename

# Get the datasets
train_ds = get_train_dataset()
data_variance = np.var(train_ds)

# Train the VQ-VAE model
vqvae_trainer = VQVAETrainer(data_variance, latent_dim=16, num_embeddings=128)
vqvae_trainer.compile(optimizer=keras.optimizers.Adam())
vqvae_trainer.fit(train_ds, epochs=30, batch_size=128)

# Save the model
vqvae_trainer.save_weights(models_directory + vqvae_weights_filename)
