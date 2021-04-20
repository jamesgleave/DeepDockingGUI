"""
James Gleave
v1.2.0

A class used to store training history

# Usage...
# hist = DataHistory(data)
# hist.averages -> {'iteration_1': {'loss': [0.7453892707824707, ...], 'sparse_categorical_accuracy': [...], ...}, ...}
# hist.current_phase -> integer from 0 to 5
# hist.plots -> {'iteration_1': [{'loss': [...], 'sparse_categorical_accuracy': [...], ...}, {...}, ...]}
# hist.molecules_remaining -> {'iteration_1': {'true': X, 'estimate': Y, 'error': Z}, 'iteration_2': ...}
# hist.current_iteration -> returns the current iteration
"""


class DataHistory:
    def __init__(self, data):
        self.history = data

        # Load the iterations and sort the list
        self.iterations = list(data.keys())
        try:
            self.iterations.sort(key=lambda x: int(x.split("_")[1]))
        except KeyError:
            self.iterations.sort()

        self.plots = self.__generate_plot_data()
        self.averages = self.__calc_averages()

        self.current_iteration = self.__get_current_iteration()  # TODO: handle error when no project is loaded...
        self.current_phase = data[self.current_iteration]['itr']['current_phase']
        self.current_phase_eta = data[self.current_iteration]['itr']['phase_eta']
        self.molecules_remaining = dict.fromkeys(self.iterations)
        self.is_idle = data[self.current_iteration]['itr']['is_idle']

        # Store the crash report (hopefully no crashes)
        self.crash_report = self.history[self.current_iteration]['itr']['crash_report']

        # The percent complete for the iteration
        self.itr_percent = self.history[self.current_iteration]['itr']['itr_percent']
        self.full_percent = self.history[self.current_iteration]['itr']['full_percent']

        # Are we running the final phase?
        self.final_phase = self.history[self.current_iteration]['itr']['final_phase']

        try:
            for key in self.molecules_remaining:
                self.molecules_remaining[key] = data[key]['itr']['molecules_remaining']
        except TypeError:
            pass

    def get_model(self, iteration, model_number, averages=False):
        if averages:
            return self.averages[iteration]
        else:
            return self.history[self.iterations[iteration]]['models'][model_number]

    def __get_current_iteration(self):
        for key in self.history:
            try:
                if self.history[key]['itr']['in_progress']:
                    return key
            except TypeError:
                pass
        return 'iteration_1'

    def __calc_averages(self):
        averages = {}
        try:
            keys = list(self.plots['iteration_1'][0].keys())
        except (IndexError, KeyError):
            return averages
        for itr in self.plots:
            averages[itr] = {}
            for metric in keys:
                metric_list = []
                for model in self.plots[itr]:
                    metric_list.append(model[metric])
                averages[itr][metric] = self.__average_cols(metric_list)
        return averages

    def __generate_plot_data(self):
        # Loop through iterations...
        plots = {}
        for iteration in self.history:
            plots[iteration] = []  # Create a list to store models from each iteration
            try:
                # Loop through models...
                for model_number, model in enumerate(self.history[iteration]['models']):
                    # Create a dict of lists to store the plot values.
                    # If the model has not finished an epoch yet, then break
                    try:
                        model_data = {}
                        for key in model["epoch_1"]:
                            # Reformat the keys to make them easy to display dynamically
                            model_data[self.reformat(key)] = []
                    except KeyError:
                        break

                    # Loop through epochs...
                    for epoch in model:
                        # Loop through each metric
                        for metric in model[epoch]:
                            model_data[self.reformat(metric)].append(model[epoch][metric])
                    plots[iteration].append(model_data)
            except TypeError:
                pass
        return plots

    def reformat(self, key):
        new_key = ""
        if "_" in key:
            tokens = [s.capitalize() for s in key.replace("val", "Validation").split("_")]
            for token in tokens:
                new_key += token + " "
            if new_key[-1] == " ":
                new_key = new_key[0:-1]
        else:
            new_key = key.capitalize()

        # Simplify words
        if "Sparse Categorical " in new_key:
            new_key = new_key.replace("Sparse Categorical ", "")

        if "acc" == key or "val_acc" == key:
            new_key = new_key.replace("Acc", "Accuracy")

        return new_key

    def __repr__(self):
        print("Iterations:", self.iterations)
        print("Current Iteration:", self.current_iteration)
        print("Current Phase:", self.current_phase)
        print("Molecules Remaining:", self.molecules_remaining)
        print("Iteration Percent:", self.itr_percent)
        print("Full Percent:", self.full_percent)

        return ""

    @staticmethod
    def __average_cols(arr):
        if len(arr) == 0:
            return []

        average = []
        max_len = max([len(length) for length in arr])
        for i in range(max_len):
            col_average = []
            for row in arr:
                if i < len(row):
                    col_average.append(row[i])
            average.append(sum(col_average)/len(col_average))
        return average



