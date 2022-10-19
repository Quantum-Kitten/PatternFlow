# This file contains the source code for training, validating, testing and saving my model
import os
import sys
sys.path.insert(1, os.getcwd())
import modules
from dataset import loadFile
import tensorflow as tf
from tensorflow import keras
from tqdm import tqdm
import time
import csv

def saveOption(optimizer, siamese):
    checkpoint_dir = os.path.join(os.getcwd(), "Siamese_ckeckpoint")
    if not os.path.exists(checkpoint_dir):
        os.mkdir(checkpoint_dir)
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
    checkpoint = tf.train.Checkpoint(optimizer=optimizer,
                                  net=siamese)
    return checkpoint_prefix, checkpoint

@tf.function
def train_step(pairs, optimizer, siamese, train_acc_metric, loss_tracker):
    # print(pairs)
    with tf.GradientTape() as gra_tape:
        y_true = pairs[2]
        # print(pairs[0], pairs[1])
        y_pred = siamese([pairs[0], pairs[1]], training=True)
        lossValue = (modules.loss())(y_true, y_pred)
        
    gradient = gra_tape.gradient(lossValue, siamese.trainable_weights)
    optimizer.apply_gradients(zip(gradient, siamese.trainable_weights))
    train_acc_metric.update_state(y_true, y_pred)
    loss_tracker.update_state(lossValue)
    return lossValue

@tf.function
def valid_step(pairs, siamese, test_acc_metric, loss_tracker):
    y_true = pairs[2]
    y_pred = siamese([pairs[0], pairs[1]], training=False)
    lossValue = (modules.loss())(y_true, y_pred)
    test_acc_metric.update_state(y_true, y_pred)
    loss_tracker.update_state(lossValue)
    return lossValue

def train(train_ds, valid_ds, epochs, train_step, checkpoint_prefix, checkpoint, optimizer, siamese):
    # print(train_ds)
    info = {'train_loss': [],
            'train_accu': [],
            'valid_loss': [],
            'valid_accu': []}
    loss_tracker = keras.metrics.Mean()
    train_acc_metric = keras.metrics.BinaryAccuracy()
    valid_acc_metric = keras.metrics.BinaryAccuracy()
    for epoch in range(epochs):
        print('>>>>>>>>> Epoch {}'.format(epoch+1))
        # count = 0
        # siameseLoss = 0
        batchnum = 0
        # train
        for batch in train_ds:
            if batchnum % 100 == 1:
                print('>> Training batch {}'.format(batchnum))
                print('> Train_loss {}'.format(loss_tracker.result().numpy()))
                print('> Train_accu {}'.format(train_acc_metric.result().numpy()))
            lossValue = train_step(batch, optimizer, siamese, train_acc_metric, loss_tracker)
            # siameseLoss += lossValue
            # count += 1
            batchnum += 1
        info['train_loss'].append(loss_tracker.result().numpy())
        train_accu = train_acc_metric.result().numpy()
        info['train_accu'].append(train_accu)
        train_acc_metric.reset_states()
        loss_tracker.reset_states()
        
        # v_count = 0
        # v_siameseLoss = 0
        batchnum = 0
        # validate
        for batch in valid_ds:
            if batchnum % 100 == 1:
                print('>> Validating batch {}'.format(batchnum))
                print('> Valid_loss {}'.format(loss_tracker.result().numpy()))
            lossValue = valid_step(batch, siamese, valid_acc_metric, loss_tracker)
            # v_siameseLoss += lossValue
            # v_count += 1
            batchnum += 1
        info['valid_loss'].append(loss_tracker.result().numpy())   
        valid_accu = valid_acc_metric.result().numpy()
        info['valid_accu'].append(valid_accu)     
        valid_acc_metric.reset_states()
        loss_tracker.reset_states()
        
        # Save the model every epochs
        if (epoch + 1) % 1 == 0:
            checkpoint.save(file_prefix = checkpoint_prefix)   
                
        row = [epoch, (info['train_loss'])[-1], (info['train_accu'])[-1], (info['valid_loss'])[-1], (info['valid_accu'])[-1]]
        print('Epoch {} | Train loss {} | Train Accu {} | Valid loss {} | Valid Accu {}'.
              format(row[0], row[1], row[2], row[3], row[4]))
        f = open('./record.csv', 'a+')
        writer = csv.writer(f)
        writer.writerow(row)
        f.close()

    return info

def main():
    t_ad, t_nc, v_ad, v_nc = loadFile('F:/AI/COMP3710/data/AD_NC/')
    td = modules.generatePairs(t_ad, t_nc)
    vd = modules.generatePairs(v_ad, v_nc)
    opt = keras.optimizers.RMSprop()
    siamese = modules.makeSiamese(modules.makeCNN())
    checkpoint_prefix, checkpoint = saveOption(opt, siamese)
    history = train(td, vd, 5, train_step, checkpoint_prefix, checkpoint, opt, siamese)
    
    # # results = siamese.evaluate(vd)
    # # print("test loss, test acc:", results)
    
if __name__ == "__main__":
    main()