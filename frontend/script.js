// Enhanced Euler Trail Builder - Multiple Edges & Mixed Types Support

class EulerTrailBuilder {
    constructor() {
        console.log('🎯 Enhanced EulerTrailBuilder constructor called');
        this.nodes = new Map();
        this.edges = [];
        this.nodeCounter = 1;
        this.edgeCounter = 1;
        this.selectedNodes = [];
        this.currentMode = 'node';
        this.currentEdgeType = 'undirected'; // New: track edge type
        this.isDirected = false; // Keep for backward compatibility
        this.isAddingNode = false;
        this.draggedNode = null;
        this.dragOffset = { x: 0, y: 0 };
        
        console.log('🚀 Initializing Enhanced EulerTrailBuilder...');
        this.init();
    }

    init() {
        console.log('⚙️ Setting up enhanced event listeners...');
        this.setupEventListeners();
        this.setupModals();
        this.updateDisplay();
        console.log('✅ Enhanced EulerTrailBuilder initialized successfully');
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

        // Edge type selection (NEW)
        document.querySelectorAll('input[name="edgeType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentEdgeType = e.target.value;
                this.showStatus(`Edge type set to ${e.target.value}`);
            });
        });

        // Graph type selection (keep for compatibility)
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

        // Print trail button
        document.getElementById('printTrail').addEventListener('click', () => {
            this.printTrail();
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
        if (!this.nodes.has(fromId) || !this.nodes.has(toId)) {
            this.showStatus('Cannot create edge: one or both nodes do not exist', 'error');
            return;
        }

        // Create edge with current edge type (allow multiple edges between same nodes)
        const isDirected = this.currentEdgeType === 'directed';
        const edge = {
            from: fromId,
            to: toId,
            id: `edge_${this.edgeCounter++}`,
            source: fromId,  // For API compatibility
            target: toId,    // For API compatibility
            directed: isDirected
        };

        this.edges.push(edge);
        
        // Count existing edges between these nodes
        const existingEdges = this.edges.filter(e => 
            (e.from === fromId && e.to === toId) ||
            (!e.directed && e.from === toId && e.to === fromId)
        );
        
        const edgeTypeStr = isDirected ? 'directed' : 'undirected';
        this.showStatus(`✅ Added ${edgeTypeStr} edge ${fromId} → ${toId} (${existingEdges.length} total between these nodes)`);
        this.updateDisplay();
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
                nodes: Array.from(this.nodes.keys()),
                edges: this.edges.map(edge => ({
                    id: edge.id,
                    source: edge.from,
                    target: edge.to,
                    directed: edge.directed || false
                }))
            };

            const response = await fetch('http://localhost:5002/api/euler-trail', {
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
        
        // Store trail data for printing
        this.currentTrailResult = result;
        
        let html = `
            <div class="graph-info">
                <div class="info-item">
                    <span class="info-label">Trail Type:</span>
                    <span class="text-success">${result.analysis?.type || 'path'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Trail Length:</span>
                    <span>${result.trail.length} edges</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Directed Edges:</span>
                    <span style="color: #e74c3c;">${result.analysis?.directed_edges || 0}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Undirected Edges:</span>
                    <span style="color: #2c3e50;">${result.analysis?.undirected_edges || 0}</span>
                </div>
            </div>
            <h4 style="margin: 20px 0 10px 0;">Trail Sequence:</h4>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 16px; line-height: 1.5;">
        `;

        if (result.trail.length > 0) {
            const trailNodes = [result.trail[0].source];
            result.trail.forEach(step => trailNodes.push(step.target));
            html += trailNodes.join(' → ');
        }

        html += '</div>';
        
        // Add detailed step-by-step trail
        if (result.trail.length > 0) {
            html += `
                <h4 style="margin: 20px 0 10px 0;">Step-by-Step Trail:</h4>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto;">
            `;
            result.trail.forEach((step, index) => {
                const edgeType = step.directed ? '→' : '↔';
                const edgeColor = step.directed ? '#e74c3c' : '#2c3e50';
                html += `
                    <div style="margin: 5px 0; font-family: monospace;">
                        <span style="color: #6c757d;">Step ${step.step}:</span>
                        <span style="color: ${edgeColor}; font-weight: bold;">
                            ${step.source} ${edgeType} ${step.target}
                        </span>
                        <span style="color: #6c757d; font-size: 12px;">(Edge ID: ${step.edge_id})</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        content.innerHTML = html;
        modal.classList.add('show');
    }

    showHelpModal() {
        const modal = document.getElementById('helpModal');
        modal.classList.add('show');
    }

    printTrail() {
        if (!this.currentTrailResult) {
            alert('No trail to print. Please find an Euler trail first.');
            return;
        }

        const result = this.currentTrailResult;
        
        // Create a printable version
        let printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Euler Trail - Printable Version</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        line-height: 1.6; 
                    }
                    .header { 
                        text-align: center; 
                        border-bottom: 2px solid #333; 
                        padding-bottom: 10px; 
                        margin-bottom: 20px; 
                    }
                    .info { 
                        background: #f8f9fa; 
                        padding: 15px; 
                        border-radius: 5px; 
                        margin: 10px 0; 
                    }
                    .trail-sequence { 
                        background: #e9ecef; 
                        padding: 15px; 
                        border-radius: 5px; 
                        font-family: monospace; 
                        font-size: 16px; 
                        margin: 15px 0; 
                    }
                    .step { 
                        margin: 5px 0; 
                        padding: 5px; 
                        border-left: 3px solid #007bff; 
                        padding-left: 10px; 
                    }
                    .directed { color: #e74c3c; }
                    .undirected { color: #2c3e50; }
                    @media print {
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🛤️ Euler Trail Result</h1>
                    <p>Generated on ${new Date().toLocaleString()}</p>
                </div>
                
                <div class="info">
                    <h3>Graph Information</h3>
                    <p><strong>Trail Type:</strong> ${result.analysis?.type || 'path'}</p>
                    <p><strong>Total Edges:</strong> ${result.trail.length}</p>
                    <p><strong>Directed Edges:</strong> ${result.analysis?.directed_edges || 0}</p>
                    <p><strong>Undirected Edges:</strong> ${result.analysis?.undirected_edges || 0}</p>
                </div>
                
                <h3>Trail Sequence</h3>
                <div class="trail-sequence">`;
        
        if (result.trail.length > 0) {
            const trailNodes = [result.trail[0].source];
            result.trail.forEach(step => trailNodes.push(step.target));
            printContent += trailNodes.join(' → ');
        }
        
        printContent += `</div>
                
                <h3>Step-by-Step Details</h3>`;
        
        result.trail.forEach((step, index) => {
            const edgeType = step.directed ? '→' : '↔';
            const edgeClass = step.directed ? 'directed' : 'undirected';
            printContent += `
                <div class="step">
                    <strong>Step ${step.step}:</strong>
                    <span class="${edgeClass}">${step.source} ${edgeType} ${step.target}</span>
                    <span style="color: #6c757d; font-size: 12px;">(Edge ID: ${step.edge_id})</span>
                </div>
            `;
        });
        
        printContent += `
                <div style="margin-top: 30px; font-size: 12px; color: #6c757d; text-align: center;">
                    Generated by Enhanced Euler Trail Builder
                </div>
            </body>
            </html>
        `;
        
        // Open print window
        const printWindow = window.open('', '_blank');
        printWindow.document.write(printContent);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
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

        // Count multiple edges between same nodes for curvature
        const sameEdges = this.edges.filter(e => 
            (e.from === edge.from && e.to === edge.to) ||
            (!e.directed && !edge.directed && e.from === edge.to && e.to === edge.from)
        );
        const edgeIndex = sameEdges.findIndex(e => e.id === edge.id);
        const totalSameEdges = sameEdges.length;

        if (totalSameEdges > 1 || edge.from === edge.to) {
            // Create curved edge for multiple edges or self-loops
            this.renderCurvedEdge(svg, startX, startY, endX, endY, edge, edgeIndex, totalSameEdges);
        } else {
            // Single straight edge
            this.renderStraightEdge(svg, startX, startY, endX, endY, edge, index);
        }
    }

    renderStraightEdge(svg, startX, startY, endX, endY, edge, index) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', startX);
        line.setAttribute('y1', startY);
        line.setAttribute('x2', endX);
        line.setAttribute('y2', endY);
        line.setAttribute('class', 'edge');
        line.setAttribute('data-edge-index', index);
        line.setAttribute('data-edge-id', edge.id);
        
        // Different colors for directed vs undirected
        if (edge.directed) {
            line.setAttribute('stroke', '#e74c3c'); // Red for directed
            line.setAttribute('marker-end', 'url(#arrowhead)');
        } else {
            line.setAttribute('stroke', '#3498db'); // Blue for undirected
        }
        
        line.setAttribute('stroke-width', '3');

        svg.appendChild(line);
    }

    renderCurvedEdge(svg, startX, startY, endX, endY, edge, edgeIndex, totalEdges) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        if (edge.from === edge.to) {
            // Self-loop
            const loopRadius = 30;
            const offsetAngle = (edgeIndex * 60) - 30; // Spread multiple self-loops
            const fromNode = this.nodes.get(edge.from);
            const centerX = fromNode.x + loopRadius * Math.cos(offsetAngle * Math.PI / 180);
            const centerY = fromNode.y + loopRadius * Math.sin(offsetAngle * Math.PI / 180);
            
            path.setAttribute('d', `M ${fromNode.x} ${fromNode.y} Q ${centerX} ${centerY} ${fromNode.x} ${fromNode.y}`);
        } else {
            // Multiple edges - create curves
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            
            // Calculate perpendicular offset
            const dx = endX - startX;
            const dy = endY - startY;
            const length = Math.sqrt(dx * dx + dy * dy);
            
            if (length > 0) {
                const offset = (edgeIndex - (totalEdges - 1) / 2) * 30;
                const perpX = -dy / length * offset;
                const perpY = dx / length * offset;
                
                const controlX = midX + perpX;
                const controlY = midY + perpY;
                
                path.setAttribute('d', `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`);
            }
        }
        
        path.setAttribute('stroke', edge.directed ? '#e74c3c' : '#3498db');
        path.setAttribute('stroke-width', '3');
        path.setAttribute('fill', 'none');
        path.setAttribute('data-edge-id', edge.id);
        path.setAttribute('class', 'edge');
        
        if (edge.directed) {
            path.setAttribute('marker-end', 'url(#arrowhead)');
        }
        
        svg.appendChild(path);
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
        const directedCount = this.edges.filter(e => e.directed).length;
        const undirectedCount = this.edges.filter(e => !e.directed).length;
        
        // Count multiple edges between same node pairs
        const edgePairs = new Map();
        this.edges.forEach(edge => {
            const key = [edge.from, edge.to].sort().join('-');
            edgePairs.set(key, (edgePairs.get(key) || 0) + 1);
        });
        const multipleEdgePairs = Array.from(edgePairs.values()).filter(count => count > 1).length;

        // Check connectivity (simplified)
        let isConnected = nodeCount <= 1 || this.isGraphConnected();

        document.getElementById('nodeCount').textContent = nodeCount;
        document.getElementById('edgeCount').textContent = edgeCount;
        
        // Update enhanced statistics with correct IDs
        const directedCountEl = document.getElementById('directedEdgeCount');
        const undirectedCountEl = document.getElementById('undirectedEdgeCount');
        const multipleEdgesEl = document.getElementById('multipleEdgeCount');
        
        if (directedCountEl) directedCountEl.textContent = directedCount;
        if (undirectedCountEl) undirectedCountEl.textContent = undirectedCount;
        if (multipleEdgesEl) multipleEdgesEl.textContent = multipleEdgePairs;

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
