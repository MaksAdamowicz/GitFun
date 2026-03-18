import random
import csv
import simpn.simulator as sim
from simpn.simulator import SimToken

# ==========================================
# 1. Initialize Model 1 (Three Queues)
# ==========================================
model = sim.SimProblem()

arrivals = model.add_var("arrivals")
queue_a = model.add_var("queue_a")
queue_b = model.add_var("queue_b")
queue_c = model.add_var("queue_c")

desk_a = model.add_var("desk_a")
desk_b = model.add_var("desk_b")
desk_c = model.add_var("desk_c")
completed = model.add_var("completed")

metrics = {
    "A": {"waiting_times": [], "served": 0},
    "B": {"waiting_times": [], "served": 0},
    "C": {"waiting_times": [], "served": 0},
    "resignations": 0
}

arrival_times = {}        
next_arrival_time = 0.0   

desk_available_times = {  
    "A": 0.0,
    "B": 0.0,
    "C": 0.0
}

raw_events = []

# ==========================================
# 2. Arrival Logic
# ==========================================
def arrive(customer_id):
    global next_arrival_time
    arrival_times[customer_id] = next_arrival_time
    
    inter_arrival = random.expovariate(1.0 / 1.3)
    next_arrival_time += inter_arrival
    
    customer = {
        "id": customer_id,
        "will_resign": random.random() <= 0.05,
        "is_intl": random.random() <= 0.30
    }
    
    next_customer = SimToken(customer_id + 1, delay=inter_arrival)
    
    choice = random.random()
    if choice < 0.333:
        q_name = "A"
        tokens = [next_customer, SimToken(customer), None, None]
    elif choice < 0.666:
        q_name = "B"
        tokens = [next_customer, None, SimToken(customer), None]
    else:
        q_name = "C"
        tokens = [next_customer, None, None, SimToken(customer)]

    raw_events.append({
        "time": arrival_times[customer_id], 
        "type": f"Arrive (Q_{q_name})", 
        "c": customer_id,
        "queue": q_name
    })
        
    return tokens

model.add_event([arrivals], [arrivals, queue_a, queue_b, queue_c], arrive, name="Arrive")

# ==========================================
# 3. Service & Resignation Logic
# ==========================================
def process_service(customer, desk, desk_name, mean_exp=None, min_uni=None, max_uni=None):
    global desk_available_times
    c_id = customer['id']
    arrival = arrival_times[c_id]
    
    start_time = max(arrival, desk_available_times[desk_name])
    wait_time = start_time - arrival
    
    if wait_time > 5.0 and customer['will_resign']:
        metrics["resignations"] += 1
        raw_events.append({"time": arrival + 5.0, "type": f"Resign (Q_{desk_name})", "c": c_id})
        return [SimToken(customer, delay=0), SimToken(desk, delay=0)]
        
    metrics[desk_name]["waiting_times"].append(wait_time)
    metrics[desk_name]["served"] += 1
    
    if mean_exp:
        service_time = random.expovariate(1.0 / mean_exp)
    else:
        service_time = random.uniform(min_uni, max_uni)
        
    end_time = start_time + service_time
    desk_available_times[desk_name] = end_time
    
    raw_events.append({
        "time": start_time, 
        "type": f"start_desk_{desk_name}", 
        "c": c_id, 
        "desk": desk_name, 
        "end_time": end_time, 
        "wait_time": wait_time
    })
    
    raw_events.append({
        "time": end_time, 
        "type": "leave", 
        "c": c_id, 
        "desk": desk_name
    })
    
    return [SimToken(customer, delay=service_time), SimToken(desk, delay=service_time)]

def service_a(customer, desk):
    return process_service(customer, desk, "A", mean_exp=2.8)
model.add_event([queue_a, desk_a], [completed, desk_a], service_a, name="Service A")

def service_b(customer, desk):
    return process_service(customer, desk, "B", min_uni=2.0, max_uni=6.0)
model.add_event([queue_b, desk_b], [completed, desk_b], service_b, name="Service B")

def service_c(customer, desk):
    return process_service(customer, desk, "C", min_uni=1.0, max_uni=4.0)
model.add_event([queue_c, desk_c], [completed, desk_c], service_c, name="Service C")

# ==========================================
# 4. Jockeying Guards (Simulation Engine)
# ==========================================
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

# ==========================================
# 5. CSV Generator (State Reconstructor)
# ==========================================
def generate_csv_trace(filename="model1_trace.csv"):
    
    raw_events.sort(key=lambda x: (x["time"], 0 if "Arrive" in x["type"] else (1 if "start" in x["type"] else 2)))
    
    queues = {"A": [], "B": [], "C": []}
    desks = {"A": None, "B": None, "C": None}
    leave_list = []
    gone_list = []
    
    csv_rows = [["now.Time", "c", "Transition", "WaitA", "WaitB", "WaitC", "DeskA", "DeskB", "DeskC", "c.WaitTime", "leave", "Gone"]]
    
    for ev in raw_events:
        t = ev["time"]
        if t > 480: continue 
        
        c = ev["c"]
        etype = ev["type"]
        c_wait = ""
        
        if "Arrive" in etype:
            queues[ev["queue"]].append(c)
        elif "start_desk" in etype:
            d = ev["desk"]
            if c in queues[d]: queues[d].remove(c)
            desks[d] = f"(c{c}, End={ev['end_time']:.1f})"
            c_wait = f"{ev['wait_time']:.2f}"
        elif etype == "leave":
            d = ev["desk"]
            desks[d] = None
            leave_list.append(c)
        elif "Resign" in etype:
            for q in queues.values():
                if c in q: q.remove(c)
            gone_list.append(c)

        switch_event = None
        if len(queues["B"]) - len(queues["A"]) > 3 and len(queues["A"]) <= len(queues["C"]):
            switched_c = queues["B"].pop(-1)
            queues["A"].append(switched_c)
            switch_event = f"Switch B->A (c{switched_c})"
        elif len(queues["B"]) - len(queues["C"]) > 3 and len(queues["C"]) < len(queues["A"]):
            switched_c = queues["B"].pop(-1)
            queues["C"].append(switched_c)
            switch_event = f"Switch B->C (c{switched_c})"

        q_strs = [f"[{', '.join(['c'+str(x) for x in queues[q]])}]" if queues[q] else "[]" for q in ["A", "B", "C"]]
        d_strs = [desks[d] if desks[d] else "Free" for d in ["A", "B", "C"]]
        
        csv_rows.append([
            f"{t:.2f}", f"c{c}", etype, q_strs[0], q_strs[1], q_strs[2], d_strs[0], d_strs[1], d_strs[2], 
            c_wait, ", ".join([f"c{x}" for x in leave_list]), ", ".join([f"c{x}" for x in gone_list])
        ])
                
        if switch_event:
            q_strs = [f"[{', '.join(['c'+str(x) for x in queues[q]])}]" if queues[q] else "[]" for q in ["A", "B", "C"]]
            csv_rows.append([
                f"{t:.2f}", f"c{switched_c}", switch_event, q_strs[0], q_strs[1], q_strs[2], d_strs[0], d_strs[1], d_strs[2], 
                "", "", ""
            ])
        leave_list.clear()
        gone_list.clear()

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_rows)
    print(f"\n[+] CSV trace successfully saved to '{filename}'!")

# ==========================================
# 6. Execution
# ==========================================
arrivals.put(1)
desk_a.put("Desk A")
desk_b.put("Desk B")
desk_c.put("Desk C")

if __name__ == '__main__':
    SIMULATION_MINUTES = 480
    model.simulate(SIMULATION_MINUTES)
    
    generate_csv_trace("model1_trace.csv")
    
    print(f"\n--- Model 1 (Three Queues) Performance ({SIMULATION_MINUTES} mins) ---")
    
    total_served = 0
    total_wait = 0.0
    
    for d in ["A", "B", "C"]:
        waits = metrics[d]["waiting_times"]
        served = metrics[d]["served"]
        avg_wait = sum(waits) / len(waits) if served > 0 else 0
        total_served += served
        total_wait += sum(waits)
        
        print(f"Desk {d} | Served: {served} | Avg Waiting Time: {avg_wait:.2f} mins")
    
    overall_avg = total_wait / total_served if total_served > 0 else 0
    abandonment_rate = (metrics['resignations'] / (total_served + metrics['resignations'])) * 100 if total_served > 0 else 0
    
    print("\n--- Key Performance Indicators ---")
    print(f"Overall Average Waiting Time: {overall_avg:.2f} mins")
    print(f"Total Resignations: {metrics['resignations']}")
    print(f"Abandonment Rate: {abandonment_rate:.2f}%")