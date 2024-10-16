import asyncio
import json
from enum import Enum
from termcolor import colored
from utils import load_agents, save_results
from collections import deque
import threading
import socket
import time

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
        
        # Create a new result based on the previous one
        previous_result = self.results[-1]
        new_result = {
            "round_count": previous_result["round_count"] + 0.5,
            "topic": previous_result["topic"],
            "proposals": previous_result["proposals"] + [new_proposal],
            "votes": [],
            "winning_proposal": ""
        }
        
        winner, votes = await self.conduct_vote(new_result['proposals'])
        winning_proposal = new_result['proposals'][winner - 1]
        print(colored(f"New winning proposal: {winning_proposal}", "green"))

        new_result['votes'] = votes
        new_result['winning_proposal'] = winning_proposal
        
        # Add the new result to the results list
        self.results.append(new_result)
        
        new_topic_prompt = f"Based on the winning proposal: '{winning_proposal}', generate a new topic for the next round of discussion about future cities. Respond with only the new topic."
        self.topic = self.agents[0].generate_response(new_topic_prompt)

        # Save updated results
        save_results('data/data_out.json', self.results)

    async def run_round(self):
        print(colored(f"Starting round {self.current_round + 1} of {self.total_rounds}", "cyan"))
        
        proposals = [agent.propose(self.topic) for agent in self.agents]
        
        winner, votes = await self.conduct_vote(proposals)
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

    async def conduct_vote(self, proposals):
        while True:
            votes = [agent.vote(proposals) for agent in self.agents]
            print(colored(f"Votes: {votes}", "yellow"))
            
            vote_counts = {i: votes.count(i) for i in set(votes)}
            max_votes = max(vote_counts.values())
            winners = [k for k, v in vote_counts.items() if v == max_votes]
            
            if len(winners) == 1:
                return winners[0],votes
            else:
                print(colored("Tie detected. Conducting a revote...", "yellow"))
                # Revote only among the tied proposals
                proposals = [proposals[i-1] for i in winners]

class UDPReceiver:
    def __init__(self, ip, port, command_queue):
        self.ip = ip
        self.port = port
        self.command_queue = command_queue
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.receive_commands)
        self.thread.start()
        print(colored("UDP Receiver started. Standing by for messages...", "cyan"))

    def stop(self):
        self.running = False
        self.thread.join()
        print(colored("UDP Receiver stopped.", "cyan"))

    def receive_commands(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.ip, self.port))
        sock.settimeout(1.0)  # 1 second timeout for checking self.running

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                command = json.loads(data.decode('utf-8'))
                self.command_queue.append(command)
                print(colored(f"Received command: {command}", "green"))
                print(colored("Standing by for next message...", "cyan"))
            except socket.timeout:
                print(colored("UDP Receiver standing by...", "cyan"), end='\r')
                time.sleep(1)  # Wait for a second before printing again
            except json.JSONDecodeError:
                print(colored("Received invalid JSON data", "red"))
            except Exception as e:
                print(colored(f"Error receiving UDP data: {e}", "red"))

        sock.close()

async def main():
    agents, topic, total_rounds = load_agents('data/raw_data.json')
    chat = RoundTableChat(agents, topic, total_rounds)
    
    # Create and start the UDP receiver
    udp_receiver = UDPReceiver('127.0.0.1', 5000, chat.command_queue)
    udp_receiver.start()

    try:
        await chat.run_chat()
    finally:
        # Stop the UDP receiver when the chat is done
        udp_receiver.stop()

if __name__ == "__main__":
    asyncio.run(main())
