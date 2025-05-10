document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const loadingSpinner = document.getElementById('loading-spinner');
    const submitBtn = document.getElementById('submit-btn');
    const resultCard = document.getElementById('result-card');
    const networkImage = document.getElementById('network-image');
    const hubNodesCard = document.getElementById('hub-nodes-card');
    const hubNodesBody = document.getElementById('hub-nodes-body');
    const statsCard = document.getElementById('stats-card');
    const networkStats = document.getElementById('network-stats');

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading spinner
        loadingSpinner.classList.remove('d-none');
        submitBtn.disabled = true;
        
        // Hide result cards if they were previously shown
        resultCard.classList.add('d-none');
        hubNodesCard.classList.add('d-none');
        statsCard.classList.add('d-none');
        
        // Get form data
        const formData = new FormData(uploadForm);
        
        // Make API call
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'An error occurred while processing your request.');
                });
            }
            return response.json();
        })
        .then(data => {
            // Handle successful response
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Display network visualization
            networkImage.src = `data:image/png;base64,${data.image}`;
            resultCard.classList.remove('d-none');
            
            // Display hub nodes table
            populateHubNodesTable(data.nodes);
            hubNodesCard.classList.remove('d-none');
            
            // Display network statistics
            populateNetworkStats(data.network_stats);
            statsCard.classList.remove('d-none');
        })
        .catch(error => {
            showError(error.message);
        })
        .finally(() => {
            // Hide loading spinner
            loadingSpinner.classList.add('d-none');
            submitBtn.disabled = false;
        });
    });
    
    function populateHubNodesTable(nodes) {
        // Clear existing table rows
        hubNodesBody.innerHTML = '';
        
        // Add rows for each hub node
        nodes.forEach(node => {
            const row = document.createElement('tr');
            
            // Add rank cell with bold styling for top 5
            const rankCell = document.createElement('td');
            if (node.rank <= 5) {
                rankCell.innerHTML = `<strong>${node.rank}</strong>`;
            } else {
                rankCell.textContent = node.rank;
            }
            row.appendChild(rankCell);
            
            // Add name cell
            const nameCell = document.createElement('td');
            nameCell.textContent = node.name;
            row.appendChild(nameCell);
            
            // Add institution cell
            const institutionCell = document.createElement('td');
            institutionCell.textContent = node.institution;
            row.appendChild(institutionCell);
            
            // Add centrality measures cells
            ['degree', 'betweenness', 'eigenvector', 'hub_score'].forEach(metric => {
                const cell = document.createElement('td');
                cell.textContent = node[metric].toFixed(4);
                row.appendChild(cell);
            });
            
            hubNodesBody.appendChild(row);
        });
    }
    
    function populateNetworkStats(stats) {
        // Clear existing stats
        networkStats.innerHTML = '';
        
        // Add each statistic
        const statItems = [
            { label: 'Total Nodes', value: stats.total_nodes },
            { label: 'Total Edges', value: stats.total_edges },
            { label: 'Network Density', value: stats.density.toFixed(4) },
            { label: 'Average Clustering', value: stats.average_clustering.toFixed(4) }
        ];
        
        statItems.forEach(item => {
            const statItem = document.createElement('div');
            statItem.className = 'stat-item';
            
            const statLabel = document.createElement('div');
            statLabel.className = 'stat-label';
            statLabel.textContent = item.label;
            
            const statValue = document.createElement('div');
            statValue.className = 'stat-value';
            statValue.textContent = item.value;
            
            statItem.appendChild(statLabel);
            statItem.appendChild(statValue);
            networkStats.appendChild(statItem);
        });
    }
    
    function showError(message) {
        alert('Error: ' + message);
    }
}); 