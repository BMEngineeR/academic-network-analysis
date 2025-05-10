import os
import json
import uuid
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import requests
import time
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from collections import defaultdict
import io
import base64

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ALLOWED_EXTENSIONS = {'csv', 'txt'}
DEFAULT_CENTER_AUTHOR = "Sizun Jiang"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    center_author = request.form.get('center_author', DEFAULT_CENTER_AUTHOR)
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{unique_id}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the uploaded file
        file.save(filepath)
        
        try:
            # Process the CSV file
            result = process_network(filepath, center_author)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

def fetch_work_data(work_id):
    """Fetch data for a specific work from OpenAlex API"""
    url = f"https://api.openalex.org/works/{work_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data for {work_id}: {e}")
        return None

def process_network(csv_path, center_author):
    """Process the CSV file and generate network visualization"""
    # Read CSV file
    try:
        df = pd.read_csv(csv_path)
        
        # Extract work IDs
        if 'id' in df.columns:
            # Extract IDs from standard format
            work_ids = df['id'].tolist()
        elif 'ids.openalex' in df.columns:
            # Extract IDs from alternative format
            work_ids = df['ids.openalex'].tolist()
        else:
            # Assume the first column contains IDs
            work_ids = df.iloc[:, 0].tolist()
    except Exception as e:
        return {'error': f'Error processing CSV: {str(e)}'}
    
    # Collect author-institution data and co-author relationships
    author_affiliation = {}
    coauthorships = []
    
    for work_id in work_ids[:100]:  # Limit to first 100 for performance
        data = fetch_work_data(work_id)
        if data:
            authors = data.get("authorships", [])
            names = []
            for a in authors:
                name = a.get("author", {}).get("display_name", None)
                insts = a.get("institutions", [])
                if name:
                    affil = insts[0]["display_name"] if insts else "Unknown"
                    author_affiliation[name] = affil
                    names.append(name)
            # Add coauthor edges
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    coauthorships.append((names[i], names[j]))
        time.sleep(0.1)  # Be polite to the API
    
    # Build collaboration graph
    G = nx.Graph()
    G.add_edges_from(coauthorships)
    
    # Extract all unique institutions from author affiliations
    unique_institutions = set()
    for author, affiliation in author_affiliation.items():
        if isinstance(affiliation, list):
            if affiliation:
                unique_institutions.add(affiliation[0])
        elif affiliation:
            unique_institutions.add(affiliation)
    
    # Map each institution to a color index
    institution_colors = {
        inst: i % 10 for i, inst in enumerate(sorted(unique_institutions))
    }
    
    # Calculate centrality metrics to identify hub nodes
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    
    try:
        eigenvector_centrality = nx.eigenvector_centrality_numpy(G)
    except:
        # Fallback if eigenvector centrality fails
        eigenvector_centrality = {node: 0 for node in G.nodes()}
    
    # Calculate hub scores with balanced weighting
    hub_score = {}
    for node in G.nodes():
        hub_score[node] = (
            1 * degree_centrality.get(node, 0) + 
            1 * betweenness_centrality.get(node, 0) +
            1 * eigenvector_centrality.get(node, 0)
        )
    
    # Get top 20 hub nodes
    num_hubs = min(20, len(hub_score))
    hub_nodes = sorted([(node, score) for node, score in hub_score.items()], 
                      key=lambda x: x[1], reverse=True)[:num_hubs]
    hub_node_list = [h[0] for h in hub_nodes]
    
    # Create initial layout
    pos = nx.spring_layout(G, seed=42, k=0.5)
    
    # Position hub nodes in a more natural spread
    # Place center author in the middle if present
    if center_author in hub_node_list:
        pos[center_author] = np.array([0, 0])
        
    # Position remaining hub nodes in a more balanced way
    for i, node in enumerate(hub_node_list):
        if node != center_author:
            radius = 1.0 + (i * 0.1)
            angle = i * 0.5
            pos[node] = np.array([radius * np.cos(angle), radius * np.sin(angle)])
    
    # Create the figure
    plt.figure(figsize=(20, 18))
    
    # Draw all edges with uniform style
    nx.draw_networkx_edges(G, pos, alpha=0.2, edge_color='gray', width=0.5)
    
    # Draw regular nodes with colors by institution
    regular_nodes = [n for n in G.nodes() if n not in hub_node_list]
    for inst, color_idx in institution_colors.items():
        nodes = [author for author in regular_nodes 
                 if author_affiliation.get(author) == inst]
        if nodes:
            color = plt.cm.tab10(color_idx)
            nx.draw_networkx_nodes(G, pos, nodelist=nodes, 
                                  node_color=[color], 
                                  node_size=20, alpha=0.6)
    
    # Draw hub nodes with scaled sizes based on rank
    hub_sizes = []
    for i, (node, score) in enumerate(hub_nodes):
        if i < 10:  # Top 10
            size = 300 - (i * 15)
        else:  # 11-20
            size = 150 - ((i-10) * 5)
        hub_sizes.append(size)
    
    # Color hub nodes by their institution
    hub_colors = []
    for node, _ in hub_nodes:
        if node == center_author:
            hub_colors.append('gold')
        else:
            inst = author_affiliation.get(node)
            color_idx = institution_colors.get(inst, 0)
            hub_colors.append(plt.cm.tab10(color_idx))
    
    # Draw hub nodes
    nx.draw_networkx_nodes(G, pos, nodelist=hub_node_list, 
                          node_color=hub_colors, 
                          node_size=hub_sizes,
                          edgecolors='black', linewidths=1.0)
    
    # Add labels for hub nodes with rank
    for i, (node, score) in enumerate(hub_nodes):
        x, y = pos[node]
        rank = i+1
        if rank <= 10:
            fontsize = 12
            bbox = dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.2')
        else:
            fontsize = 10
            bbox = dict(facecolor='white', alpha=0.6, edgecolor='lightgray', boxstyle='round,pad=0.1')
            
        plt.text(x, y+0.1, f"{rank}. {node}", fontsize=fontsize, ha='center', 
                 bbox=bbox)
    
    # Add title and remove axes
    plt.title(f"Top {num_hubs} Hub Nodes in Collaboration Network", fontsize=18)
    plt.axis('off')
    plt.tight_layout()
    
    # Save the figure to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode as base64 string
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # Prepare node data for visualization
    node_data = []
    for i, (node, score) in enumerate(hub_nodes):
        node_data.append({
            'rank': i + 1,
            'name': node,
            'institution': author_affiliation.get(node, 'Unknown'),
            'degree': degree_centrality.get(node, 0),
            'betweenness': betweenness_centrality.get(node, 0),
            'eigenvector': eigenvector_centrality.get(node, 0),
            'hub_score': score
        })
    
    # Prepare edge data
    edge_data = []
    for source, target in G.edges():
        if source in hub_node_list or target in hub_node_list:
            edge_data.append({
                'source': source,
                'target': target
            })
    
    return {
        'image': img_base64,
        'nodes': node_data,
        'edges': edge_data,
        'institutions': {inst: i for i, inst in enumerate(institution_colors.keys())},
        'center_author': center_author,
        'network_stats': {
            'total_nodes': len(G.nodes()),
            'total_edges': len(G.edges()),
            'density': nx.density(G),
            'average_clustering': nx.average_clustering(G)
        }
    }

@app.route('/data/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 