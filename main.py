import asyncio
import json
from enum import Enum
from termcolor import colored
from utils import load_agents, save_results
from collections import deque

class RoundState(Enum):
    WAITING = 0
    RUNNING = 1
    FINISHED = 2
    CHATINROUND = 3
    ADDMEMORY = 4

class RoundTableChat:
    def __init__(self, agents, topic, total_rounds):
        self.agents = agents
        self.topic = topic
        self.total_rounds = total_rounds
        self.current_round = 0
        self.results = []
        self.command_queue = deque()
        self.state = RoundState.WAITING

    async def process_commands(self):
        while self.command_queue:
            command = self.command_queue.popleft()
            if command['command'] == 'start':
                self.state = RoundState.RUNNING
                await self.run_round()
            elif command['command'] == 'chat_in_round':
                self.state = RoundState.CHATINROUND
                await self.add_proposal_and_revote(command['content'])
            elif command['command'] == 'add_memory':
                self.state = RoundState.ADDMEMORY
                # Placeholder for add_memory functionality
                agent_number = command['content']['agent_number']
                memory = command['content']['memory']
                self.agents[int(agent_number)].add_memory(memory)
                print(f"Adding memory: {command['content']}")
                self.state = RoundState.WAITING

    async def add_proposal_and_revote(self, new_proposal):
        print(colored(f"Adding new proposal: {new_proposal}", "magenta"))
        self.results[-1]['proposals'].append(new_proposal)
        
        votes = [agent.vote(self.results[-1]['proposals']) for agent in self.agents]
        print(colored(f"New votes: {votes}", "yellow"))
        
        winner = max(set(votes), key=votes.count)
        winning_proposal = self.results[-1]['proposals'][winner - 1]
        print(colored(f"New winning proposal: {winning_proposal}", "green"))

        self.results[-1]['votes'] = votes
        self.results[-1]['winning_proposal'] = winning_proposal
        
        # Save updated results
        save_results('data/data_out.json', self.results)

    async def run_round(self):
        print(colored(f"Starting round {self.current_round + 1} of {self.total_rounds}", "cyan"))
        
        proposals = [agent.propose(self.topic) for agent in self.agents]
        
        votes = [agent.vote(proposals) for agent in self.agents]
        print(colored(f"Votes: {votes}", "yellow"))
        
        winner = max(set(votes), key=votes.count)
        winning_proposal = proposals[winner - 1]
        print(colored(f"Winning proposal: {winning_proposal}", "green"))

        round_result = {
            "round_count": self.current_round,
            "topic": self.topic,
            "proposals": proposals,
            "votes": votes,
            "winning_proposal": winning_proposal
        }
        self.results.append(round_result)
        
        # Save results after each round
        save_results('data/data_out.json', self.results)
        
        self.current_round += 1
        print(colored(f"Round {self.current_round} completed\n", "cyan"))

        # Generate new topic
        new_topic_prompt = f"Based on the winning proposal: '{winning_proposal}', generate a new topic for the next round of discussion about future cities. Respond with only the new topic."
        self.topic = self.agents[0].generate_response(new_topic_prompt)

    async def run_chat(self):
        while self.current_round < self.total_rounds:
            if self.state == RoundState.WAITING:
                await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting
            await self.process_commands()

async def main():
    agents, topic, total_rounds = load_agents('data/raw_data.json')
    chat = RoundTableChat(agents, topic, total_rounds)
    
    # Simulating UDP received commands
    chat.command_queue.append({"command": "start"})
    chat.command_queue.append({"command": "chat_in_round", "content": "My proposal is to build a green city all using solar energy"})
    chat.command_queue.append({"command": "chat_in_round", "content": "My proposal is to make ai to be the mayer of the city"})
    chat.command_queue.append({"command": "chat_in_round", "content": "My proposal is to Develop modular, vertical urban clusters connected by high-speed transit."})
    chat.command_queue.append({"command": "add_memory", "content": {"agent_number": "0", "memory": "i dont like everything, i just like my opinion"}})
    
    await chat.run_chat()

if __name__ == "__main__":
    asyncio.run(main())
