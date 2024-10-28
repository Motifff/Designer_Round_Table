import json
import ollama
from typing import List, Dict, Optional
import re
from tqdm import tqdm
import time
import tkinter as tk
from tkinter import filedialog, messagebox

class ProposalAnalyzer:
    def __init__(self, json_path: str):
        print(f"Loading data from {json_path}...")
        self.data = self._load_json(json_path)
        self.model = "phi3"
        print(f"Initialized with {len(self.data['runtime'])} rounds")
    
    def _load_json(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return json.load(f)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        # Split text into sentences using regex
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_embedding(self, text: str) -> List[float]:
        # Get embedding from ollama model
        response = ollama.embeddings(
            model=self.model,
            prompt=text
        )
        return response['embedding']
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        # Get embeddings and compute cosine similarity
        emb1 = self._get_embedding(text1)
        emb2 = self._get_embedding(text2)
        
        # Compute cosine similarity
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        return dot_product / (norm1 * norm2)
    
    def find_nearest_sentences(self, round_idx: int) -> List[Dict]:
        runtime = self.data['runtime']
        if round_idx >= len(runtime):
            return []
        
        print(f"\nProcessing Round {round_idx + 1}/{len(runtime)}")
        current_topic = runtime[round_idx]['topic']['text']
        next_topic = runtime[round_idx + 1]['topic']['text'] if round_idx + 1 < len(runtime) else None
        
        results = []
        proposals = runtime[round_idx]['proposals']
        
        print(f"Processing {len(proposals)} proposals...")
        for idx, proposal in enumerate(proposals, 1):
            print(f"\nAnalyzing proposal {idx}/{len(proposals)}")
            proposal_text = proposal['text']
            sentences = self._split_into_sentences(proposal_text)
            print(f"Found {len(sentences)} sentences")
            
            # Find nearest sentence to current topic
            max_similarity = -1
            nearest_current = ""
            
            print("Finding matches for current topic...")
            for i, sentence in enumerate(sentences, 1):
                print(f"\rProcessing sentence {i}/{len(sentences)}", end="")
                similarity = self._compute_similarity(sentence, current_topic)
                if similarity > max_similarity:
                    max_similarity = similarity
                    nearest_current = sentence
            print(f"\nBest match found with similarity: {max_similarity:.3f}")
            
            result = {
                "proposal_idx": idx - 1,
                "pre_link": nearest_current,
                "after_link": None
            }
            
            # If there's a next topic, find nearest sentence to it
            if next_topic:
                print("\nFinding matches for next topic...")
                max_similarity = -1
                nearest_next = ""
                
                for i, sentence in enumerate(sentences, 1):
                    print(f"\rProcessing sentence {i}/{len(sentences)}", end="")
                    similarity = self._compute_similarity(sentence, next_topic)
                    if similarity > max_similarity:
                        max_similarity = similarity
                        nearest_next = sentence
                print(f"\nBest match found with similarity: {max_similarity:.3f}")
                
                result["after_link"] = nearest_next
            
            results.append(result)
        
        return results

    def _clean_data(self) -> Dict:
        """Remove vector-related keys from the data"""
        print("\nCleaning data...")
        cleaned_data = self.data.copy()
        
        # Clean runtime data
        for round_data in tqdm(cleaned_data['runtime'], desc="Removing vector data"):
            if 'topic' in round_data:
                # Keep only the text field in topic
                round_data['topic'] = {'text': round_data['topic']['text']}
            
            # Clean proposals
            if 'proposals' in round_data:
                for proposal in round_data['proposals']:
                    keys_to_remove = ['vector', 'compressed_text', 'pca_vector', 'compressed_proposal']
                    for key in keys_to_remove:
                        proposal.pop(key, None)
            
            # Remove any other vector-related fields
            keys_to_remove = ['vector', 'compressed_text', 'pca_vector']
            for key in keys_to_remove:
                round_data.pop(key, None)
                if 'topic' in round_data:
                    round_data['topic'].pop(key, None)
        
        return cleaned_data

    def analyze_all_rounds(self):
        start_time = time.time()
        print("\nStarting analysis of all rounds...")
        results = []
        
        for i in range(len(self.data['runtime'])):
            round_start = time.time()
            round_results = self.find_nearest_sentences(i)
            round_end = time.time()
            
            results.append({
                "round": i,
                "proposals": round_results
            })
            
            print(f"Round {i + 1} completed in {round_end - round_start:.2f} seconds")
        
        # Update the original JSON with results
        print("\nUpdating JSON with results...")
        for i, result in enumerate(results):
            for proposal_result in result['proposals']:
                idx = proposal_result['proposal_idx']
                self.data['runtime'][i]['proposals'][idx]['pre_link'] = proposal_result['pre_link']
                self.data['runtime'][i]['proposals'][idx]['after_link'] = proposal_result['after_link']
        
        # Clean and save the data without vectors
        cleaned_data = self._clean_data()
        
        # Replace the hardcoded output path with the instance variable
        output_path = getattr(self, 'output_path', 'data/history/bright_env_cleaned.json')
        print(f"\nSaving cleaned data to {output_path}...")
        with open(output_path, 'w') as f:
            json.dump(cleaned_data, f, indent=4)
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nAnalysis completed in {total_time:.2f} seconds")
        print(f"Results saved to {output_path}")

def main():
    # Create root window but hide it
    root = tk.Tk()
    root.withdraw()

    # Open file dialog for input file
    input_file = filedialog.askopenfilename(
        title="Select Input JSON File",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir="data/history"
    )
    
    if not input_file:
        messagebox.showerror("Error", "No input file selected")
        return

    # Open file dialog for output file
    output_file = filedialog.asksaveasfilename(
        title="Select Output File Location",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir="data/history",
        initialfile="bright_env_cleaned.json"
    )
    
    if not output_file:
        messagebox.showerror("Error", "No output location selected")
        return

    try:
        analyzer = ProposalAnalyzer(input_file)
        # Update the output path in analyze_all_rounds
        analyzer.output_path = output_file
        analyzer.analyze_all_rounds()
        messagebox.showinfo("Success", f"Analysis completed!\nResults saved to {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
