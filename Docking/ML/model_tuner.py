from Docking.ML.DDModel import DDModel
import numpy as np
import tensorflow as tf
import kerastuner as kt
from Docking.ML.utils import *
import Docking.ML.load_data
import IPython


class ClearTrainingOutput(tf.keras.callbacks.Callback):
    def on_train_end(*args, **kwargs):
        IPython.display.clear_output(wait=True)


if __name__ == '__main__':
    # Load config
    print("Loading Config...")
    config = read_tuner_config('tuner_config.txt')
    # For hyper band tuner
    train_path, test_path = config['training_path'], config['testing_path']
    directory = config['directory']
    project_name = config['project_name']
    objective = config['objective']
    max_trials = config['max_trials']
    max_epochs = config['max_epochs']
    factor = config['factor']
    hyperband_iterations = config['hyperband_iterations']
    direction = config['direction']

    # For search
    steps_per_epoch = config['steps_per_epoch']
    validation_steps = config['validation_steps']
    epochs = config['epochs']
    batch_size = config['batch_size']

    print("Loading Dataset...")
    data = Docking.ML.load_data.load(train_path, test_path)
    train_x, train_y, test_x, test_y = data()
    train_x, train_y = train_x.tolist(), train_y.tolist()
    test_x, test_y = test_x.tolist(), test_y.tolist()
    tr_x = np.array(train_x)
    tr_y = np.array(train_y)

    tx = np.array(test_x)
    ty = np.array(test_y)

    tuner = kt.BayesianOptimization(DDModel.build_tuner_model,
                                    objective=kt.Objective(objective, direction),
                                    project_name=project_name,
                                    directory=directory,
                                    max_trials=max_trials)

    tuner.search_space_summary()
    tuner.search(tr_x, tr_y,
                 validation_data=(tx, ty), epochs=epochs, batch_size=batch_size,
                 class_weight={0: 2, 1: 1},
                 callbacks=[tf.keras.callbacks.EarlyStopping(monitor=objective,
                                                             min_delta=0,
                                                             patience=3,
                                                             verbose=0,
                                                             mode=direction)])

    print("Done...")

    # Show a summary of the search
    tuner.results_summary()

    # Retrieve the best 3 models.

    # 1
    best_hyperparameters = tuner.get_best_hyperparameters(1)[0]
    best_model = tuner.get_best_models(num_models=1)[0]
    print("Saving best model...")

    model_location = config['model_location'] + "/"
    model = DDModel.load(best_model, kt_hyperparameters=best_hyperparameters)
    model.save(model_location + project_name + "_1st_" + objective + "_" + direction, json=True)

    # 2
    best_hyperparameters = tuner.get_best_hyperparameters(2)[1]
    best_model = tuner.get_best_models(num_models=2)[1]
    print("Saving best model...")

    model_location = config['model_location'] + "/"
    model = DDModel.load(best_model, kt_hyperparameters=best_hyperparameters)
    model.save(model_location + project_name + "_2nd_" + objective + "_" + direction, json=True)

    # 3
    best_hyperparameters = tuner.get_best_hyperparameters(3)[2]
    best_model = tuner.get_best_models(num_models=3)[2]
    print("Saving best model...")

    model_location = config['model_location'] + "/"
    model = DDModel.load(best_model, kt_hyperparameters=best_hyperparameters)
    model.save(model_location + project_name + "_3rd_" + objective + "_" + direction, json=True)

    print("Saved!")
