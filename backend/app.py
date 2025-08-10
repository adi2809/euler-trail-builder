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
    print(f"\n🔍 ANALYZING MIXED GRAPH:")
    print(f"📊 Nodes: {sorted(nodes)}")
    print(f"🔗 Total edges: {len(edges)}")
    
    # Separate directed and undirected edges
    directed_edges = [e for e in edges if e.get('directed', False)]
    undirected_edges = [e for e in edges if not e.get('directed', False)]
    
    print(f"➡️  Directed edges: {len(directed_edges)}")
    print(f"↔️  Undirected edges: {len(undirected_edges)}")
    
    for edge in directed_edges:
        print(f"   {edge['source']} → {edge['target']} (ID: {edge['id']})")
    for edge in undirected_edges:
        print(f"   {edge['source']} ↔ {edge['target']} (ID: {edge['id']})")
    
    # Calculate degrees more carefully for mixed graphs
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    
    # For directed edges: count in-degree and out-degree separately
    for edge in directed_edges:
        out_degree[edge['source']] += 1
        in_degree[edge['target']] += 1
    
    # For undirected edges: each contributes equally to both in and out degree
    for edge in undirected_edges:
        in_degree[edge['source']] += 1
        out_degree[edge['source']] += 1
        in_degree[edge['target']] += 1
        out_degree[edge['target']] += 1
    
    print(f"\n📈 DEGREE ANALYSIS:")
    for node in sorted(nodes):
        if in_degree[node] > 0 or out_degree[node] > 0:
            balance = out_degree[node] - in_degree[node]
            print(f"   Node {node}: in={in_degree[node]}, out={out_degree[node]}, balance={balance:+d}")
    
    # Check connectivity
    if not _mixed_connectivity_ok(nodes, edges):
        print("❌ Graph is not connected")
        return False, None, "Graph is not connected", {}
    
    print("✅ Graph is connected")
    
    # Analyze degree conditions for mixed Euler trail
    problematic_nodes = []
    start_candidates = []
    end_candidates = []
    
    for node in nodes:
        # Skip isolated nodes
        if in_degree[node] == 0 and out_degree[node] == 0:
            continue
            
        if in_degree[node] == out_degree[node]:
            continue  # Balanced node, good for Euler cycle
        elif out_degree[node] - in_degree[node] == 1:
            start_candidates.append(node)
        elif in_degree[node] - out_degree[node] == 1:
            end_candidates.append(node)
        else:
            problematic_nodes.append(node)
    
    print(f"\n🎯 EULER ANALYSIS:")
    print(f"   Start candidates (out-degree > in-degree by 1): {start_candidates}")
    print(f"   End candidates (in-degree > out-degree by 1): {end_candidates}")
    print(f"   Problematic nodes: {problematic_nodes}")
    
    if problematic_nodes:
        error_msg = f"Nodes {problematic_nodes} have invalid degree balance for Euler trail"
        print(f"❌ {error_msg}")
        return False, None, error_msg, {}
    
    # Determine if Euler trail exists
    if len(start_candidates) == 0 and len(end_candidates) == 0:
        # Euler cycle exists
        start_node = next((n for n in nodes if out_degree[n] > 0), None)
        print(f"🔄 Euler CYCLE found, starting from: {start_node}")
        return True, start_node, "Euler cycle found", {
            'type': 'cycle',
            'start': start_node,
            'directed_edges': len(directed_edges),
            'undirected_edges': len(undirected_edges)
        }
    elif len(start_candidates) == 1 and len(end_candidates) == 1:
        # Euler path exists
        print(f"🛤️  Euler PATH found: {start_candidates[0]} → {end_candidates[0]}")
        return True, start_candidates[0], "Euler path found", {
            'type': 'path',
            'start': start_candidates[0],
            'end': end_candidates[0],
            'directed_edges': len(directed_edges),
            'undirected_edges': len(undirected_edges)
        }
    else:
        error_msg = f"Invalid start/end configuration: {len(start_candidates)} starts, {len(end_candidates)} ends"
        print(f"❌ {error_msg}")
        return False, None, error_msg, {}

def _hierholzer_mixed(nodes: Set[str], edges: List[dict]) -> Optional[List[str]]:
    """Find Euler trail using Hierholzer's algorithm for mixed graphs."""
    # Build adjacency list with proper direction handling
    adj = defaultdict(list)
    
    for edge in edges:
        eid = edge['id']
        u, v = edge['source'], edge['target']
        is_directed = edge.get('directed', False)
        
        # For directed edges: u -> v only
        # For undirected edges: u <-> v (both directions)
        adj[u].append((eid, v))
        if not is_directed:
            adj[v].append((eid, u))
    
    # Debug adjacency list
    print(f"\n🔗 ADJACENCY LIST:")
    for node in sorted(adj.keys()):
        edges_str = ", ".join([f"{eid}→{target}" for eid, target in adj[node]])
        print(f"   {node}: [{edges_str}]")
    
    # Find starting point using our analysis
    ok, start, reason, info = _analyze_mixed_graph(nodes, edges)
    if not ok or start is None:
        print(f"❌ Mixed graph analysis failed: {reason}")
        return None
    
    print(f"🎯 Starting Hierholzer from node: {start}")
    print(f"📊 Analysis result: {info}")
    
    # Hierholzer's algorithm with circuit finding
    def find_circuit(start_node):
        """Find a circuit starting from start_node."""
        stack = [start_node]
        circuit = []
        used_edges = set()
        
        # Keep track of remaining edges from each vertex (local copy)
        remaining_edges = {node: list(adj[node]) for node in adj}
        
        while stack:
            curr = stack[-1]
            
            # Find an unused edge from current vertex
            found_edge = False
            for i, (eid, next_vertex) in enumerate(remaining_edges.get(curr, [])):
                if eid not in used_edges:
                    # Use this edge
                    used_edges.add(eid)
                    stack.append(next_vertex)
                    # Remove this edge from all adjacency lists
                    remaining_edges[curr].pop(i)
                    # Also remove the reverse edge if it's undirected
                    edge_obj = next(e for e in edges if e['id'] == eid)
                    if not edge_obj.get('directed', False):
                        # Remove reverse edge
                        for j, (rev_eid, rev_target) in enumerate(remaining_edges.get(next_vertex, [])):
                            if rev_eid == eid and rev_target == curr:
                                remaining_edges[next_vertex].pop(j)
                                break
                    found_edge = True
                    break
            
            if not found_edge:
                # No more edges from current vertex, add to circuit
                circuit.append(stack.pop())
        
        return circuit, used_edges
    
    # Start with a circuit from the starting node
    circuit, used_edges = find_circuit(start)
    
    # Keep adding circuits until all edges are used
    while len(used_edges) < len(edges):
        # Find a vertex in the current circuit that has unused edges
        start_vertex = None
        for vertex in circuit:
            remaining_count = sum(1 for eid, _ in adj.get(vertex, []) if eid not in used_edges)
            if remaining_count > 0:
                start_vertex = vertex
                break
        
        if start_vertex is None:
            print(f"❌ No vertex with unused edges found, but {len(edges) - len(used_edges)} edges remain")
            break
        
        # Find a circuit starting from this vertex
        new_circuit, new_used_edges = find_circuit(start_vertex)
        used_edges.update(new_used_edges)
        
        # Insert the new circuit into the main circuit at the start vertex
        insert_index = circuit.index(start_vertex)
        circuit = circuit[:insert_index] + new_circuit[::-1] + circuit[insert_index + 1:]
    
    # Reverse to get the correct order
    path = circuit[::-1]
    
    print(f"🛤️  Final constructed path: {' -> '.join(path)}")
    print(f"🔗 Used {len(used_edges)} of {len(edges)} edges")
    
    # Convert vertex path to edge sequence
    if len(path) < 2:
        print("❌ Path too short")
        return None
    
    edge_sequence = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        
        # Find the correct edge between u and v that hasn't been used in sequence
        found_edge = None
        for edge in edges:
            if edge['id'] in edge_sequence:
                continue  # Already used in sequence
                
            # Check if this edge connects u to v correctly
            if edge['source'] == u and edge['target'] == v:
                found_edge = edge['id']
                break
            elif not edge.get('directed', False) and edge['source'] == v and edge['target'] == u:
                found_edge = edge['id']
                break
        
        if found_edge:
            edge_sequence.append(found_edge)
            print(f"✅ Step {i+1}: {u} -> {v} using edge {found_edge}")
        else:
            print(f"❌ No edge found between {u} and {v}")
            # Debug: show available edges
            available_edges = [e for e in edges if e['id'] not in edge_sequence]
            print(f"   Available edges: {[(e['id'], e['source'], e['target'], e.get('directed', False)) for e in available_edges]}")
            return None
    
    success = len(edge_sequence) == len(edges)
    print(f"🎉 Trail construction {'successful' if success else 'failed'}: {len(edge_sequence)}/{len(edges)} edges")
    
    return edge_sequence if success else None

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
