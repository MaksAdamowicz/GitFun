import random
import csv
import simpn.simulator as sim
from simpn.simulator import SimToken
import numpy as np
import scipy.stats as st

def run_single_replication(rep_num, sim_minutes=480):
    """
    Encapsulates a single run of the simulation so that all variables, 
    places, and events are completely reset for each replication.
    """
    model = sim.SimProblem()

    # Variables (Places)
    arrivals = model.add_var("arrivals")
    wait_sq = model.add_var("wait_sq")
    resignation_timers = model.add_var("resignation_timers")

    desk_a = model.add_var("desk_a")
    desk_b = model.add_var("desk_b")
    desk_c = model.add_var("desk_c")
    completed = model.add_var("completed")

    # Local metrics for this specific replication
    metrics = {
        "A": {"waiting_times": [], "served": 0},
        "B": {"waiting_times": [], "served": 0},
        "C": {"waiting_times": [], "served": 0},
        "resignations": 0
    }

    # State variables tracking time locally
    sim_state = {"next_arrival_time": 0.0}
    arrival_times = {}        
    desk_available_times = {"A": 0.0, "B": 0.0, "C": 0.0}
    raw_events = []

    # --- 1. ARRIVAL EVENT ---
    def arrive(customer_id):
        arrival_times[customer_id] = sim_state["next_arrival_time"]
        
        inter_arrival = random.expovariate(1.0 / 1.3)
        sim_state["next_arrival_time"] += inter_arrival
        
        will_resign = random.random() <= 0.05
        customer = {
            "id": customer_id,
            "will_resign": will_resign,
            "is_intl": random.random() <= 0.30
        }
        
        next_customer = SimToken(customer_id + 1, delay=inter_arrival)
        
        raw_events.append({"time": arrival_times[customer_id], "type": "Arrive (Queue)", "c": customer_id})
        
        # Spawn a timer token if the customer is prone to resigning
        timer_token = SimToken(customer_id, delay=5.0) if will_resign else None
            
        return [next_customer, SimToken(customer), timer_token]

    model.add_event([arrivals], [arrivals, wait_sq, resignation_timers], arrive, name="Arrive")

    # --- 2. DYNAMIC RESIGNATION EVENT ---
    def guard_resign(customer, timer_id):
        return customer["id"] == timer_id

    def resign_dynamic(customer, timer_id):
        c_id = customer['id']
        resign_time = arrival_times[c_id] + 5.0
        metrics["resignations"] += 1
        raw_events.append({"time": resign_time, "type": "Resign (Dynamic)", "c": c_id})
        return []

    model.add_event([wait_sq, resignation_timers], [], resign_dynamic, name="Resign", guard=guard_resign)

    # --- 3. SERVICE LOGIC ---
    def process_service(customer, desk, desk_name, mean_exp=None, min_uni=None, max_uni=None):
        c_id = customer['id']
        arrival = arrival_times[c_id]
        
        start_time = max(arrival, desk_available_times[desk_name])
        wait_time = start_time - arrival
            
        metrics[desk_name]["waiting_times"].append(wait_time)
        metrics[desk_name]["served"] += 1
        
        if mean_exp: service_time = random.expovariate(1.0 / mean_exp)
        else: service_time = random.uniform(min_uni, max_uni)
            
        end_time = start_time + service_time
        desk_available_times[desk_name] = end_time
        
        raw_events.append({"time": start_time, "type": f"start_desk_{desk_name}", "c": c_id, "desk": desk_name})
        return [SimToken(customer, delay=service_time), SimToken(desk, delay=service_time)]

    def service_a(customer, desk): return process_service(customer, desk, "A", mean_exp=2.8)
    model.add_event([wait_sq, desk_a], [completed, desk_a], service_a, name="Service A")

    def service_b(customer, desk): return process_service(customer, desk, "B", min_uni=2.0, max_uni=6.0)
    model.add_event([wait_sq, desk_b], [completed, desk_b], service_b, name="Service B")

    def service_c(customer, desk): return process_service(customer, desk, "C", min_uni=1.0, max_uni=4.0)
    model.add_event([wait_sq, desk_c], [completed, desk_c], service_c, name="Service C")

    # --- 4. INITIALIZATION & EXECUTION ---
    arrivals.put(1)
    desk_a.put("Desk A")
    desk_b.put("Desk B")
    desk_c.put("Desk C")

    model.simulate(sim_minutes)

    # --- 5. CALCULATE QUEUE AVERAGES ---
    raw_events.sort(key=lambda x: (x["time"], 0 if "Arrive" in x["type"] else (1 if "start" in x["type"] else 2)))
    
    queue = []
    queue_area = 0.0
    last_time = 0.0

    for ev in raw_events:
        t = ev["time"]
        if t > sim_minutes: continue 
        
        dt = t - last_time
        queue_area += len(queue) * dt
        last_time = t

        c = ev["c"]
        etype = ev["type"]
        
        if "Arrive" in etype: queue.append(c)
        elif "start_desk" in etype:
            if c in queue: queue.remove(c)
        elif "Resign" in etype:
            if c in queue: queue.remove(c)

    # --- 6. COMPILE RESULTS FOR THIS REPLICATION ---
    total_served = metrics["A"]["served"] + metrics["B"]["served"] + metrics["C"]["served"]
    total_wait = sum(metrics["A"]["waiting_times"]) + sum(metrics["B"]["waiting_times"]) + sum(metrics["C"]["waiting_times"])
    
    overall_avg_wait = total_wait / total_served if total_served > 0 else 0
    abandonment_rate = (metrics['resignations'] / (total_served + metrics['resignations'])) * 100 if (total_served + metrics['resignations']) > 0 else 0

    return {
        "overall_avg_wait": overall_avg_wait,
        "total_resignations": metrics['resignations'],
        "abandonment_rate": abandonment_rate,
        "avg_wait_A": sum(metrics["A"]["waiting_times"]) / metrics["A"]["served"] if metrics["A"]["served"] > 0 else 0,
        "avg_wait_B": sum(metrics["B"]["waiting_times"]) / metrics["B"]["served"] if metrics["B"]["served"] > 0 else 0,
        "avg_wait_C": sum(metrics["C"]["waiting_times"]) / metrics["C"]["served"] if metrics["C"]["served"] > 0 else 0,
        "avg_q_length": queue_area / last_time if last_time > 0 else 0
    }


# ==========================================
# MAIN EXECUTION LOOP (30 REPLICATIONS)
# ==========================================
if __name__ == '__main__':
    NUM_REPLICATIONS = 30
    SIMULATION_MINUTES = 480
    
    # Dictionary to store the results of all 30 runs
    results = {
        "overall_avg_wait": [], "total_resignations": [], "abandonment_rate": [],
        "avg_wait_A": [], "avg_wait_B": [], "avg_wait_C": [], "avg_q_length": []
    }

    print(f"Running {NUM_REPLICATIONS} replications for Model 2 ({SIMULATION_MINUTES} minutes each)...")
    
    for i in range(NUM_REPLICATIONS):
        rep_res = run_single_replication(i + 1, SIMULATION_MINUTES)
        
        # Append this run's results to our tracking dictionary
        for key, value in rep_res.items():
            results[key].append(value)
            
        if (i + 1) % 5 == 0:
            print(f"Completed replication {i+1}/{NUM_REPLICATIONS}")

    print("\n=== FINAL RESULTS - MODEL 2 (30 REPLICATIONS) ===")
    
    # Function to calculate and print Mean and 95% Confidence Interval
    def print_stat(name, data):
        mean = np.mean(data)
        sem = st.sem(data)
        # Calculate 95% CI using t-distribution
        ci = st.t.interval(0.95, len(data)-1, loc=mean, scale=sem)
        # Handle cases where all values are identical (sem = 0)
        if np.isnan(ci[0]): ci = (mean, mean) 
        
        print(f"{name:.<35} Mean = {mean:>6.2f} | 95% CI = [{ci[0]:>6.2f}, {ci[1]:>6.2f}]")

    print_stat("Overall Avg Waiting Time (mins)", results["overall_avg_wait"])
    print_stat("Total Resignations (count)", results["total_resignations"])
    print_stat("Abandonment Rate (%)", results["abandonment_rate"])
    print_stat("Avg Wait - Desk A (mins)", results["avg_wait_A"])
    print_stat("Avg Wait - Desk B (mins)", results["avg_wait_B"])
    print_stat("Avg Wait - Desk C (mins)", results["avg_wait_C"])
    print_stat("Average Shared Queue Length", results["avg_q_length"])