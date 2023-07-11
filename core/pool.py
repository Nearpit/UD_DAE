import numpy as np
from torch.utils.data import DataLoader, Subset


class Pool:

    def __init__(self, data, random_seed, whole_dataset=False, **kwargs):
        np.random.seed(random_seed)
        self.__dict__.update(**data["train"].configs)

        if whole_dataset:
            self.n_labeled = self.train_size

        self.idx_lb = np.random.choice(self.train_size, size=self.n_labeled, replace=False)
        self.data = data

        for key_name in ["val", "test"]:
            if key_name in self.data:
                setattr(self, f"{key_name}_loader", DataLoader(data[key_name], batch_size=self.batch_size))

        self.idx_intact = np.arange(self.train_size)

    def get_len(self, pool="total"):
        if pool == "labeled":
            return len(self.idx_lb)
        elif pool == "unlabeled":
            return len(self.idx_ulb) 
        else:
            return self.train_size

    
    @property
    def idx_ulb(self):
        return np.delete(self.idx_intact, self.idx_lb)
    
      
    @property
    def train_loader(self):
        drop_last = self.get_len("labeled") > self.batch_size # drop last if the number of labeled instances is bigger than the batch_size
        return DataLoader(Subset(self.data['train'], self.idx_lb), 
                          batch_size=self.batch_size, 
                          shuffle=True, 
                          drop_last=drop_last)
    
    def add_new_inst(self, idx):
        self.idx_lb = np.append(self.idx_lb, idx)
        assert len(self.idx_ulb)
    
    def get(self, pool):
        if pool == "labeled":
            return self.data["train"][self.idx_lb]
        elif pool == "unlabeled":
            return self.data["train"][self.idx_ulb]   
          
    def get_train_instance(self, idx):
        return self.data["train"][idx]