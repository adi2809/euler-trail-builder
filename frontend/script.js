// Euler Trail Builder - Interactive JavaScript with React Hooks

class EulerTrailBuilder {
    constructor() {
        console.log('🎯 EulerTrailBuilder constructor called');
        this.nodes = new Map();
        this.edges = [];
        this.nodeCounter = 1;
        this.selectedNodes = [];
        this.currentMode = 'node';
        this.isDirected = false;
        this.isAddingNode = false;
        this.draggedNode = null;
        this.dragOffset = { x: 0, y: 0 };
        
        console.log('🚀 Initializing EulerTrailBuilder...');
        this.init();
    }

    init() {
        console.log('⚙️ Setting up event listeners...');
        this.setupEventListeners();
        this.setupModals();
        this.updateDisplay();
        console.log('✅ EulerTrailBuilder initialized successfully');
    }

    setupEventListeners() {
        // Mode selection
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentMode = e.target.value;
                this.clearSelection();
                this.updateModeButtons();
                this.showStatus(`Mode changed to: ${this.currentMode}`);
            });
        });

        // Graph type selection
        document.querySelectorAll('input[name="graphType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.isDirected = e.target.value === 'directed';
                this.updateDisplay();
                this.showStatus(`Graph type changed to: ${this.isDirected ? 'directed' : 'undirected'}`);
            });
        });

        // Action buttons
        document.getElementById('clearGraph').addEventListener('click', () => {
            this.clearGraph();
        });

        document.getElementById('findEulerTrail').addEventListener('click', () => {
            this.findEulerTrail();
        });

        document.getElementById('showHelp').addEventListener('click', () => {
            this.showHelpModal();
        });

        // Graph canvas events
        const canvas = document.getElementById('graphCanvas');
        canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        // Zoom controls
        document.getElementById('zoomIn').addEventListener('click', () => this.zoom(1.2));
        document.getElementById('zoomOut').addEventListener('click', () => this.zoom(0.8));
        document.getElementById('resetView').addEventListener('click', () => this.resetView());
    }

    setupModals() {
        // Close modal buttons
        document.querySelectorAll('.btn-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    modal.classList.remove('show');
                }
            });
        });

        // Close modal on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.show').forEach(modal => {
                    modal.classList.remove('show');
                });
            }
        });
    }

    handleCanvasClick(e) {
        console.log('🖱️ Canvas clicked, current mode:', this.currentMode);
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        console.log('📍 Click coordinates:', x, y);

        if (this.currentMode === 'node') {
            this.addNode(x, y);
        } else if (this.currentMode === 'edge') {
            this.handleEdgeMode(e);
        } else if (this.currentMode === 'delete') {
            this.handleDeleteMode(e);
        }
    }

    handleMouseDown(e) {
        if (this.currentMode === 'node' && e.target.classList.contains('node-circle')) {
            this.draggedNode = e.target.closest('.node');
            const nodeId = this.draggedNode.dataset.nodeId;
            const node = this.nodes.get(nodeId);
            
            const rect = e.currentTarget.getBoundingClientRect();
            this.dragOffset.x = e.clientX - rect.left - node.x;
            this.dragOffset.y = e.clientY - rect.top - node.y;
            
            e.preventDefault();
        }
    }

    handleMouseMove(e) {
        if (this.draggedNode && this.currentMode === 'node') {
            const rect = e.currentTarget.getBoundingClientRect();
            const nodeId = this.draggedNode.dataset.nodeId;
            const node = this.nodes.get(nodeId);
            
            node.x = Math.max(25, Math.min(575, e.clientX - rect.left - this.dragOffset.x));
            node.y = Math.max(25, Math.min(475, e.clientY - rect.top - this.dragOffset.y));
            
            this.updateDisplay();
        }
    }

    handleMouseUp(e) {
        this.draggedNode = null;
    }

    addNode(x, y) {
        console.log('➕ Adding node at:', x, y);
        // Ensure node is within bounds
        x = Math.max(25, Math.min(575, x));
        y = Math.max(25, Math.min(475, y));

        const nodeId = this.nodeCounter.toString();
        this.nodes.set(nodeId, {
            id: nodeId,
            label: nodeId,
            x: x,
            y: y
        });

        console.log('✅ Node added:', nodeId, 'Total nodes:', this.nodes.size);
        this.nodeCounter++;
        this.updateDisplay();
        this.showStatus(`Added node ${nodeId} at (${Math.round(x)}, ${Math.round(y)})`);
    }

    handleEdgeMode(e) {
        if (e.target.classList.contains('node-circle')) {
            const nodeElement = e.target.closest('.node');
            const nodeId = nodeElement.dataset.nodeId;
            
            if (this.selectedNodes.includes(nodeId)) {
                // Deselect node
                this.selectedNodes = this.selectedNodes.filter(id => id !== nodeId);
                this.showStatus(`Deselected node ${nodeId}`);
            } else {
                // Select node
                this.selectedNodes.push(nodeId);
                this.showStatus(`Selected node ${nodeId}`);
                
                if (this.selectedNodes.length === 2) {
                    this.addEdge(this.selectedNodes[0], this.selectedNodes[1]);
                    this.selectedNodes = [];
                }
            }
            
            this.updateDisplay();
        }
    }

    handleDeleteMode(e) {
        if (e.target.classList.contains('node-circle')) {
            const nodeElement = e.target.closest('.node');
            const nodeId = nodeElement.dataset.nodeId;
            this.deleteNode(nodeId);
        } else if (e.target.classList.contains('edge')) {
            const edgeElement = e.target;
            const edgeIndex = parseInt(edgeElement.dataset.edgeIndex);
            this.deleteEdge(edgeIndex);
        }
    }

    addEdge(fromId, toId) {
        if (fromId === toId) {
            this.showStatus('Cannot create self-loop', 'error');
            return;
        }

        // Check if edge already exists
        const existingEdge = this.edges.find(edge => 
            (edge.from === fromId && edge.to === toId) ||
            (!this.isDirected && edge.from === toId && edge.to === fromId)
        );

        if (existingEdge) {
            this.showStatus('Edge already exists', 'error');
            return;
        }

        this.edges.push({
            from: fromId,
            to: toId,
            id: `${fromId}-${toId}`
        });

        this.updateDisplay();
        this.showStatus(`Added edge from ${fromId} to ${toId}`);
    }

    deleteNode(nodeId) {
        this.nodes.delete(nodeId);
        this.edges = this.edges.filter(edge => edge.from !== nodeId && edge.to !== nodeId);
        this.selectedNodes = this.selectedNodes.filter(id => id !== nodeId);
        this.updateDisplay();
        this.showStatus(`Deleted node ${nodeId}`);
    }

    deleteEdge(edgeIndex) {
        if (edgeIndex >= 0 && edgeIndex < this.edges.length) {
            const edge = this.edges[edgeIndex];
            this.edges.splice(edgeIndex, 1);
            this.updateDisplay();
            this.showStatus(`Deleted edge from ${edge.from} to ${edge.to}`);
        }
    }

    clearGraph() {
        this.nodes.clear();
        this.edges = [];
        this.selectedNodes = [];
        this.nodeCounter = 1;
        this.updateDisplay();
        this.showStatus('Graph cleared');
    }

    clearSelection() {
        this.selectedNodes = [];
        this.updateDisplay();
    }

    updateModeButtons() {
        // Update mode button states
        const modes = ['node', 'edge', 'delete'];
        modes.forEach(mode => {
            const btn = document.querySelector(`input[value="${mode}"]`).closest('.radio-label');
            if (this.currentMode === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    async findEulerTrail() {
        if (this.nodes.size === 0) {
            this.showStatus('Graph is empty', 'error');
            return;
        }

        try {
            this.showStatus('Finding Euler trail...', 'info');
            
            const graphData = {
                nodes: Array.from(this.nodes.keys()), // Send node IDs as array
                edges: this.edges.map(edge => ({
                    id: edge.id,
                    source: edge.from,
                    target: edge.to
                })),
                graph_type: this.isDirected ? 'directed' : 'undirected'
            };

            const response = await fetch('http://localhost:5001/api/euler-trail', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(graphData)
            });

            const result = await response.json();

            if (result.success) {
                if (result.trail && result.trail.length > 0) {
                    this.highlightEulerTrail(result.trail);
                    this.showEulerTrailModal(result);
                } else {
                    this.showStatus('No Euler trail exists for this graph', 'warning');
                }
            } else {
                this.showStatus(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Error finding Euler trail:', error);
            this.showStatus('Error connecting to server. Make sure the backend is running.', 'error');
        }
    }

    highlightEulerTrail(trail) {
        // Clear previous highlights
        document.querySelectorAll('.edge').forEach(edge => {
            edge.classList.remove('highlighted');
        });

        // Highlight trail edges with delay for animation
        trail.forEach((edgeStep, index) => {
            setTimeout(() => {
                // The backend returns steps with source/target, convert to our edge ID format
                const edgeId = `${edgeStep.source}-${edgeStep.target}`;
                const reverseEdgeId = `${edgeStep.target}-${edgeStep.source}`;
                
                const edgeElement = document.querySelector(`[data-edge-id="${edgeId}"]`) ||
                                 document.querySelector(`[data-edge-id="${reverseEdgeId}"]`);
                if (edgeElement) {
                    edgeElement.classList.add('highlighted');
                }
            }, index * 300);
        });
    }

    showEulerTrailModal(result) {
        const modal = document.getElementById('eulerTrailModal');
        const content = document.getElementById('eulerTrailContent');
        
        let html = `
            <div class="graph-info">
                <div class="info-item">
                    <span class="info-label">Trail Type:</span>
                    <span class="text-success">${result.trail_type}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Trail Length:</span>
                    <span>${result.trail.length} edges</span>
                </div>
            </div>
            <h4 style="margin: 20px 0 10px 0;">Trail Sequence:</h4>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace;">
        `;

        if (result.trail.length > 0) {
            const trailNodes = [result.trail[0].source];
            result.trail.forEach(step => trailNodes.push(step.target));
            html += trailNodes.join(' → ');
        }

        html += '</div>';
        
        if (result.details) {
            html += `
                <h4 style="margin: 20px 0 10px 0;">Details:</h4>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 0.9rem;">
                    ${result.details}
                </div>
            `;
        }

        content.innerHTML = html;
        modal.classList.add('show');
    }

    showHelpModal() {
        const modal = document.getElementById('helpModal');
        modal.classList.add('show');
    }

    updateDisplay() {
        this.renderGraph();
        this.updateGraphInfo();
    }

    renderGraph() {
        const svg = document.querySelector('#graphCanvas svg');
        
        // Clear existing content
        svg.innerHTML = `
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                        refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                </marker>
            </defs>
        `;

        // Render edges first (so they appear behind nodes)
        this.edges.forEach((edge, index) => {
            const fromNode = this.nodes.get(edge.from);
            const toNode = this.nodes.get(edge.to);
            
            if (fromNode && toNode) {
                this.renderEdge(svg, fromNode, toNode, edge, index);
            }
        });

        // Render nodes
        this.nodes.forEach(node => {
            this.renderNode(svg, node);
        });
    }

    renderEdge(svg, fromNode, toNode, edge, index) {
        const dx = toNode.x - fromNode.x;
        const dy = toNode.y - fromNode.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Calculate edge endpoints (offset by node radius)
        const nodeRadius = 25;
        const offsetX = (dx / distance) * nodeRadius;
        const offsetY = (dy / distance) * nodeRadius;
        
        const startX = fromNode.x + offsetX;
        const startY = fromNode.y + offsetY;
        const endX = toNode.x - offsetX;
        const endY = toNode.y - offsetY;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', startX);
        line.setAttribute('y1', startY);
        line.setAttribute('x2', endX);
        line.setAttribute('y2', endY);
        line.setAttribute('class', 'edge');
        line.setAttribute('data-edge-index', index);
        line.setAttribute('data-edge-id', edge.id);
        
        if (this.isDirected) {
            line.setAttribute('marker-end', 'url(#arrowhead)');
        }

        svg.appendChild(line);

        // Add edge weight/label if needed
        if (this.isDirected || this.edges.length < 20) {
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', midX);
            label.setAttribute('y', midY - 5);
            label.setAttribute('class', 'edge-label');
            label.textContent = this.isDirected ? '→' : '';
            
            svg.appendChild(label);
        }
    }

    renderNode(svg, node) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'node');
        group.setAttribute('data-node-id', node.id);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', 25);
        circle.setAttribute('class', `node-circle ${this.selectedNodes.includes(node.id) ? 'pending' : ''}`);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y);
        text.setAttribute('class', 'node-text');
        text.textContent = node.label;

        group.appendChild(circle);
        group.appendChild(text);
        svg.appendChild(group);
    }

    updateGraphInfo() {
        const nodeCount = this.nodes.size;
        const edgeCount = this.edges.length;
        
        // Calculate degrees
        const degrees = new Map();
        this.nodes.forEach(node => degrees.set(node.id, 0));
        
        this.edges.forEach(edge => {
            degrees.set(edge.from, (degrees.get(edge.from) || 0) + 1);
            if (!this.isDirected) {
                degrees.set(edge.to, (degrees.get(edge.to) || 0) + 1);
            }
        });

        // Check connectivity (simplified)
        let isConnected = nodeCount <= 1 || this.isGraphConnected();

        document.getElementById('nodeCount').textContent = nodeCount;
        document.getElementById('edgeCount').textContent = edgeCount;
        document.getElementById('graphConnected').textContent = isConnected ? 'Yes' : 'No';
        document.getElementById('graphConnected').className = isConnected ? 'text-success' : 'text-danger';
    }

    isGraphConnected() {
        if (this.nodes.size <= 1) return true;
        
        // Simple connectivity check using DFS
        const visited = new Set();
        const adjacency = new Map();
        
        // Build adjacency list
        this.nodes.forEach(node => adjacency.set(node.id, []));
        this.edges.forEach(edge => {
            adjacency.get(edge.from).push(edge.to);
            if (!this.isDirected) {
                adjacency.get(edge.to).push(edge.from);
            }
        });

        // DFS from first node
        const firstNode = this.nodes.keys().next().value;
        const stack = [firstNode];
        
        while (stack.length > 0) {
            const current = stack.pop();
            if (!visited.has(current)) {
                visited.add(current);
                adjacency.get(current).forEach(neighbor => {
                    if (!visited.has(neighbor)) {
                        stack.push(neighbor);
                    }
                });
            }
        }

        return visited.size === this.nodes.size;
    }

    showStatus(message, type = 'info') {
        const statusDisplay = document.getElementById('statusDisplay');
        const timestamp = new Date().toLocaleTimeString();
        
        let icon = '📝';
        if (type === 'error') icon = '❌';
        else if (type === 'success') icon = '✅';
        else if (type === 'warning') icon = '⚠️';
        else if (type === 'info') icon = 'ℹ️';
        
        const statusMessage = `[${timestamp}] ${icon} ${message}\n`;
        statusDisplay.textContent = statusMessage + statusDisplay.textContent;
        
        // Limit status display length
        const lines = statusDisplay.textContent.split('\n');
        if (lines.length > 50) {
            statusDisplay.textContent = lines.slice(0, 50).join('\n');
        }
    }

    zoom(factor) {
        // Simple zoom implementation - scale all coordinates
        this.nodes.forEach(node => {
            node.x = Math.max(25, Math.min(575, node.x * factor));
            node.y = Math.max(25, Math.min(475, node.y * factor));
        });
        this.updateDisplay();
    }

    resetView() {
        // Reset to default view
        this.updateDisplay();
        this.showStatus('View reset');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM Content Loaded');
    window.eulerApp = new EulerTrailBuilder();
    console.log('Euler Trail Builder initialized');
    
    // Test status message
    setTimeout(() => {
        if (window.eulerApp) {
            window.eulerApp.showStatus('🎉 Application loaded successfully! Click on the canvas to add nodes.', 'success');
        }
    }, 500);
});
