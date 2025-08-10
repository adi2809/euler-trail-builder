# Flask Backend for Euler Trail Builder
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from collections import defaultdict, deque
from typing import List, Tuple, Optional, Set, Dict
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

# Enhanced functions for mixed graphs with multiple edges
def _mixed_connectivity_ok(nodes: Set[str], edges: List[dict]) -> bool:
    """Check if all non-isolated vertices are connected in a mixed graph."""
    # Build adjacency list treating all edges as undirected for connectivity
    adj = defaultdict(set)
    vertices_with_edges = set()
    
    for edge in edges:
        u, v = edge['source'], edge['target']
        adj[u].add(v)
        adj[v].add(u)
        vertices_with_edges.add(u)
        vertices_with_edges.add(v)
    
    if not vertices_with_edges:
        return True
    
    # BFS to check connectivity
    start = next(iter(vertices_with_edges))
    visited = {start}
    queue = deque([start])
    
    while queue:
        node = queue.popleft()
        for neighbor in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return visited == vertices_with_edges

def _analyze_mixed_graph(nodes: Set[str], edges: List[dict]) -> Tuple[bool, Optional[str], str, dict]:
    """Analyze mixed graph for Euler trail possibilities."""
    # Separate directed and undirected edges
    directed_edges = [e for e in edges if e.get('directed', False)]
    undirected_edges = [e for e in edges if not e.get('directed', False)]
    
    # Calculate degrees
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    undirected_degree = defaultdict(int)
    
    for edge in directed_edges:
        out_degree[edge['source']] += 1
        in_degree[edge['target']] += 1
    
    for edge in undirected_edges:
        undirected_degree[edge['source']] += 1
        undirected_degree[edge['target']] += 1
    
    # Check connectivity
    if not _mixed_connectivity_ok(nodes, edges):
        return False, None, "Graph is not connected", {}
    
    # Analyze degree conditions for mixed Euler trail
    problematic_nodes = []
    start_candidates = []
    end_candidates = []
    
    for node in nodes:
        total_in = in_degree[node] + undirected_degree[node]
        total_out = out_degree[node] + undirected_degree[node]
        
        # For mixed graphs, we need to be more flexible
        if total_in == total_out:
            continue  # Balanced node, good for Euler cycle
        elif total_out - total_in == 1:
            start_candidates.append(node)
        elif total_in - total_out == 1:
            end_candidates.append(node)
        else:
            problematic_nodes.append(node)
    
    if problematic_nodes:
        return False, None, f"Nodes {problematic_nodes} have invalid degree balance", {}
    
    # Determine if Euler trail exists
    if len(start_candidates) == 0 and len(end_candidates) == 0:
        # Euler cycle exists
        start_node = next((n for n in nodes if out_degree[n] + undirected_degree[n] > 0), None)
        return True, start_node, "Euler cycle found", {
            'type': 'cycle',
            'start': start_node,
            'directed_edges': len(directed_edges),
            'undirected_edges': len(undirected_edges)
        }
    elif len(start_candidates) == 1 and len(end_candidates) == 1:
        # Euler path exists
        return True, start_candidates[0], "Euler path found", {
            'type': 'path',
            'start': start_candidates[0],
            'end': end_candidates[0],
            'directed_edges': len(directed_edges),
            'undirected_edges': len(undirected_edges)
        }
    else:
        return False, None, f"Invalid start/end configuration: {len(start_candidates)} starts, {len(end_candidates)} ends", {}

def _hierholzer_mixed(nodes: Set[str], edges: List[dict]) -> Optional[List[str]]:
    """Find Euler trail using Hierholzer's algorithm for mixed graphs."""
    # Build adjacency list
    adj = defaultdict(list)
    edge_lookup = {}
    
    for edge in edges:
        eid = edge['id']
        u, v = edge['source'], edge['target']
        is_directed = edge.get('directed', False)
        
        edge_lookup[eid] = edge
        adj[u].append((eid, v, is_directed))
        
        if not is_directed:
            adj[v].append((eid, u, is_directed))
    
    # Find starting point
    ok, start, reason, info = _analyze_mixed_graph(nodes, edges)
    if not ok or start is None:
        return None
    
    # Hierholzer's algorithm
    stack = [start]
    path = []
    used_edges = set()
    
    # Copy adjacency lists for iteration
    adj_copy = {u: list(adj[u]) for u in adj}
    
    while stack:
        curr = stack[-1]
        found_edge = False
        
        # Find an unused edge from current vertex
        while adj_copy.get(curr):
            eid, next_vertex, is_directed = adj_copy[curr].pop()
            
            if eid in used_edges:
                continue
                
            used_edges.add(eid)
            stack.append(next_vertex)
            found_edge = True
            break
        
        if not found_edge:
            if len(stack) > 1:
                path.append(stack.pop())
            else:
                stack.pop()
    
    path.reverse()
    
    # Convert path to edge sequence
    if len(path) < 2:
        return None
    
    edge_sequence = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        # Find the edge between u and v
        for edge in edges:
            if edge['id'] not in [e for e in edge_sequence]:
                if ((edge['source'] == u and edge['target'] == v) or 
                    (not edge.get('directed', False) and edge['source'] == v and edge['target'] == u)):
                    edge_sequence.append(edge['id'])
                    break
    
    return edge_sequence if len(edge_sequence) == len(edges) else None

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
    """Find Euler trail for mixed directed/undirected graph with multiple edges."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided', 'trail': None}), 400
            
        nodes = set(data.get('nodes', []))
        edges = data.get('edges', [])
        
        if not edges:
            return jsonify({
                'success': False,
                'error': 'No edges provided',
                'trail': None,
                'analysis': None
            })
        
        # Check if this is a mixed graph or legacy format
        has_mixed_edges = any(isinstance(edge, dict) and 'directed' in edge for edge in edges)
        
        if has_mixed_edges:
            # Use new mixed graph algorithm
            ok, start, reason, analysis = _analyze_mixed_graph(nodes, edges)
            
            if not ok:
                return jsonify({
                    'success': False,
                    'error': reason,
                    'trail': None,
                    'analysis': analysis
                })
            
            # Find Euler trail
            trail = _hierholzer_mixed(nodes, edges)
            
            if trail is None:
                return jsonify({
                    'success': False,
                    'error': 'Could not construct Euler trail',
                    'trail': None,
                    'analysis': analysis
                })
            
            # Create trail steps
            edge_map = {edge['id']: edge for edge in edges}
            trail_steps = []
            
            for i, edge_id in enumerate(trail, 1):
                edge = edge_map[edge_id]
                trail_steps.append({
                    'step': i,
                    'edge_id': edge_id,
                    'source': edge['source'],
                    'target': edge['target'],
                    'directed': edge.get('directed', False)
                })
            
            return jsonify({
                'success': True,
                'error': None,
                'trail': trail_steps,
                'analysis': analysis
            })
        else:
            # Legacy format - convert and use original algorithm
            graph_type = data.get('graph_type', 'undirected')
            
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
    print("🚀 Starting Enhanced Euler Trail Builder Backend...")
    print("📍 API will be available at: http://localhost:5002")
    print("🌐 Frontend will be served at: http://localhost:5002")
    print("✨ New Features:")
    print("   • Multiple edges between same nodes")
    print("   • Mixed directed/undirected edges")
    print("   • Self-loops support")
    print("   • Enhanced graph analysis")
    app.run(debug=True, host='0.0.0.0', port=5002)
