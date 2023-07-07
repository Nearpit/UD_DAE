import pickle
import os
from argparse import ArgumentParser

def get_arguments():
    parser = ArgumentParser()
    parser.add_argument("-d", "--dataset",
                        help="What dataset to train on", 
                        required=True, 
                        choices=["dna", "splice", "toy"])
    parser.add_argument("-a", "--algorithm",
                        help="What active learning algorithm to evaluate",  
                        required=True,
                        choices=["random",
                                 "cheating",
                                 "keychain",
                                 "bald", 
                                 "coreset",
                                 "entropy",
                                 "margin"])
    parser.add_argument("-r", "--random_seed",
                        help="What random seed to use",  
                        type=int,
                        default=42)
    
    parser.add_argument("-hi", "--hindered_iters",
                        help="How many hindered iterations should happen to retune the classifier",
                        type=int,
                        default=10)
    
    return parser.parse_args()



def store_results(array, filename):
 
    path = "results/"
    if not os.path.exists(path):
        os.makedirs(path)

    with open(f'{path}{filename}.pkl', 'wb') as file:
        pickle.dump(array, file)