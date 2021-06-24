import IPython
import kerastuner as kt
import numpy as np
import tensorflow as tf

try:
    import Docking.ML.load_data
    from Docking.ML.DDModel import DDModel
    from Docking.ML.Models import TunerModel
    from Docking.ML.utils import *
except:
    import ML.load_data
    from ML.DDModel import DDModel
    from ML.Models import TunerModel
    from ML.utils import *


class ClearTrainingOutput(tf.keras.callbacks.Callback):
    def on_train_end(*args, **kwargs):
        IPython.display.clear_output(wait=True)


class Config:
    def __init__(self, config):
        self.directory = config['directory']
        self.project_name = config['project_name']
        self.objective = config['objective']
        self.max_trials = config['max_trials']
        self.max_epochs = config['max_epochs']
        self.factor = config['factor']
        self.hyperband_iterations = config['hyperband_iterations']
        self.direction = config['direction']

        # For search
        self.steps_per_epoch = config['steps_per_epoch']
        self.validation_steps = config['validation_steps']
        self.epochs = config['epochs']
        self.batch_size = config['batch_size']
        self.model_location = config['model_location']


def optimize(technique):
    # Load config
    print("Loading Config...")
    config_file = read_tuner_config('../ML/tuner_config.txt')
    tuner_config = Config(config_file)
    print("Loading Dataset...")
    train_path, test_path = config_file['training_path'], config_file['testing_path']
    data = ML.load_data.load(train_path, test_path)
    train_x, train_y, test_x, test_y = data()
    train_x, train_y = train_x.tolist(), train_y.tolist()
    test_x, test_y = test_x.tolist(), test_y.tolist()

    tr_x = np.array(train_x)
    tr_y = np.array(train_y)
    tx = np.array(test_x)
    ty = np.array(test_y)

    if technique == 'bayesian':
        return run_bayesian(tr_x, tr_y, tx, ty, tuner_config, {0: 1, 1: 1})


def run_bayesian(tr_x, tr_y, tx, ty, config: Config, class_weights):
    tuner_model = TunerModel(tr_x.shape[1:])
    tuner = kt.BayesianOptimization(tuner_model.build_tuner_model,
                                    objective=kt.Objective(config.objective, config.direction),
                                    project_name=config.project_name,
                                    directory=config.directory,
                                    max_trials=config.max_trials, overwrite=True)

    tuner.search_space_summary()
    tuner.search(tr_x, tr_y,
                 validation_data=(tx, ty),
                 epochs=config.epochs,
                 batch_size=config.batch_size,
                 class_weight=class_weights,
                 callbacks=[tf.keras.callbacks.EarlyStopping(monitor=config.objective, min_delta=0, patience=3,
                                                             verbose=0, mode=config.direction)])
    # Show a summary of the search
    tuner.results_summary()

    # Retrieve the best model.
    print("Saving the top model...")
    best_hyperparameters = tuner.get_best_hyperparameters(1)[0]
    print("Top hyperparameters:", best_hyperparameters)

    best_model = tuner.hypermodel.build(best_hyperparameters)
    model = DDModel.load(best_model, kt_hyperparameters=best_hyperparameters)
    return model


def run_sklearn(tr_x, tr_y, config: Config, build_model_func):
    """
    Runs the bayesian optimization algorithm on an sklearn model.
    """
    from sklearn import metrics, model_selection

    # Create the tuner
    tuner = kt.tuners.Sklearn(
        oracle=kt.oracles.BayesianOptimization(objective=kt.Objective('score', 'max'),
                                               max_trials=config.max_trials),
        hypermodel=build_model_func,
        scoring=metrics.make_scorer(metrics.precision_score),
        cv=model_selection.StratifiedKFold(5),
        directory=config.directory,
        project_name=config.project_name)

    # Run the search
    tuner.search(tr_x, tr_y)

    # Return the best model
    return build_model_func(tuner.get_best_hyperparameters(num_trials=1)[0], return_light_model=True)
