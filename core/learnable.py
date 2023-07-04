from typing import Any
import torch
import optuna

from utilities import NN, EarlyStopper, Tuner

class Learnable:

    #DEBUG
    epochs=500

    model = None
    model_class = NN
    model_configs = {"MLP": {"last_activation": "Softmax",
                              "criterion": "CrossEntropyLoss"},
                     "AE": {"last_activation": "Identity",
                            "criterion": "MSELoss"}}
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tuner_configs = {
        "n_trials": 3 #DEBUG
        }


    def __init__(self, 
                 pool,
                 random_seed,
                 model_arch_name="MLP"):
        # Reproducibility
        torch.manual_seed(random_seed)
        self.tuner_configs["random_seed"] = random_seed
        self.pool = pool
        self.model_configs = self.model_configs[model_arch_name]
        self.model_configs.update({"metrics_dict":pool.metrics,
                                   "batch_size":pool.batch_size})
        self.model_arch_name = model_arch_name
        self.tune_model()

    def __call__(self, x):
        return self.model(x)

    @staticmethod
    def hook_once(func):
            called = False  
            def wrapper(self, *args, **kwargs):
                nonlocal called
                if not called:
                    called = True
                    self.embedding_hook() # to make sure that we hook once at the right moment
                return func(self, *args, **kwargs)

            return wrapper
    
    def initilize_first(func):
        def wrapper(self, *args, **kwargs):
                if not self.model:
                   self.model = self.initialize_model()  # to make sure that we initialize the model
                return func(self, *args, **kwargs)
        return wrapper
    
    def initialize_model(self):
        return self.model_class(self.device, **self.model_configs)
    
    def update_model_configs(self, new_configs):
        self.model_configs.update(new_configs)
        self.model = self.initialize_model()
    
    def eval_model(self, split_name):
        total_loss = 0
        loader = getattr(self.pool, f"{split_name}_loader")
        with torch.no_grad():
            for inputs, targets in loader:

                targets = targets.to(self.device)
                inputs = inputs.to(self.device)

                predictions = self.model(inputs)

                batch_loss = self.model.criterion(predictions, targets)
                total_loss += batch_loss.item()
                self.model.metrics_set.update(inputs=predictions, targets=targets)  

        return total_loss, self.model.metrics_set.flush()

    @initilize_first
    def train_model(self, trial=None):

        # TO DISABLE DROPOUT (and Normalization if it is added)
        self.model.eval()
        
        early_stopper = EarlyStopper()

        for epoch_num in range(self.epochs):
            train_loss = 0

            for inputs, targets in self.pool.train_loader:

                targets = targets.to(self.device)
                inputs = inputs.to(self.device)

                predictions = self.model(inputs.float())
                
                batch_loss = self.model.criterion(predictions, targets.float())
                train_loss += batch_loss.item()
                self.model.metrics_set.update(inputs=predictions, targets=targets)
                self.model.zero_grad()
                batch_loss.backward()
                self.model.optimizer.step()
                                 
            train_metrics = self.model.metrics_set.flush()
            val_loss, val_metrics = self.eval_model("val")

            if trial:
                trial.report(val_loss, epoch_num)
                if trial.should_prune():
                    raise optuna.exceptions.TrialPruned()
                
            if early_stopper.early_stop(val_loss):
                break

    def reset_model(self):
        for seq in self.model.children():
            for layer in seq.modules():
                if hasattr(layer, 'reset_parameters'):
                    layer.reset_parameters()
    def tune_model(self):
        self.update_model_configs(Tuner(pool=self.pool, model=self, **self.tuner_configs)())
