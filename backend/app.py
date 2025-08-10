# Flask Backend for Euler Trail Builder
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from collections import defaultdict, deque
from typing import List, Tuple, Optional, Set
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Euler algorithm functions
def _undirected_connectivity_ok(nodes: Set[str], edges: List[Tuple[str, str]]) -> bool:
    """Check if all non-isolated vertices are connected."""
    deg = defaultdict(int)
    g = defaultdict(list)
    for u, v in edges:
        deg[u] += 1
        deg[v] += 1
        g[u].append(v)
        g[v].append(u)

    non_isolated = {u for u in nodes if deg[u] > 0}
    if not non_isolated:
        return True

    start = next(iter(non_isolated))
    seen = {start}
    q = deque([start])
    while q:
        x = q.popleft()
        for y in g[x]:
            if y not in seen:
                seen.add(y)
                q.append(y)
    return seen == non_isolated

def _choose_start_undirected(nodes: Set[str], edges: List[Tuple[str, str]]) -> Tuple[bool, Optional[str], str]:
    """Find start node for undirected Euler trail."""
    deg = defaultdict(int)
    for u, v in edges:
        deg[u] += 1
        deg[v] += 1

    odd = [u for u in nodes if deg[u] % 2 == 1]
    if not _undirected_connectivity_ok(nodes, edges):
        return False, None, "Graph is not connected"
    if len(odd) == 0:
        start = next((u for u in nodes if deg[u] > 0), None)
        if start is None:
            return False, None, "Graph has no edges"
        return True, start, ""
    if len(odd) == 2:
        return True, odd[0], ""
    return False, None, f"Found {len(odd)} vertices of odd degree (need 0 or 2)"

def _choose_start_directed(nodes: Set[str], edges: List[Tuple[str, str]]) -> Tuple[bool, Optional[str], str]:
    """Find start node for directed Euler trail."""
    indeg = defaultdict(int)
    outdeg = defaultdict(int)
    for u, v in edges:
        outdeg[u] += 1
        indeg[v] += 1

    start_candidates = []
    end_candidates = []
    for u in nodes:
        diff = outdeg[u] - indeg[u]
        if diff == 1:
            start_candidates.append(u)
        elif diff == -1:
            end_candidates.append(u)
        elif diff != 0:
            return False, None, f"Invalid degree balance at {u}"

    if len(start_candidates) == 0 and len(end_candidates) == 0:
        start = next((u for u in nodes if outdeg[u] > 0), None)
        if start is None:
            return False, None, "Graph has no edges"
        return True, start, ""
    if len(start_candidates) == 1 and len(end_candidates) == 1:
        return True, start_candidates[0], ""
    return False, None, "Need exactly one start and one end vertex"

def _hierholzer_undirected(nodes: Set[str], edge_items: List[Tuple[str, str, str]]) -> Optional[List[str]]:
    """Find Euler trail using Hierholzer's algorithm."""
    adj = defaultdict(list)
    for eid, u, v in edge_items:
        adj[u].append((eid, v))
        adj[v].append((eid, u))

    ok, start, _reason = _choose_start_undirected(nodes, [(u, v) for _, u, v in edge_items])
    if not ok or start is None:
        return None

    stack = [start]
    stack_e = []
    circuit = []
    used = set()
    iters = {u: list(adj[u]) for u in adj}

    while stack:
        v = stack[-1]
        while iters.get(v):
            eid, u = iters[v].pop()
            if eid in used:
                continue
            used.add(eid)
            stack.append(u)
            stack_e.append(eid)
            v = u
        stack.pop()
        if stack_e:
            circuit.append(stack_e.pop())

    circuit.reverse()
    return circuit if len(circuit) == len(edge_items) else None

def _hierholzer_directed(nodes: Set[str], edge_items: List[Tuple[str, str, str]]) -> Optional[List[str]]:
    """Find Euler trail for directed graph."""
    adj = defaultdict(list)
    for eid, u, v in edge_items:
        adj[u].append((eid, v))

    ok, start, _reason = _choose_start_directed(nodes, [(u, v) for _, u, v in edge_items])
    if not ok or start is None:
        return None

    stack = [start]
    stack_e = []
    circuit = []
    used = set()
    iters = {u: list(adj[u]) for u in adj}

    while stack:
        v = stack[-1]
        while iters.get(v):
            eid, u = iters[v].pop()
            if eid in used:
                continue
            used.add(eid)
            stack.append(u)
            stack_e.append(eid)
            v = u
        stack.pop()
        if stack_e:
            circuit.append(stack_e.pop())

    circuit.reverse()
    return circuit if len(circuit) == len(edge_items) else None

# API Routes

@app.route('/')
def serve_frontend():
    """Serve the React frontend."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('../frontend', path)

@app.route('/api/euler-trail', methods=['POST'])
def find_euler_trail():
    """Find Euler trail for the given graph."""
    try:
        data = request.json
        nodes = set(data.get('nodes', []))
        edges = data.get('edges', [])
        graph_type = data.get('graph_type', 'undirected')
        
        if not edges:
            return jsonify({
                'success': False,
                'error': 'No edges provided',
                'trail': None
            })
        
        # Convert edges to the format needed by algorithm
        edge_items = [(edge['id'], edge['source'], edge['target']) for edge in edges]
        
        if graph_type == 'undirected':
            trail = _hierholzer_undirected(nodes, edge_items)
            if trail is None:
                ok, start, reason = _choose_start_undirected(nodes, [(e['source'], e['target']) for e in edges])
                return jsonify({
                    'success': False,
                    'error': reason or 'No Euler trail exists',
                    'trail': None
                })
        else:  # directed
            trail = _hierholzer_directed(nodes, edge_items)
            if trail is None:
                ok, start, reason = _choose_start_directed(nodes, [(e['source'], e['target']) for e in edges])
                return jsonify({
                    'success': False,
                    'error': reason or 'No Euler trail exists',
                    'trail': None
                })
        
        # Create trail with steps
        edge_map = {edge['id']: edge for edge in edges}
        trail_steps = []
        for i, edge_id in enumerate(trail, 1):
            edge = edge_map[edge_id]
            trail_steps.append({
                'step': i,
                'edge_id': edge_id,
                'source': edge['source'],
                'target': edge['target']
            })
        
        return jsonify({
            'success': True,
            'error': None,
            'trail': trail_steps
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'trail': None
        }), 500

@app.route('/api/graph-info', methods=['POST'])
def get_graph_info():
    """Get information about the graph structure."""
    try:
        data = request.json
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        graph_type = data.get('graph_type', 'undirected')
        
        # Calculate degrees
        degrees = defaultdict(lambda: {'in': 0, 'out': 0, 'total': 0})
        
        for edge in edges:
            source, target = edge['source'], edge['target']
            if graph_type == 'directed':
                degrees[source]['out'] += 1
                degrees[target]['in'] += 1
            else:
                degrees[source]['total'] += 1
                degrees[target]['total'] += 1
        
        # Prepare node info
        node_info = []
        for node in nodes:
            if graph_type == 'directed':
                node_info.append({
                    'id': node,
                    'in_degree': degrees[node]['in'],
                    'out_degree': degrees[node]['out'],
                    'total_degree': degrees[node]['in'] + degrees[node]['out']
                })
            else:
                node_info.append({
                    'id': node,
                    'degree': degrees[node]['total']
                })
        
        return jsonify({
            'nodes': node_info,
            'edge_count': len(edges),
            'node_count': len(nodes),
            'graph_type': graph_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Euler Trail Builder Backend...")
    print("📍 API will be available at: http://localhost:5001")
    print("🌐 Frontend will be served at: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
