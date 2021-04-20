import csv
import numpy as np


class DDGenerator:
    """
    A data generator
    """
    def __init__(self, train_features, train_labels, val_features, val_labels, batch_size, cutoff):
        self.cutoff = cutoff
        self.batch_size = batch_size

        # The path to the training set and labels
        self.train_labels_csv = train_labels
        self.train_features_csv = train_features

        # The path to the validation set and labels
        self.val_features_csv = val_features
        self.val_labels_csv = val_labels

    def train_flow(self):
        with open(self.train_features_csv, "r") as csv1, open(self.train_labels_csv, "r") as csv2:
            reader1 = csv.reader(csv1)
            reader2 = csv.reader(csv2)
            for row1, row2 in zip(reader1, reader2):
                try:
                    fp = [None] * self.batch_size
                    score = [None] * self.batch_size
                    for i in range(self.batch_size):
                        morgan = np.array(self.decompress_morgan(row1[1:]))
                        label = float(row2[0]) > self.cutoff
                        fp[i] = morgan
                        score[i] = label
                    yield np.array(fp).reshape((self.batch_size, 1024)), np.array(score)
                except ValueError:
                    yield

    def val_flow(self):
        with open(self.val_features_csv, "r") as csv1, open(self.val_labels_csv, "r") as csv2:
            reader1 = csv.reader(csv1)
            reader2 = csv.reader(csv2)
            for row1, row2 in zip(reader1, reader2):
                try:
                    fp = [None] * self.batch_size
                    score = [None] * self.batch_size
                    for i in range(self.batch_size):
                        morgan = np.array(self.decompress_morgan(row1[1:]))
                        label = float(row2[0]) > self.cutoff
                        fp[i] = morgan
                        score[i] = label
                    yield np.array(fp).reshape((self.batch_size, 1024)), np.array(score)
                except ValueError:
                    yield

    # Decompress a morgan fingerprint from the dataset
    def decompress_morgan(self, mol_info):
        # ID_labels is a dataframe containing the zincIDs and their corresponding scores.
        morgan = np.zeros(1024, dtype=int)

        # "Decompressing" the information from the file about where the 1s are on the 1024 bit vector.
        # array of indexes of the binary 1s in the 1024 bit vector representing the morgan fingerprint
        bit_indices = mol_info
        for elem in bit_indices:
            morgan[int(elem)] = 1

        return morgan


def keras_generator_test(f="", lbl=""):
    from tensorflow.keras.layers import Dense
    from tensorflow.keras.models import Input, Model

    inputs = Input(shape=[1024])
    x = inputs
    x = Dense(10000, activation='relu')(x)
    output = Dense(1, activation='sigmoid')(x)

    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.summary()

    generator = DDGenerator(train_features=f, train_labels=lbl, val_features=f, val_labels=lbl, cutoff=-10,
                            batch_size=32)
    model.fit_generator(generator=generator.train_flow(), validation_data=generator.val_flow(), steps_per_epoch=100,
                        validation_steps=100)


