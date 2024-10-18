import json
from agent import GenerativeAgent
import os

def load_agents(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    agents = []
    for agent_data in data['agents']:
        agent = GenerativeAgent(
            name=agent_data['name'],
            age=agent_data['age'],
            traits=agent_data['traits'],
            status=agent_data['status'],
            environment=data['environment']
        )
        for memory in agent_data['initial_memory']:
            agent.add_memory(memory)
        agents.append(agent)
    
    return agents, data['original_topic'], data['total_round'], data['environment']

def save_results(file_path, results):
    try:
        # Check if the file exists
        if os.path.exists(file_path):
            # File exists, open it in read-write mode
            with open(file_path, 'r+') as f:
                data = json.load(f)
                data['runtime'] = results
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        else:
            # File doesn't exist, create it with the results
            with open(file_path, 'w') as f:
                data = {'runtime': results}
                json.dump(data, f, indent=4)
        print(f"Results saved successfully to {file_path}")
    except IOError as e:
        print(f"Error saving results to {file_path}: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {file_path}: {e}")
