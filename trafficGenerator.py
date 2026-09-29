import asyncio
import aiohttp
import random
import math
import csv
import time
from datetime import datetime
from statistics import mean

# ======================================================
# Configuration
# ======================================================

# Target URLs for the traffic generator
TARGET_URLS = [
    "http://localhost:8001/process",
    "http://localhost:8002/process",
    "http://localhost:8003/process",
]


INTERVAL_SECONDS = 1 # Time interval between traffic bursts in seconds
SIMULATION_DURATION = 3600 # Total duration of the simulation in seconds (1 hour)

BASE_RPS = 50 # Base requests per second
AMPLITUDE = 30 # Amplitude of the sine wave for traffic variation
PERIOD_SECONDS = 300 # Period of the sine wave in seconds (5 minutes)

NOISE_RANGE = 5 # Range for random noise added to the traffic

SPIKE_PROBABILITY = 0.03 # Probability of a traffic spike occurring
SPIKE_MIN = 100 # Minimum additional requests for a spike
SPIKE_MAX = 400 # Maximum additional requests for a spike

# CSV file to log metrics
CSV_FILE = "traffic_metrics.csv"


# ======================================================
# Traffic Model
# ======================================================

# This class generates a dynamic requests per second (RPS) value based on a sine wave pattern, random noise, and occasional spikes to simulate realistic traffic patterns.
class TrafficModel:

    # Initialize the TrafficModel with the current time to track elapsed time for generating RPS.
    def __init__(self):
        self.start_time = time.time() # Store the start time to calculate elapsed time for traffic generation.

    # Generate the current requests per second (RPS) based on a sine wave, random noise, and occasional spikes.
    def generate_rps(self):

        elapsed = time.time() - self.start_time # Calculate the elapsed time since the start of the simulation.

        # Calculate the sine wave component of the RPS based on the elapsed time, amplitude, and period.
        sine_component = (
            AMPLITUDE *
            math.sin(
                2 * math.pi * elapsed / PERIOD_SECONDS
            )
        )

        # Generate random noise within the specified range to add variability to the RPS.
        noise = random.randint(
            -NOISE_RANGE,
            NOISE_RANGE
        )

        # Initialize spike to 0; it will be set to a random value if a spike occurs.
        spike = 0

        # Determine if a spike should occur based on the defined probability.
        if random.random() < SPIKE_PROBABILITY:
            spike = random.randint(
                SPIKE_MIN,
                SPIKE_MAX
            )

        # Calculate the final RPS by combining the base RPS, sine component, noise, and any spike.
        rps = BASE_RPS + sine_component + noise + spike

        return max(1, int(rps))


# ======================================================
# Metrics Collector
# ======================================================

# This class collects and summarizes metrics for the traffic generator, including latencies, successes, and failures.
class MetricsCollector:

    # Initialize the MetricsCollector with empty lists for latencies and counters for successes and failures.
    def __init__(self):

        self.latencies = []
        self.successes = 0
        self.failures = 0

    # Record a successful request with its latency.
    def record_success(self, latency):

        self.latencies.append(latency)
        self.successes += 1

    # Record a failed request.
    def record_failure(self):

        self.failures += 1

    # Summarize the collected metrics, calculating average latency and success rate.
    def summarize(self):

        # Calculate the average latency in milliseconds, handling the case where there are no latencies recorded.
        avg_latency = (
            mean(self.latencies)
            if self.latencies
            else 0
        )

        # Calculate the total number of requests (successes + failures).
        total = self.successes + self.failures

        # Calculate the success rate as a percentage, handling the case where there are no requests.
        success_rate = (
            self.successes / total * 100
            if total
            else 0
        )

        # Return a dictionary containing the summarized metrics, rounded to two decimal places for readability.
        return {
            "average_latency_ms": round(avg_latency, 2),
            "success_rate": round(success_rate, 2),
            "successful_requests": self.successes,
            "failed_requests": self.failures
        }


# ======================================================
# Request Sender
# ======================================================

# This asynchronous function sends an HTTP GET request to the specified URL using the provided session and records the result in the metrics collector.
async def send_request(session, url, metrics):

    start = time.perf_counter()

    try:

        async with session.get(url) as response:

            await response.text()

            latency = (
                time.perf_counter() - start
            ) * 1000

            if response.status == 200:
                metrics.record_success(latency)
            else:
                metrics.record_failure()

    except Exception:
        metrics.record_failure()


# ======================================================
# Generate Traffic Burst
# ======================================================

# This asynchronous function generates a burst of traffic by sending multiple requests concurrently based on the specified requests per second (RPS).
async def generate_load(rps):

    # Create a new instance of MetricsCollector to track the metrics for this burst of traffic.
    metrics = MetricsCollector()

    # Use an asynchronous context manager to create a new aiohttp ClientSession for sending HTTP requests.
    async with aiohttp.ClientSession() as session:

        tasks = []
        # Loop through the number of requests to be sent in this burst, creating a task for each request.
        for i in range(rps):

            # Select a target URL from the list of TARGET_URLS in a round-robin fashion based on the current index.
            url = TARGET_URLS[
                i % len(TARGET_URLS)
            ]

            # Create a task to send the request and append it to the list of tasks to be executed concurrently.
            tasks.append(
                send_request(
                    session,
                    url,
                    metrics
                )
            )
        # Use asyncio.gather to run all the tasks concurrently and wait for their completion, allowing for efficient handling of multiple requests.
        await asyncio.gather(*tasks)

    return metrics


# ======================================================
# CSV Logging
# ======================================================

# This function initializes the CSV file for logging metrics by writing the header row with the appropriate column names.
def initialize_csv():

    # Open the CSV file in write mode, creating it if it doesn't exist, and prepare to write the header row.
    with open(
        CSV_FILE,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file) # Create a CSV writer object to write rows to the file.

        # Write the header row to the CSV file, specifying the column names for the logged metrics.
        writer.writerow([
            "timestamp",
            "target_rps",
            "average_latency_ms",
            "success_rate",
            "successful_requests",
            "failed_requests"
        ])

# This function logs the metrics for a given requests per second (RPS) value and its corresponding summary to the CSV file.
def log_metrics(rps, summary):

    with open(
        CSV_FILE,
        "a",
        newline=""
    ) as file:
        # Create a CSV writer object to append rows to the file.
        writer = csv.writer(file)

        # Write a new row to the CSV file with the current timestamp, target RPS, average latency, success rate, and counts of successful and failed requests.
        writer.writerow([
            datetime.now().isoformat(),
            rps,
            summary["average_latency_ms"],
            summary["success_rate"],
            summary["successful_requests"],
            summary["failed_requests"]
        ])


# ======================================================
# Main Loop
# ======================================================

# This asynchronous function runs the main simulation loop, generating traffic bursts, collecting metrics, and logging them to a CSV file for the specified duration.
async def run_simulation():

    initialize_csv() # Initialize the CSV file for logging metrics before starting the simulation.

    model = TrafficModel() # Create an instance of the TrafficModel to generate dynamic RPS values based on the defined traffic pattern.

    start_time = time.time() # Record the start time of the simulation to track elapsed time and determine when to stop the simulation.

    # Enter the main simulation loop, which will continue running until the specified simulation duration is reached.
    while True:
        # Calculate the elapsed time since the start of the simulation to determine if the simulation should continue or stop.
        elapsed = (
            time.time() - start_time
        )
        # Check if the elapsed time has exceeded the defined simulation duration, and if so, break out of the loop to end the simulation.
        if elapsed > SIMULATION_DURATION:
            break

        rps = model.generate_rps() # Generate the current requests per second (RPS) value based on the traffic model, which incorporates a sine wave pattern, random noise, and occasional spikes.

        metrics = await generate_load(rps) # Generate a burst of traffic by sending the specified number of requests concurrently and collect the resulting metrics.

        summary = metrics.summarize() # Summarize the collected metrics, calculating average latency, success rate, and counts of successful and failed requests.

        log_metrics(rps, summary) # Log the summarized metrics to the CSV file for later analysis and record-keeping.

        print(
            f"RPS={rps} | "
            f"Latency={summary['average_latency_ms']}ms | "
            f"Success={summary['success_rate']}%"
        )

        await asyncio.sleep(
            INTERVAL_SECONDS
        )

    print("Simulation Complete")


# ======================================================
# Entry Point
# ======================================================

# This block checks if the script is being run directly (as opposed to being imported as a module) and starts the simulation by running the asynchronous run_simulation function using asyncio.
if __name__ == "__main__":
    asyncio.run(run_simulation())