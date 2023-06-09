import matplotlib.pyplot as plt
from matplotlib.lines import Line2D 
import matplotlib 
import matplotlib.patches as mpatches


import numpy as np
import torch 

import utilities


class Visualize:
    max_dot_size = 100
    def __init__(self, pool, clf, acq, steps=100):
        self.pool = pool
        self.clf = clf
        self.acq = acq

        x = np.concatenate([split.x for split in pool.data.values()])
        x1_min, x2_min = np.amin(x, axis=0) - np.std(x)
        x1_max, x2_max = np.amax(x, axis=0) + np.std(x)

        x1_span = np.linspace(x1_min, x1_max, steps)
        x2_span = np.linspace(x2_min, x2_max, steps)
        self.x1, self.x2 = np.meshgrid(x1_span, x2_span)
        self.clf_inputs = torch.from_numpy(np.column_stack([self.x1.ravel(), self.x2.ravel()])).float()
    

    
    def compute_clf_grad(self):
        self.clf_grad = (self.clf(self.clf_inputs)[:, 1]).reshape(self.x1.shape)

    def clf_train(self, ax, train_perf, val_perf):
        ax.contourf(self.x1, self.x2, self.clf_grad, alpha=0.3, cmap=plt.cm.coolwarm, antialiased=True)
        x, y = self.pool.get("unlabeled")
        ax.scatter(x[:, 0], x[:, 1], marker='2', c='grey', alpha=0.4, s=self.max_dot_size)

        x, y = self.pool.get("labeled")
        ax.scatter(x[:, 0], x[:, 1], marker='^', c=y.argmax(axis=-1), s=self.max_dot_size, cmap=plt.cm.coolwarm)        
        ax.set_title("Classifier Labeled/Unlabeled")
        performance_string = f"Train {train_perf[1]['MulticlassAccuracy']:.1%}\nVal {val_perf[1]['MulticlassAccuracy']:.1%}"
        ax.annotate(performance_string, xy=(0.03, 0.97), xycoords='axes fraction',
                    ha='left', va='top',
                    bbox=dict(boxstyle='round', fc='w'))
    

    def clf_test(self, ax, test_perf):

        ax.contourf(self.x1, self.x2, self.clf_grad, alpha=0.3, cmap=plt.cm.coolwarm, antialiased=True)

        x, y = self.pool.get("test")
        ax.scatter(x[:, 0], x[:, 1], marker='$*$', alpha=0.5, c=y.argmax(axis=-1), s=self.max_dot_size/2, cmap=plt.cm.coolwarm)
        
        ax.set_title("Classifier Test")
        performance_string = f"Test {test_perf[1]['MulticlassAccuracy']:.1%}"
        ax.annotate(performance_string, xy=(0.03, 0.97), xycoords='axes fraction',
                    ha='left', va='top',
                    bbox=dict(boxstyle='round', fc='w'))
    
        cb_boundary = plt.colorbar(matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0, 1), cmap=plt.cm.coolwarm), ax=[ax],location='left')
        cb_boundary.set_ticks([0, 1])
        cb_boundary.ax.tick_params(size=0)
        cb_boundary.set_ticklabels(["Class B", "Class A",])



        
    def acq_boundary(self, ax, chosen_idx):
        Z = (self.acq.get_scores(self.clf_inputs)).reshape(self.x1.shape)
        ax.contourf(self.x1, self.x2, Z, cmap=plt.cm.binary, alpha=0.3, antialiased=True)
        x, y = self.pool.get("unlabeled")
        chosen_x, chosen_y = x[chosen_idx], y[chosen_idx]
        x, y = np.delete(x, chosen_idx, axis=0), np.delete(y, chosen_idx, axis=0)
        ax.scatter(x[:, 0], x[:, 1], marker='2', c=y.argmax(axis=-1), s=self.max_dot_size, cmap=plt.cm.coolwarm)
        ax.scatter(chosen_x[0], chosen_x[1], marker='o', linewidths=2, facecolor=plt.cm.coolwarm(chosen_y[1]*255), color="black", s=self.max_dot_size)
        ax.set_title("Acquisition")
        cb = plt.colorbar(matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0, 1), cmap=plt.cm.binary), ax=[ax],location='right')
        cb.set_ticks([0, 1])
        cb.ax.tick_params(size=0)
        cb.set_ticklabels(["min", "max"])
        cb.set_label('Score', rotation=270)



    def make_plots(self, chosen_idx, args, iter, train_perf, val_perf, test_perf):
        fig, ax = plt.subplots(1, 3, figsize=(20, 5))
        self.compute_clf_grad()
        self.clf_test(ax[0], test_perf)
        self.clf_train(ax[1], train_perf, val_perf)
        self.acq_boundary(ax[2], chosen_idx)
        plt.suptitle(f"{str(args.algorithm).capitalize()} Iter:{iter} Random Seed:{args.random_seed}", fontsize="x-large")
        labeled_point = Line2D([0], [0], label='Labeled', marker='^', color='black', linestyle='')
        unlabeled_point = Line2D([0], [0], label='Unlabeled', marker='2', markersize=10, color='black', linestyle='')
        test_points = Line2D([0], [0], label='Test', marker='*', color='black', linestyle='')

        chosen_point = Line2D([0], [0], label='Next added', marker='o',  markeredgewidth=2, markersize=8, markerfacecolor='grey', markeredgecolor='black', linestyle='')
        class_0 = mpatches.Patch(color=plt.cm.coolwarm(0), label='Class B')  
        class_1 = mpatches.Patch(color=plt.cm.coolwarm(255), label='Class A')  

        legend_elements = [test_points, labeled_point, unlabeled_point, class_0, class_1, chosen_point]
        plt.figlegend(handles=legend_elements, loc='lower center', ncol=len(legend_elements), fancybox=True, shadow=True)

        path_to_store = f"results/aux/{args.dataset}/{args.algorithm}/plots/{args.random_seed}/"

        utilities.funcs.makedir(path_to_store)
        plt.savefig(path_to_store + str(iter))
        plt.close()