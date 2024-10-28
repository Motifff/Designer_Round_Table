import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import os

class PCAVisualizer:
    def __init__(self, master):
        self.master = master
        self.master.title("PCA Visualizer")
        self.master.geometry("400x150")

        self.file_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        # File path input
        tk.Label(self.master, text="File Path:").pack(pady=(10,0))
        self.path_entry = tk.Entry(self.master, textvariable=self.file_path, width=50)
        self.path_entry.pack(pady=(0,5))

        # Buttons
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Browse", command=self.select_file).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Visualize", command=self.visualize).pack(side=tk.LEFT, padx=5)

    def select_file(self):
        initial_dir = os.getcwd()  # Get the current working directory
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            self.file_path.set(file_path)

    def visualize(self):
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a file first.")
            return

        self.process_data()

    def process_data(self):
        # Load the JSON data
        with open(self.file_path.get(), 'r') as file:
            data = json.loads(file.read())

        # Prepare data for PCA visualization
        all_vectors = []
        labels = []
        colors = []
        paragraphs = []

        agent_names = [agent['name'] for agent in data['agents']]
        agent_index = 0

        round_colors = [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
        ]
        alpha = 0.5

        for i, round_data in enumerate(data['runtime']):
            topic_vector = round_data['topic']['vector']
            all_vectors.append(topic_vector)
            labels.append(f"Round {round_data['round_count']} Topic")
            colors.append(round_colors[i])
            paragraphs.append(f"System: {round_data['topic']['text']}")

            for proposal in round_data['proposals']:
                proposal_vector = proposal['vector']
                all_vectors.append(proposal_vector)
                labels.append(f"Round {round_data['round_count']} Proposal")
                colors.append(round_colors[i])
                paragraphs.append(f"{agent_names[agent_index]}: {proposal['text']}")
                agent_index = (agent_index + 1) % len(agent_names)

        # Convert all_vectors to numpy array for PCA
        all_vectors_np = np.array(all_vectors)

        # Standardize the vectors
        scaler = StandardScaler()
        all_vectors_scaled = scaler.fit_transform(all_vectors_np)

        # Apply PCA
        pca = PCA(n_components=3)
        principal_components = pca.fit_transform(all_vectors_scaled)

        # Create a new window for visualization
        vis_window = tk.Toplevel(self.master)
        vis_window.title("PCA Visualization")

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Create scatter plot
        scatter = ax.scatter(principal_components[:, 0], principal_components[:, 1], principal_components[:, 2], c=colors, alpha=0.5)

        # Function to update annotation on hover
        def update_annot(ind):
            pos = scatter._offsets3d
            x, y, z = pos[0][ind["ind"][0]], pos[1][ind["ind"][0]], pos[2][ind["ind"][0]]
            annot.xy = (x, y)
            annot.set_position((x, y, z))
            text = f"Author: {authors[ind['ind'][0]]}\n\n{paragraphs[ind['ind'][0]]}"
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.9)

        # Create a custom annotation class for auto-scrolling
        class ScrollingAnnotation(plt.Annotation):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.scroll_speed = 1
                self.scroll_position = 0
                self.full_text = ""

            def set_full_text(self, text):
                self.full_text = text
                self.scroll_position = 0

            def update_text(self):
                visible_text = self.full_text[self.scroll_position:self.scroll_position + 200]
                self.set_text(visible_text)
                self.scroll_position = (self.scroll_position + self.scroll_speed) % len(self.full_text)

        # Replace the original annotation with the custom one
        annot = ScrollingAnnotation("", xy=(0,0), xytext=(20,20),
                                        textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w"),
                                        arrowprops=dict(arrowstyle="->"))
        ax.add_artist(annot)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont, ind = scatter.contains(event)
                if cont:
                    pos = scatter._offsets3d
                    x, y, z = pos[0][ind["ind"][0]], pos[1][ind["ind"][0]], pos[2][ind["ind"][0]]
                    annot.xy = (x, y)
                    annot.set_position((x, y, z))
                    annot.set_full_text(paragraphs[ind['ind'][0]])
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        # Function to update the annotation text
        def update_annotation(frame):
            if annot.get_visible():
                annot.update_text()
                return annot,
            return ()

        # Connect the topics and proposals
        for i, round_data in enumerate(data['runtime']):
            for idx, proposal in enumerate(round_data['proposals']):
                ax.plot([principal_components[i*4, 0], principal_components[i*4+idx+1, 0]],
                        [principal_components[i*4, 1], principal_components[i*4+idx+1, 1]],
                        [principal_components[i*4, 2], principal_components[i*4+idx+1, 2]],
                        color=round_colors[i],linestyle='--', alpha=0.2)

        # Connect topics from consecutive rounds
        for i in range(len(data['runtime']) - 1):
            current_topic_index = labels.index(f"Round {data['runtime'][i]['round_count']} Topic")
            next_topic_index = labels.index(f"Round {data['runtime'][i+1]['round_count']} Topic")
            print("current_topic:"+str(current_topic_index)+"&next_topic:"+str(next_topic_index))
            ax.plot([principal_components[current_topic_index, 0], principal_components[next_topic_index, 0]],
                    [principal_components[current_topic_index, 1], principal_components[next_topic_index, 1]],
                    [principal_components[current_topic_index, 2], principal_components[next_topic_index, 2]],
                    color=round_colors[i])

        ax.set_xlabel('PCA Component 1')
        ax.set_ylabel('PCA Component 2')
        ax.set_zlabel('PCA Component 3')
        ax.set_title('3D PCA Visualization of Topics and Proposals')
        annot.set_visible(False)

        canvas = FigureCanvasTkAgg(fig, master=vis_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Connect the hover event to the canvas
        canvas.mpl_connect("motion_notify_event", self.hover)

        # Add animation for auto-scrolling
        self.anim = FuncAnimation(fig, self.update_annotation, interval=100, blit=True)

        # Add a close button
        tk.Button(vis_window, text="Close", command=vis_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = PCAVisualizer(root)
    root.mainloop()
