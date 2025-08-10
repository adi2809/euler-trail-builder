# Euler Trail Builder 🎯

A modern, interactive web application for creating graphs and finding Euler trails using Hierholzer's algorithm. Built with Flask backend and vanilla JavaScript frontend.

![Euler Trail Builder](https://img.shields.io/badge/Python-3.8+-blue.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

## ✨ Features

### 🎮 Interactive Graph Builder
- **Click to Add Nodes**: Click anywhere on the canvas to add numbered nodes
- **Create Edges**: Select two nodes to connect them with edges
- **Delete Elements**: Remove nodes or edges with delete mode
- **Drag & Drop**: Move nodes around by dragging them
- **Graph Types**: Toggle between directed and undirected graphs

### 🔍 Euler Trail Detection
- **Smart Algorithm**: Uses Hierholzer's algorithm for accurate trail detection
- **Real-time Analysis**: Shows graph connectivity and statistics
- **Visual Feedback**: Highlights the Euler trail with animated edges
- **Detailed Results**: Modal shows trail sequence and mathematical details
- **Error Handling**: Clear feedback when no Euler trail exists

### 💎 Modern Design
- **Responsive Layout**: Works on desktop and mobile devices
- **Professional UI**: Clean, modern interface with smooth animations
- **Status Tracking**: Real-time feedback for all user actions
- **Help System**: Built-in instructions and examples

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/euler-trail-builder.git
   cd euler-trail-builder
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install flask flask-cors
   ```

3. **Start the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   ```
   http://localhost:5001
   ```

## 🎯 How to Use

### Building Graphs
1. **Select Mode**: Choose "Add Nodes", "Create Edges", or "Delete Elements"
2. **Add Nodes**: Click anywhere on the gray canvas area
3. **Create Edges**: 
   - Switch to "Create Edges" mode
   - Click two nodes to connect them
4. **Graph Type**: Toggle between "Undirected" and "Directed" graphs

### Finding Euler Trails
1. **Build Your Graph**: Add nodes and edges as described above
2. **Click "Find Euler Trail"**: The algorithm will analyze your graph
3. **View Results**: 
   - If a trail exists, edges will highlight in sequence
   - A modal will show the complete trail path
   - Status panel provides detailed feedback

### Example Scenarios
- **Simple Path**: A→B→C (has Euler trail)
- **Cycle**: A→B→C→A (has Euler trail)
- **Complex Graph**: Multiple interconnected paths
- **No Trail**: Disconnected components or odd-degree vertices

## 🏗️ Architecture

### Backend (Flask)
- **RESTful API**: Clean endpoints for graph analysis
- **Hierholzer's Algorithm**: Efficient Euler trail detection
- **CORS Support**: Enables frontend-backend communication
- **Error Handling**: Comprehensive error responses

### Frontend (Vanilla JavaScript)
- **SVG Rendering**: Scalable vector graphics for nodes and edges
- **Event-Driven**: Responsive user interactions
- **Modern CSS**: CSS Grid, Flexbox, and animations
- **Modular Design**: Clean separation of concerns

### File Structure
```
euler-trail-builder/
├── backend/
│   └── app.py              # Flask server with Euler algorithms
├── frontend/
│   ├── index.html          # Main HTML structure
│   ├── styles.css          # Modern CSS styling
│   └── script.js           # Interactive JavaScript
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
└── .gitignore             # Git ignore rules
```

## 🧮 Algorithm Details

### Euler Trail Theory
An **Euler trail** is a path in a graph that visits every edge exactly once.

**Conditions for Euler Trails:**
- **Undirected Graph**: 
  - Connected graph with exactly 0 or 2 vertices of odd degree
- **Directed Graph**: 
  - Weakly connected with at most one vertex having (out-degree - in-degree = 1) and at most one vertex having (in-degree - out-degree = 1)

### Hierholzer's Algorithm
1. **Start** from a vertex with odd degree (if any), otherwise any vertex
2. **Follow edges** to form a trail, removing used edges
3. **When stuck**, find a vertex in the current trail with unused edges
4. **Create sub-trails** from such vertices
5. **Combine trails** to form the complete Euler trail

## 🛠️ Development

### Running in Development Mode
```bash
# Backend with auto-reload
cd backend
python app.py

# The server runs on http://localhost:5001
# Frontend files are served automatically
```

### API Endpoints

#### POST `/api/euler-trail`
Find Euler trail for a given graph.

**Request:**
```json
{
  "nodes": ["1", "2", "3"],
  "edges": [
    {"id": "1-2", "source": "1", "target": "2"},
    {"id": "2-3", "source": "2", "target": "3"}
  ],
  "graph_type": "undirected"
}
```

**Response:**
```json
{
  "success": true,
  "trail": [
    {"step": 1, "edge_id": "1-2", "source": "1", "target": "2"},
    {"step": 2, "edge_id": "2-3", "source": "2", "target": "3"}
  ],
  "error": null
}
```

### Customization
- **Styling**: Modify `frontend/styles.css` for visual changes
- **Algorithms**: Extend `backend/app.py` for additional graph algorithms
- **UI Components**: Update `frontend/script.js` for new features

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Educational Use

This project is perfect for:
- **Computer Science Students**: Learning graph theory and algorithms
- **Mathematics**: Understanding Euler trails and graph connectivity
- **Web Development**: Modern frontend-backend architecture
- **Algorithm Visualization**: Interactive learning of graph algorithms

## 🔗 Related Concepts

- **Graph Theory**: Vertices, edges, paths, cycles
- **Euler Circuits**: Closed trails that visit every edge once
- **Hamiltonian Paths**: Paths that visit every vertex once
- **Graph Traversal**: DFS, BFS, and specialized algorithms

## 🆘 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/euler-trail-builder/issues) page
2. Create a new issue with detailed description
3. Include browser console logs if applicable

---

**Built with ❤️ for graph theory enthusiasts and algorithm learners!**
