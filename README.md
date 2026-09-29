# Dynamic Resource Allocation in Cloud Distribution Systems

**Aim:** Combine Deep-Learning with Online Convex Optimization (OCO) to lower operational costs while maintaining SLA Guarantees under non-stationary traffic spikes.

**Thesis:** A hybrid dynamic resource allocation framework combining predictive deep-learning schedulers for baseline demand with Online Convex Optimization for real-time drift correction achieves lower operational costs while maintaining SLA Guarantees under non-stationary traffic spikes.

**Goal Statement:** I'm interested if cloud services can be optimized using two techniques: firstly using OCO Algorithms to enhance delivery speeds and minimize overhead latency. The other technique is using deep learning schedulers to potentially improve dynamic resource allocation based on a predictive model using usage data. Lastly, testing the combination of the two and attempting to create an improved backend for cloud servers while identifying the positives and negatives of this approach.

---

## Tech Stack

* **ML / Optimization:** PyTorch, NumPy, SciPy
* **Cloud & Containers:** Docker, NGINX, FastAPI, Prometheus, Grafana
* **Traffic Testing:** Custom Python async traffic generator

---

## Project One: Predictive-Dynamic Micro-Load Balancer

**Introduction:** This starter project isolates the core hybrid architecture—a predictive model handling baseline demand paired with a real-time reactive feedback loop. It avoids cloud infrastructure bills while merging concepts from machine learning, cloud API operations, and dynamic optimization.

**Time Frame:** 3–5 Weeks

### Phase 1: Workload Generator & Local Cluster
* **Goal:** Set up a minimal, inspectable backend environment using Docker and Python.
* **Hardware:** Local Docker Desktop.
* **Service Architecture:** Deploy FastAPI app running behind 1 to 10 container instances.
* **Traffic Generator:** Use a Python script to simulate incoming requests per second (RPS), combining a predictable sine wave pattern (representing daily cyclic traffic) with random noise (variation within traffic) and sudden spikes (unpredictable surges).
* *Note:* This phase will prepare data for the predictive scheduler used during the next phase and set up the local environment/VM to contain our scripts and data, allowing for accurate measurements of our metrics.

### Phase 2: Predictive Baseline Scheduler
* **Introduction:** Build a predictive engine to allocate container capacity in advance based on historical usage pattern learning.
* **Model Architecture:** Build a light PyTorch LSTM (Long Short-Term Memory) or GRU (Gated Recurrent Unit) Model.
* **Input Data:** Time series sequence of past RPS and CPU utilization metrics (collected during Phase 1) following $t_{-n} \dots t_{0}$.
* **Output:** Predicted demand for the next time window $(t_{+1} \dots t_{+10})$, mapped directly to target container scale count:
  $$\text{baseline Containers} = \left\lceil \frac{\text{predicted RPS}}{\text{capacity per container}} \right\rceil$$

### Phase 3: Real-Time Drift Correction Engine (OCO)
Implementation of Online Convex Optimization to correct the baseline scheduler's prediction errors instantly.

* **Algorithm:** Implement OGD (Online Gradient Descent) to adjust resource allocations dynamically:
  $$x_{t+1} = \Pi_{x}(x_{t} - \eta \nabla f_{t}(x_{t}))$$
* **Loss Function $f_{t}(x_{t})$:** Define a convex cost function balancing SLA penalty and resource overhead:
 ```math
  f_{t}(x_{t}) = C_{\text{sla}} \cdot \max(0, \text{Latency}_{t} - \text{SLA}_{\text{tar}}) + C_{\text{resource}} \cdot x_{t}
  ```

  *Where $x_{t}$ represents added capacity and $\eta$ is the learning rate.*
* **Execution:** Run the OGD loop every second. If actual traffic exceeds the LSTM prediction, OGD quickly scales up resources before SLA violations compound.

### Phase 4: Hybrid Integration & Metrics Benchmarking
Combine both modules into a unified controller and run comparative experiments against baseline strategies.

| Metric | Reactive-Only | Predictive-Only | OCO-Only | Hybrid Framework |
| :--- | :---: | :---: | :---: | :---: |
| **SLA Violations (%)** | | | | |
| **Resource Waste (Over-Provisioning)** | | | | |
| **Response Latency** | | | | |
