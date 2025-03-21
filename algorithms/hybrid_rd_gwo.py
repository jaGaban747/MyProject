from config import ALPHA, BANDWIDTH, GAMMA, NUM_EDGE_NODES, NUM_TASKS, POP_SIZE
import numpy as np
from .base_gwo import BaseGWO

class HybridRDGWO(BaseGWO):
    def __init__(self, tasks, edge_nodes):
        super().__init__(tasks, edge_nodes)
        self.strategy_probs = np.full((NUM_TASKS, NUM_EDGE_NODES), 1 / NUM_EDGE_NODES)
        
    def _update_strategies(self):
        fitness = np.zeros((NUM_TASKS, NUM_EDGE_NODES))
        for i in range(NUM_TASKS):
            for j in range(NUM_EDGE_NODES):
                fitness[i, j] = self._compute_utility(i, j)
        avg_fitness = np.sum(self.strategy_probs * fitness, axis=1, keepdims=True)
        self.strategy_probs *= fitness / avg_fitness
        
    def _compute_utility(self, task_idx, node_idx):
        task = self.tasks[task_idx]
        node = self.edge_nodes[node_idx]
        proc_time = task['cpu'] / node['cpu_cap']
        tx_time = (task['data'] / BANDWIDTH) * np.linalg.norm(node['loc'] - task['loc'])
        return -ALPHA * (proc_time + tx_time) - GAMMA * node['energy_cost'] * task['cpu']
    
    def _compute_fitness(self, solution):
        base_fitness = super()._compute_base_fitness(solution)
        strategy_penalty = 0
        for task_idx, node_idx in enumerate(solution):
            chosen_prob = self.strategy_probs[task_idx, node_idx]
            strategy_penalty += -np.log(chosen_prob + 1e-10)
        return base_fitness / (1 + strategy_penalty / NUM_TASKS)
    
    def optimize(self):
        # Initialize population using Replicator Dynamics
        for _ in range(10):  # Warm-up iterations
            self._update_strategies()
        for i in range(POP_SIZE):
            self.population[i] = [np.random.choice(NUM_EDGE_NODES, p=self.strategy_probs[task_idx]) 
                                  for task_idx in range(NUM_TASKS)]
        return super().optimize()