import json
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from langchain_community.embeddings import OllamaEmbeddings
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.loads(file.read())

def save_json(data, file_path):
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, list):
                return [self.default(item) for item in obj]
            return json.JSONEncoder.default(self, obj)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4, cls=NumpyEncoder)

def get_embedding_vector(model: str, text: str):
    embeddings_model = OllamaEmbeddings(model=model)
    return embeddings_model.embed_query(text)

def generate_embeddings(texts):
    return [get_embedding_vector(model="phi3", text=text) for text in texts]

def process_data(data):
    texts_to_embed = []
    for round_data in data['runtime']:
        texts_to_embed.append(round_data['topic'] if isinstance(round_data['topic'], str) else round_data['topic'].get('text', ''))
        for proposal in round_data['proposals']:
            texts_to_embed.append(proposal if isinstance(proposal, str) else proposal.get('text', proposal.get('proposal', '')))

    embeddings = generate_embeddings(texts_to_embed)
    all_vectors_np = np.array(embeddings)
    scaler = StandardScaler()
    all_vectors_scaled = scaler.fit_transform(all_vectors_np)
    pca = PCA(n_components=3)
    principal_components = pca.fit_transform(all_vectors_scaled)

    embedding_index = 0
    for round_data in data['runtime']:
        topic_text = round_data['topic'] if isinstance(round_data['topic'], str) else round_data['topic'].get('text', '')
        round_data['topic'] = {
            'text': topic_text,
            'compressed_text': topic_text[:100] + '...' if len(topic_text) > 100 else topic_text,
            'vector': embeddings[embedding_index] if embedding_index < len(embeddings) else None,
            'pca_vector': principal_components[embedding_index].tolist() if embedding_index < len(principal_components) else None
        }
        embedding_index += 1
        
        round_data['proposals'] = [
            {
                'text': proposal if isinstance(proposal, str) else proposal.get('text', proposal.get('proposal', '')),
                'compressed_proposal': (proposal[:100] + '...') if len(proposal) > 100 else proposal if isinstance(proposal, str) else (proposal.get('text', proposal.get('proposal', ''))[:100] + '...'),
                'vector': embeddings[embedding_index] if embedding_index < len(embeddings) else None,
                'pca_vector': principal_components[embedding_index].tolist() if embedding_index < len(principal_components) else None
            }
            for proposal in round_data['proposals']
        ]
        embedding_index += len(round_data['proposals'])

    return data

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, file_path)

def process_file():
    input_file_path = path_entry.get()
    if not input_file_path or not os.path.exists(input_file_path):
        messagebox.showerror("Error", "Please select a valid file.")
        return

    try:
        data = load_json(input_file_path)
        processed_data = process_data(data)
        file_name, file_extension = os.path.splitext(input_file_path)
        output_file_path = f"{file_name}_edited{file_extension}"
        save_json(processed_data, output_file_path)
        messagebox.showinfo("Success", f"Embeddings generated and saved to {output_file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Create the main window
root = tk.Tk()
root.title("JSON Processor")
root.geometry("500x120")  # Adjusted size

# Create a frame for the file selection row
file_frame = tk.Frame(root)
file_frame.pack(pady=20, padx=10, fill=tk.X)

# Create and pack widgets
tk.Label(file_frame, text="Select JSON file:").pack(side=tk.LEFT)
path_entry = tk.Entry(file_frame, width=25)
path_entry.pack(side=tk.LEFT, padx=(10, 5), expand=True, fill=tk.X)
tk.Button(file_frame, text="Browse", command=select_file).pack(side=tk.RIGHT)

# Create a frame for the process button
process_frame = tk.Frame(root)
process_frame.pack(pady=10, fill=tk.X)

# Add the Process button
tk.Button(process_frame, text="Process", command=process_file, width=20).pack()

# Start the GUI event loop
root.mainloop()
