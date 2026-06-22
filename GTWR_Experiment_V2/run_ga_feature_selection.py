import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor
import warnings
import random

warnings.filterwarnings('ignore')

print("==========================================================")
print(" GENETIC ALGORITHM FOR FEATURE SELECTION (N=212)")
print("==========================================================\n")

# Load enriched super panel
csv_path = r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\SpatioTemporal_SuperPanel_Enriched.csv"
df = pd.read_csv(csv_path).fillna(0)

# Define feature candidates (17 features)
candidate_features = [
    'Capacity_tpa', 'Coal_MW', 'Diesel_MW', 'PLN_MW', 'Gas_MW', 'Hydro_MW', 
    'GHG_Intensity', 'Mining_RpMiliar', 'Processing_RpMiliar', 'Electricity_RpMiliar', 
    'Construction_RpMiliar', 'Work_Absence', 'Child_Asthma', 'Low_Birth_Weight', 
    'Latitude', 'Longitude', 'Tahun'
]

X_df = df[candidate_features]
y = df['Agri_Loss_RpMiliar'].values

# K-Fold CV setup
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def evaluate_fitness(chromosome):
    # Selected features based on chromosome bits (1=active, 0=inactive)
    selected_cols = [candidate_features[i] for i, bit in enumerate(chromosome) if bit == 1]
    
    if len(selected_cols) == 0:
        return -999.0  # Penalize empty selection
        
    X_subset = X_df[selected_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_subset)
    
    y_pred = np.zeros(len(y))
    
    for train_idx, test_idx in kf.split(X_scaled):
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train = y[train_idx]
        
        model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred[test_idx] = model.predict(X_test)
        
    r2 = r2_score(y, y_pred)
    return r2

# GA Parameters
POP_SIZE = 15
GENS = 20
MUT_RATE = 0.1
CROSS_RATE = 0.8
ELITE_SIZE = 1

# Initialize population randomly
np.random.seed(42)
random.seed(42)
population = [np.random.randint(0, 2, len(candidate_features)).tolist() for _ in range(POP_SIZE)]

# Ensure no completely zero chromosome in initial population
for i in range(POP_SIZE):
    if sum(population[i]) == 0:
        population[i][random.randint(0, len(candidate_features)-1)] = 1

best_ever_chrom = None
best_ever_fitness = -float('inf')

print(f"[+] Memulai Optimasi GA...")
print(f"    - Ukuran Populasi: {POP_SIZE}")
print(f"    - Jumlah Generasi: {GENS}")
print(f"    - Kandidat Fitur: {len(candidate_features)} variabel\n")

for gen in range(GENS):
    # Calculate fitness for all individuals
    fitness_scores = [evaluate_fitness(chrom) for chrom in population]
    
    # Track elite
    best_idx = np.argmax(fitness_scores)
    gen_best_fitness = fitness_scores[best_idx]
    gen_best_chrom = population[best_idx]
    
    if gen_best_fitness > best_ever_fitness:
        best_ever_fitness = gen_best_fitness
        best_ever_chrom = gen_best_chrom.copy()
        
    print(f"Generasi {gen+1:02d}/{GENS:02d} | Fitness Terbaik (R2): {gen_best_fitness*100:6.2f}% | Fitur Terpilih: {sum(gen_best_chrom)}/{len(candidate_features)}")
    
    # Tournament selection
    selected_parents = []
    for _ in range(POP_SIZE):
        i1, i2 = random.randint(0, POP_SIZE-1), random.randint(0, POP_SIZE-1)
        parent = population[i1] if fitness_scores[i1] > fitness_scores[i2] else population[i2]
        selected_parents.append(parent.copy())
        
    # Crossover and Mutation
    next_gen = []
    
    # Preserve Elitism
    elites = [population[idx] for idx in np.argsort(fitness_scores)[-ELITE_SIZE:]]
    next_gen.extend([e.copy() for e in elites])
    
    # Fill the rest of the generation
    while len(next_gen) < POP_SIZE:
        p1 = random.choice(selected_parents)
        p2 = random.choice(selected_parents)
        
        # Crossover
        if random.random() < CROSS_RATE:
            cross_point = random.randint(1, len(candidate_features)-2)
            c1 = p1[:cross_point] + p2[cross_point:]
            c2 = p2[:cross_point] + p1[cross_point:]
        else:
            c1 = p1.copy()
            c2 = p2.copy()
            
        # Mutation
        for c in [c1, c2]:
            for i in range(len(c)):
                if random.random() < MUT_RATE:
                    c[i] = 1 - c[i]  # Flip bit
            
            # Avoid empty chromosome
            if sum(c) == 0:
                c[random.randint(0, len(candidate_features)-1)] = 1
                
            if len(next_gen) < POP_SIZE:
                next_gen.append(c)
                
    population = next_gen

selected_features_final = [candidate_features[i] for i, bit in enumerate(best_ever_chrom) if bit == 1]
print("\n==========================================================")
print(" OPTIMASI GA SELESAI")
print("==========================================================")
print(f" R-Squared Terbaik yang Dicapai : {best_ever_fitness*100:.2f}%")
print(f" Total Fitur Terpilih           : {len(selected_features_final)} dari {len(candidate_features)}")
print(f" Fitur Terpilih                 : {selected_features_final}")
print("==========================================================\n")

# Save selected features to a text file for ultimate showdown script
with open(r"c:\Users\msi\Documents\New folder\Nickel-Spatiotemporal-GTWR-Leontief\GTWR_Experiment_V2\selected_features.txt", "w") as f:
    f.write(",".join(selected_features_final))
