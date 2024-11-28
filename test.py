import openai
import pandas as pd
import json
import os

# Read OpenAI API key from file
with open("OPENAIKEY.txt", "r") as file:
    api_key = file.read().strip()

# Initialize the OpenAI client with the API key
client = openai.OpenAI(api_key=api_key)

# Load necessary data
ferry_trips_data = pd.read_csv("ferry_trips_data.csv")
with open("route_descriptions.md", "r") as file:
    route_descriptions = file.read()
with open("ferries.json", "r") as f:
    ferries = json.load(f)

# Function to query OpenAI for optimization suggestions
def query_openai(prompt, model="gpt-4", max_tokens=500):
    try:
        # Create a chat completion request
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in transportation and ferry optimization."},
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
def generate_prompt(route, schedule_file, fleet):
    # Read the current schedule CSV content
    try:
        schedule_df = pd.read_csv(schedule_file)
        schedule_content = schedule_df.to_csv(index=False)
    except Exception as e:
        schedule_content = f"Error reading schedule file: {e}"
    
    return f"""
Optimize ferry operations for the route {route}.
Route Details:
{route_descriptions}

Current Schedule (CSV format):
{schedule_content}

Current Fleet:
{json.dumps(fleet, indent=2)}

Goals:
1. Reduce emissions.
2. Meet demand efficiently.
3. Avoid unmet demand during peak hours.
4. Minimize underutilized trips during off-peak hours.

Provide:
1. Optimized schedules in CSV format.
2. Fleet allocation adjustments.
"""

# Generate prompts for each route
routes = {
    "Aspöleden": {
        "schedule": "schedules/aspoleden_utg11_2020_w.csv",
        "fleet": ferries.get("Yxlan"),
    },
    "Oxdjupsleden": {
        "schedule": "schedules/Vaxholms-Oxdjupsleden_utg16_1_WEB_20230401.csv",
        "fleet": ferries.get("Fragancia"),
    },
    "Furusundsleden": {
        "schedule": "schedules/furusundsleden-blidoleden_utg9_200623_w.csv",
        "fleet": ferries.get("Merkurius"),
    },
    "Vaxholmsleden": {
        "schedule": "schedules/Vaxholms-Oxdjupsleden_utg16_1_WEB_20230401.csv",
        "fleet": ferries.get("Nina"),
    },
    "Ljusteröleden": {
        "schedule": "schedules/ljusteroleden_oktober_april_utg22_2020_w.csv",
        "fleet": ferries.get("Jupiter"),
    }
}

# Create a directory for optimized schedules
os.makedirs("optimized_schedules", exist_ok=True)

# Analyze and generate optimized outputs
for route, details in routes.items():
    prompt = generate_prompt(route, details["schedule"], details["fleet"])
    print(f"Querying OpenAI for {route} optimization...")
    result = query_openai(prompt)
    if result:
        # Save the optimized schedule to a CSV file
        output_file = f"optimized_schedules/{route}_optimized_schedule.csv"
        try:
            with open(output_file, "w") as file:
                file.write(result)
            print(f"Optimization Result for {route} saved to {output_file}.\n")
        except Exception as e:
            print(f"Error saving optimized schedule for {route}: {e}\n")
    else:
        print(f"No result for {route}.\n")

print("All optimizations completed. Optimized schedules saved in the 'optimized_schedules' directory.")
