# Academic Network Analysis Tool

A web-based tool for visualizing and analyzing academic collaboration networks using OpenAlex data.

## Features

- Upload CSV files containing OpenAlex work IDs
- Specify a center author to focus the network visualization
- Visualize collaboration networks with institution-based coloring
- Identify top hub nodes based on centrality metrics
- View detailed statistics about the network structure

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/academic-network-analysis.git
cd academic-network-analysis
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
python app.py
```

4. Access the web interface at http://localhost:5000

## Usage

1. Prepare a CSV file containing OpenAlex work IDs (such as "W3036371598", "W3163131652", etc.)
2. Upload the CSV file through the web interface
3. Optionally specify a center author to focus the network visualization
4. View the network visualization and analysis results

## Data Format

The input CSV file should contain OpenAlex work IDs. The application will look for the following columns:
- `id` or `ids.openalex` for work IDs

If these columns are not found, the application will assume the first column contains the work IDs.

## How It Works

1. The application extracts work IDs from the uploaded CSV file
2. It fetches detailed information for each work from the OpenAlex API
3. Author-institution data and co-authorship relationships are extracted
4. A collaboration graph is constructed using NetworkX
5. Centrality metrics (degree, betweenness, eigenvector) are calculated
6. Hub nodes are identified based on composite centrality scores
7. The network is visualized with the specified center author (if provided) at the center
8. Statistics and detailed information about hub nodes are presented in the interface

## License

MIT 

### Example with Included Dataset

This repository includes an example dataset:

- **File:** `works-2025-05-09T21-24-58.csv`
- **Location:** In this repository (see the root directory)
- **How to use:**
  1. Upload `works-2025-05-09T21-24-58.csv` through the web interface
  2. Enter `Sizun Jiang` as the center author
  3. Click "Analyze Network" to visualize the collaboration network

This will generate a network visualization with Sizun Jiang at the center, showing their academic collaboration network and institutional connections.

#### About the Example CSV
- The file `works-2025-05-09T21-24-58.csv` is included in this repository for convenience.
- You can also download and search for similar datasets from [OpenAlex](https://openalex.org/), a fully open catalog of the global research system.
- To get your own data: Go to [https://openalex.org/](https://openalex.org/), search for papers, authors, or topics, and export the results as a CSV file for use with this application. 