import ollama
from memory import AgentMemory
import termcolor

class GenerativeAgent:
    def __init__(self, name, age, traits, status, model="phi3"):
        self.name = name
        self.age = age
        self.traits = traits
        self.status = status
        self.model = model
        self.memory = AgentMemory(name)

    def generate_response(self, prompt):
        response = ollama.generate(model=self.model, prompt=prompt)
        return response['response']

    def propose(self, topic):
        memories = self.get_relevant_memories(topic)
        memories_str = "\n".join(memories)
        prompt = f"You are {self.name}, a {self.age}-year-old {self.traits}. Your current status is: {self.status}. There are some relevant memories: {memories_str}. Based on your knowledge and experience, propose an idea for the topic: {topic}. Respond in 3-4 sentences."
        response = self.generate_response(prompt)
        print(termcolor.colored(f"{self.name}: ", "cyan") + termcolor.colored(response, "yellow"))
        
        # Add memory of the proposal
        self.add_memory(f"I proposed an idea about '{topic}': {response}")
        
        return response

    def vote(self, proposals):
        memories = self.get_relevant_memories(proposals)
        memories_str = "\n".join(memories)
        prompt = f"You are {self.name}, a {self.age}-year-old {self.traits}. Your current status is: {self.status}.There are some relevant memories: {memories_str}. Given these proposals:\n" + "\n".join([f"{i+1}. {p}" for i, p in enumerate(proposals)]) + "\nWhich proposal do you vote for? I want your response one number then explain 1-2 short sentence in folloing paragraph."
        response = self.generate_response(prompt)
        print(termcolor.colored(f"{self.name}'s vote: ", "cyan") + termcolor.colored(response, "yellow"))
        
        # Find the only one digit number first occurred in the response
        vote = next(filter(str.isdigit, response))
        
        # Add memory of the vote and proposals
        self.add_memory(f"I voted for proposal {vote}. The proposals were: {'; '.join(proposals)}")
        
        return int(vote)

    def add_memory(self, memory):
        self.memory.add(memory)

    def get_relevant_memories(self, query):
        return self.memory.search(query)
