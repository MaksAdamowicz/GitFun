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
    queue_a = model.add_var("queue_a")
    queue_b = model.add_var("queue_b")
    queue_c = model.add_var("queue_c")
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
        timer_token = SimToken(customer_id, delay=5.0) if will_resign else None
        
        choice = random.random()
        if choice < 0.333:
            q_name = "A"
            tokens = [next_customer, SimToken(customer), None, None, timer_token]
        elif choice < 0.666:
            q_name = "B"
            tokens = [next_customer, None, SimToken(customer), None, timer_token]
        else:
            q_name = "C"
            tokens = [next_customer, None, None, SimToken(customer), timer_token]

        raw_events.append({"time": arrival_times[customer_id], "type": f"Arrive (Q_{q_name})", "c": customer_id, "queue": q_name})
        return tokens

    model.add_event([arrivals], [arrivals, queue_a, queue_b, queue_c, resignation_timers], arrive, name="Arrive")

    # --- 2. DYNAMIC RESIGNATION EVENTS ---
    def guard_resign(customer, timer_id):
        return customer["id"] == timer_id

    def create_resign_func(queue_name):
        def resign_dynamic(customer, timer_id):
            c_id = customer['id']
            resign_time = arrival_times[c_id] + 5.0
            metrics["resignations"] += 1
            raw_events.append({"time": resign_time, "type": f"Resign", "c": c_id})
            return []
        return resign_dynamic

    model.add_event([queue_a, resignation_timers], [], create_resign_func("A"), name="Resign A", guard=guard_resign)
    model.add_event([queue_b, resignation_timers], [], create_resign_func("B"), name="Resign B", guard=guard_resign)
    model.add_event([queue_c, resignation_timers], [], create_resign_func("C"), name="Resign C", guard=guard_resign)

    # --- 3. SWITCHING LOGIC ---
    def guard_switch_b_to_a(customer):
        len_b, len_a, len_c = len(queue_b.marking), len(queue_a.marking), len(queue_c.marking)
        return (len_b - len_a > 3) and (len_a <= len_c)

    def switch_b_to_a(customer): return [SimToken(customer)]
    model.add_event([queue_b], [queue_a], switch_b_to_a, name="Switch B to A", guard=guard_switch_b_to_a)

    def guard_switch_b_to_c(customer):
        len_b, len_a, len_c = len(queue_b.marking), len(queue_a.marking), len(queue_c.marking)
        return (len_b - len_c > 3) and (len_c < len_a)

    def switch_b_to_c(customer): return [SimToken(customer)]
    model.add_event([queue_b], [queue_c], switch_b_to_c, name="Switch B to C", guard=guard_switch_b_to_c)

    # --- 4. SERVICE LOGIC ---
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
    model.add_event([queue_a, desk_a], [completed, desk_a], service_a, name="Service A")

    def service_b(customer, desk): return process_service(customer, desk, "B", min_uni=2.0, max_uni=6.0)
    model.add_event([queue_b, desk_b], [completed, desk_b], service_b, name="Service B")

    def service_c(customer, desk): return process_service(customer, desk, "C", min_uni=1.0, max_uni=4.0)
    model.add_event([queue_c, desk_c], [completed, desk_c], service_c, name="Service C")

    # --- 5. INITIALIZATION & EXECUTION ---
    arrivals.put(1)
    desk_a.put("Desk A")
    desk_b.put("Desk B")
    desk_c.put("Desk C")

    model.simulate(sim_minutes)

    # --- 6. CALCULATE QUEUE AVERAGES ---
    raw_events.sort(key=lambda x: (x["time"], 0 if "Arrive" in x["type"] else (1 if "start" in x["type"] else 2)))
    
    queues = {"A": [], "B": [], "C": []}
    queue_areas = {"A": 0.0, "B": 0.0, "C": 0.0}
    last_time = 0.0

    for ev in raw_events:
        t = ev["time"]
        if t > sim_minutes: continue 
        
        dt = t - last_time
        queue_areas["A"] += len(queues["A"]) * dt
        queue_areas["B"] += len(queues["B"]) * dt
        queue_areas["C"] += len(queues["C"]) * dt
        last_time = t

        c = ev["c"]
        etype = ev["type"]
        
        if "Arrive" in etype: queues[ev["queue"]].append(c)
        elif "start_desk" in etype:
            for q in ["A", "B", "C"]:
                if c in queues[q]: queues[q].remove(c)
        elif "Resign" in etype:
            for q in queues.values():
                if c in q: q.remove(c)

        # Switch logic tracker
        while True:
            switched = False
            if len(queues["B"]) - len(queues["A"]) > 3 and len(queues["A"]) <= len(queues["C"]):
                queues["A"].append(queues["B"].pop(-1))
                switched = True
            elif len(queues["B"]) - len(queues["C"]) > 3 and len(queues["C"]) < len(queues["A"]):
                queues["C"].append(queues["B"].pop(-1))
                switched = True
            if not switched: break

    # --- 7. COMPILE RESULTS FOR THIS REPLICATION ---
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
        "avg_q_A": queue_areas["A"] / last_time if last_time > 0 else 0,
        "avg_q_B": queue_areas["B"] / last_time if last_time > 0 else 0,
        "avg_q_C": queue_areas["C"] / last_time if last_time > 0 else 0
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
        "avg_wait_A": [], "avg_wait_B": [], "avg_wait_C": [],
        "avg_q_A": [], "avg_q_B": [], "avg_q_C": []
    }

    print(f"Running {NUM_REPLICATIONS} replications for {SIMULATION_MINUTES} minutes each...")
    
    for i in range(NUM_REPLICATIONS):
        rep_res = run_single_replication(i + 1, SIMULATION_MINUTES)
        
        # Append this run's results to our tracking dictionary
        for key, value in rep_res.items():
            results[key].append(value)
            
        if (i + 1) % 5 == 0:
            print(f"Completed replication {i+1}/{NUM_REPLICATIONS}")

    print("\n=== FINAL RESULTS (30 REPLICATIONS) ===")
    
    # Function to calculate and print Mean and 95% Confidence Interval
    def print_stat(name, data):
        mean = np.mean(data)
        sem = st.sem(data)
        # Calculate 95% CI using t-distribution
        ci = st.t.interval(0.95, len(data)-1, loc=mean, scale=sem)
        print(f"{name:.<35} Mean = {mean:>6.2f} | 95% CI = [{ci[0]:>6.2f}, {ci[1]:>6.2f}]")

    print_stat("Overall Avg Waiting Time (mins)", results["overall_avg_wait"])
    print_stat("Total Resignations (count)", results["total_resignations"])
    print_stat("Abandonment Rate (%)", results["abandonment_rate"])
    print_stat("Avg Wait - Desk A (mins)", results["avg_wait_A"])
    print_stat("Avg Wait - Desk B (mins)", results["avg_wait_B"])
    print_stat("Avg Wait - Desk C (mins)", results["avg_wait_C"])
    print_stat("Avg Queue Length - Desk A", results["avg_q_A"])
    print_stat("Avg Queue Length - Desk B", results["avg_q_B"])
    print_stat("Avg Queue Length - Desk C", results["avg_q_C"])