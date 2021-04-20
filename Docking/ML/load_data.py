import pandas as pd
from sklearn.utils import shuffle


def load(path_train, path_test):
    loaded_train = shuffle(pd.read_pickle(path_train))
    loaded_test = shuffle(pd.read_pickle(path_test))

    train_x = loaded_train.morgan_fingerprint
    train_y = loaded_train.docking_score

    test_x = loaded_test.morgan_fingerprint
    test_y = loaded_test.docking_score

    data = DataContainer(train_x, train_y, test_x, test_y)
    return data


def load_data():
    """These function will load up the data like as done in phase 4 and 5 """
    pass


class DataContainer:
    def __init__(self, train_x, train_y, test_x, test_y):
        self.train_x = train_x
        self.train_y = train_y
        self.test_x = test_x
        self.test_y = test_y

    def __repr__(self):
        print("Features:", self.train_x.name, "-> Lables:", self.train_y.name)
        print("Train Size:", len(self.train_x))
        print("Test Size:", len(self.test_x))
        print("Hit/Miss ratio:", sum([1 if x else 0 for x in self.train_y])/len(self.train_y) * 100, "%")
        return ""

    def __call__(self, *args, **kwargs):
        return self.train_x, self.train_y, self.test_x, self.test_y
