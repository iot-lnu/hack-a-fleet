import openai
import pandas as pd
import json
import os

# Read OpenAI API key from file
with open("OPENAIKEY.txt", "r") as file:
    api_key = file.read().strip()

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

# Load necessary data
ferry_trips_data = pd.read_csv("ferry_trips_data.csv")
with open("route_descriptions.md", "r") as file:
    route_descriptions = file.read()
with open("ferries.json", "r") as f:
    ferries = json.load(f)

# Function to query OpenAI for optimization suggestions
def query_openai(prompt, model="gpt-4", max_tokens=3000):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in transportation and ferry schedule optimization."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None

# Function to prepare the prompt for optimization
def generate_prompt(route, schedule_file, fleet, optimizations):
    try:
        schedule_df = pd.read_csv(schedule_file)
        schedule_content = schedule_df.head(10).to_csv(index=False)  # Include the top 10 rows for context
    except Exception as e:
        schedule_content = f"Error reading schedule file: {e}"

    return f"""
You are tasked with optimizing ferry schedules and fleet usage for the route '{route}'.

Route Details:
{route_descriptions}

Current Schedule (CSV format snippet):
{schedule_content}

Current Fleet:
{json.dumps(fleet, indent=2)}

Optimization Goals:
{optimizations}

Provide:
1. A detailed optimized schedule in CSV format. DO NOT SIMPLIFY IT.
2. Adjusted fleet assignments for peak and off-peak hours.
3. Feasibility analysis for proposed changes, especially ensuring demand is met and emissions are reduced.
4. Simulated amount of emissions decreased and demand being met. 
"""

# Save optimized schedules to CSV
def save_optimized_schedule(route, schedule_data):
    try:
        output_file = f"optimized_schedules/{route}_optimized_schedule.csv"
        with open(output_file, "w") as file:
            file.write(schedule_data)
        print(f"Optimized schedule saved for {route} at {output_file}.")
    except Exception as e:
        print(f"Error saving optimized schedule for {route}: {e}")

# Prepare a directory for optimized schedules
os.makedirs("optimized_schedules", exist_ok=True)

# Define routes and optimization plans
routes = {
    "Aspöleden": {
        "schedule": "schedules/aspoleden_utg11_2020_w.csv",
        "fleet": ferries.get("Yxlan"),
        "optimizations": """
Retain only Yxlan during late-night hours (10 PM–6 AM).
Schedule trips every 50 minutes instead of 25 minutes during off-peak times.
Use both ferries during peak hours to meet demand.
"""
    },
    "Oxdjupsleden": {
        "schedule": "schedules/Vaxholms-Oxdjupsleden_utg16_1_WEB_20230401.csv",
        "fleet": ferries.get("Fragancia"),
        "optimizations": """
Reduce trip frequency to every 15 minutes during late-night hours (10 PM–6 AM).
Retain Fragancia for all operations to minimize emissions.
"""
    },
    "Furusundsleden": {
        "schedule": "schedules/furusundsleden-blidoleden_utg9_200623_w.csv",
        "fleet": ferries.get("Merkurius"),
        "optimizations": """
Operate only Merkurius during winter weekdays.
Retain both Merkurius and Gulli during summer holidays and weekends.
Use Gulli for off-peak trips to reduce emissions.
"""
    },
    "Vaxholmsleden": {
        "schedule": "schedules/Vaxholms-Oxdjupsleden_utg16_1_WEB_20230401.csv",
        "fleet": ferries.get("Nina"),
        "optimizations": """
Retain only Castella during late-night hours (10 PM–6 AM).
Schedule trips every 20 minutes during late-night periods.
Use Nina and Castella during peak times to meet demand.
"""
    },
    "Ljusteröleden": {
        "schedule": "schedules/ljusteroleden_oktober_april_utg22_2020_w.csv",
        "fleet": ferries.get("Jupiter"),
        "optimizations": """
Retain both ferries during summer weekends and holidays for peak demand.
Use only Jupiter during winter weekdays to reduce emissions.
Switch to Frida during off-peak times to minimize fuel usage.
"""
    }
}

# Process each route and generate optimized schedules
for route, details in routes.items():
    print(f"Processing route: {route}")
    prompt = generate_prompt(route, details["schedule"], details["fleet"], details["optimizations"])
    result = query_openai(prompt)
    if result:
        save_optimized_schedule(route, result)
    else:
        print(f"No result for {route}.")
