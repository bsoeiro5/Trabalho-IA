import time
import csv
import os
from datetime import datetime

class GameMetrics:
    def __init__(self):
        self.reset()
        self.metrics_file = f"dameo_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_file = None
        self.csv_writer = None
        self._initialize_file()
        
    def reset(self):
        # Métricas gerais
        self.game_id = 0
        self.algorithm = ""
        self.difficulty = ""
        self.execution_time = 0
        self.start_time = 0
        self.nodes_expanded = 0
        self.simulations_run = 0
        self.evaluation_score = 0
        self.moves_considered = 0
        self.depth = 0
        
        # Contadores de peças
        self.green_pieces_start = 0
        self.orange_pieces_start = 0
        self.green_pieces_end = 0
        self.orange_pieces_end = 0

        self.nodes_pruned = 0
        self.max_depth_reached = 0
        self.sequential_captures = 0
        self.initial_heuristic = 0
        self.final_heuristic = 0
        self.memory_usage = 0
        self.branching_factor = 0
        
    def _initialize_file(self):
        header = [
            "game_id", "algorithm", "difficulty", "move_number", 
            "execution_time_ms", "nodes_expanded", "nodes_pruned",
            "max_depth_reached", "sequential_captures",
            "initial_heuristic", "final_heuristic",
            "simulations_run", "evaluation_score", "moves_considered", 
            "depth", "branching_factor", "memory_usage",
            "green_pieces", "orange_pieces", "total_game_time"
        ]
        
        self.csv_file = open(self.metrics_file, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(header)
                
    def start_move_timer(self):
        self.start_time = time.time()
        
    def stop_move_timer(self):
        self.execution_time = (time.time() - self.start_time) * 1000  # Convert to milliseconds
        
    def record_move_metrics(self, move_number, total_game_time=0):
        self.csv_writer.writerow([
            self.game_id,
            self.algorithm,
            self.difficulty,
            move_number,
            round(self.execution_time, 2),
            self.nodes_expanded,
            self.nodes_pruned,
            self.max_depth_reached,
            self.sequential_captures,
            self.initial_heuristic,
            self.final_heuristic,
            self.simulations_run,
            self.evaluation_score,
            self.moves_considered,
            self.depth,
            self.branching_factor,
            self.memory_usage,
            self.green_pieces_end,
            self.orange_pieces_end,
            round(total_game_time, 2)
        ])
        self.csv_file.flush()  # Força a escrita no arquivo
            
    def set_algorithm_info(self, algorithm, difficulty, depth=0):
        self.algorithm = algorithm
        self.difficulty = difficulty
        self.depth = depth
        
    def update_piece_count(self, green_pieces, orange_pieces):
        self.green_pieces_end = green_pieces
        self.orange_pieces_end = orange_pieces
        
    def set_alphabeta_metrics(self, nodes_expanded, nodes_pruned, max_depth, initial_heuristic, final_heuristic):
        self.nodes_expanded = nodes_expanded
        self.nodes_pruned = nodes_pruned
        self.max_depth_reached = max_depth
        self.initial_heuristic = initial_heuristic
        self.final_heuristic = final_heuristic
        
    def print_move_summary(self, move_number):
        print(f"\n--- Métricas do Movimento {move_number} ---")
        print(f"Algoritmo: {self.algorithm} (Dificuldade: {self.difficulty})")
        print(f"Tempo de execução: {self.execution_time:.2f} ms")
        print(f"Nós expandidos: {self.nodes_expanded}")
        if self.algorithm.lower() == "mcts":
            print(f"Simulações executadas: {self.simulations_run}")
        print(f"Avaliação final: {self.evaluation_score}")
        print(f"Peças verdes: {self.green_pieces_end}")
        print(f"Peças laranjas: {self.orange_pieces_end}")
        print("--------------------------------\n")

    def __del__(self):
        """Destructor to ensure file is closed"""
        if self.csv_file:
            self.csv_file.close()

# Instância global para uso em todo o jogo
metrics = GameMetrics()