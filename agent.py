import ollama
from memory import AgentMemory
import termcolor
import random

class GenerativeAgent:
    def __init__(self, name, age, traits, status, environment, model="phi3"):
        self.name = name
        self.age = age
        self.traits = traits
        self.status = status
        self.environment = environment
        self.model = model
        self.memory = AgentMemory(name)

    def generate_response(self, prompt):
        response = ollama.generate(model=self.model, prompt=prompt)
        return response['response']

    def propose(self, topic):
        memories = self.get_relevant_memories(topic)
        memories_str = "\n".join(memories)
        prompt = f"You are {self.name}, a {self.age}-year-old {self.traits}. Your current status is: {self.status}. The current environment is: {self.environment}. There are some relevant memories: {memories_str}. Based on your knowledge and experience, propose an idea for the topic: {topic}. Respond in 3-4 sentences."
        response = self.generate_response(prompt)
        print(termcolor.colored(f"{self.name}: ", "cyan") + termcolor.colored(response, "yellow"))
        
        # Add memory of the proposal
        self.add_memory(f"I proposed an idea about '{topic}' in the environment '{self.environment}': {response}")
        
        return response

    def vote(self, proposals, max_attempts=3):
        for attempt in range(max_attempts):
            memories = self.get_relevant_memories(proposals)
            memories_str = "\n".join(memories)
            prompt = f"You are {self.name}, a {self.age}-year-old {self.traits}. Your current status is: {self.status}. The current environment is: {self.environment}. There are some relevant memories: {memories_str}. Given these proposals:\n" + "\n".join([f"{i+1}. {p}" for i, p in enumerate(proposals)]) + "\nWhich proposal do you vote for? Your response MUST start with the number of your chosen proposal, followed by a brief explanation in 1-2 sentences."
            response = self.generate_response(prompt)
            print(termcolor.colored(f"{self.name}'s vote (attempt {attempt+1}): ", "cyan") + termcolor.colored(response, "yellow"))
            
            # Find the first digit in the response
            vote = next((char for char in response if char.isdigit()), None)
            
            if vote is not None:
                vote = int(vote)
                if 1 <= vote <= len(proposals):
                    # Add memory of the vote and proposals
                    self.add_memory(f"I voted for proposal {vote} in the environment '{self.environment}'. The proposals were: {'; '.join(proposals)}")
                    return vote
                else:
                    print(f"Invalid vote number. Retrying... (Attempt {attempt+1}/{max_attempts})")
            else:
                print(f"No vote number found. Retrying... (Attempt {attempt+1}/{max_attempts})")
        
        # If all attempts fail, return a random vote
        random_vote = random.randint(1, len(proposals))
        print(f"Failed to get a valid vote after {max_attempts} attempts. Randomly selecting proposal {random_vote}.")
        self.add_memory(f"I failed to vote properly and a random vote for proposal {random_vote} was cast in the environment '{self.environment}'. The proposals were: {'; '.join(proposals)}")
        return random_vote

    def add_memory(self, memory):
        self.memory.add(memory)

    def get_relevant_memories(self, query):
        return self.memory.search(query)
