# Flask Backend for Euler Trail Builder
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from collections import defaultdict, deque
from typing import List, Tuple, Optional, Set, Dict
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# --- Utilities ---
def _normalize_graph_payload(data: dict) -> Tuple[Set[str], List[dict], Dict[str, object], Dict[str, object]]:
    """Normalize nodes/edges and provide mappings.

    Returns:
    - norm_nodes: set of node ids as strings
    - norm_edges: list of edges with 'source'/'target' as strings and 'id' as string
    - norm_to_orig: mapping from normalized node id (str) to original id (any JSON type)
    - orig_to_norm: mapping from original id (any JSON type) to normalized (str)
    """
    raw_nodes = data.get('nodes', []) or []
    raw_edges = data.get('edges', []) or []

    orig_to_norm: Dict[object, str] = {}
    norm_to_orig: Dict[str, object] = {}

    def to_norm(x):
        if x in orig_to_norm:
            return orig_to_norm[x]
        s = str(x)
        orig_to_norm[x] = s
        norm_to_orig[s] = x
        return s

    # Normalize edges first (guarantees we capture all seen nodes)
    norm_edges: List[dict] = []
    nodes_from_edges: Set[str] = set()
    for e in raw_edges:
        eid = str(e.get('id'))
        u = to_norm(e.get('source'))
        v = to_norm(e.get('target'))
        directed = bool(e.get('directed', False))
        norm_edges.append({'id': eid, 'source': u, 'target': v, 'directed': directed})
        nodes_from_edges.add(u)
        nodes_from_edges.add(v)

    # Normalize provided nodes; ensure mapping exists even for isolated nodes
    for n in raw_nodes:
        to_norm(n)

    norm_nodes = set(norm_to_orig.keys())
    if not norm_nodes:
        norm_nodes = nodes_from_edges
    else:
        norm_nodes |= nodes_from_edges

    return norm_nodes, norm_edges, norm_to_orig, orig_to_norm

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

def _hierholzer_undirected(nodes: Set[str], edge_items: List[Tuple[str, str, str]]) -> Optional[List[Tuple[str, str, str]]]:
    """Find Euler trail for undirected graph using Hierholzer's algorithm.

    Returns oriented steps as (edge_id, src, dst).
    """
    adj = defaultdict(list)
    for eid, u, v in edge_items:
        adj[u].append((eid, v))
        adj[v].append((eid, u))

    ok, start, _reason = _choose_start_undirected(nodes, [(u, v) for _, u, v in edge_items])
    if not ok or start is None:
        return None

    stack = [start]
    stack_e: List[Tuple[str, str, str]] = []  # (eid, from, to)
    circuit: List[Tuple[str, str, str]] = []
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
            stack_e.append((eid, v, u))
            v = u
        stack.pop()
        if stack_e:
            circuit.append(stack_e.pop())

    circuit.reverse()
    return circuit if len(circuit) == len(edge_items) else None

def _hierholzer_directed(nodes: Set[str], edge_items: List[Tuple[str, str, str]]) -> Optional[List[Tuple[str, str, str]]]:
    """Find Euler trail for directed graph. Returns (edge_id, src, dst)."""
    adj = defaultdict(list)
    for eid, u, v in edge_items:
        adj[u].append((eid, v))

    ok, start, _reason = _choose_start_directed(nodes, [(u, v) for _, u, v in edge_items])
    if not ok or start is None:
        return None

    stack = [start]
    stack_e: List[Tuple[str, str, str]] = []
    circuit: List[Tuple[str, str, str]] = []
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
            stack_e.append((eid, v, u))
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
        # For connectivity, we consider both directions regardless of edge type
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
    """Analyze mixed graph and propose a start node.

    More permissive: only require connectivity. We'll attempt construction even if
    degree balances look odd, since undirected edges can be oriented during traversal.
    """
    print("\n🔍 ANALYZING MIXED GRAPH:")
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
    
    # Degree tallies. Keep both: (a) directed-only in/out, (b) total incident degree.
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    total_deg = defaultdict(int)

    # Directed edges contribute to in/out and incident totals
    for edge in directed_edges:
        u, v = edge['source'], edge['target']
        out_degree[u] += 1
        in_degree[v] += 1
        total_deg[u] += 1
        total_deg[v] += 1

    # Undirected edges are incident to both endpoints; they don't change net out-in
    for edge in undirected_edges:
        u, v = edge['source'], edge['target']
        total_deg[u] += 1
        total_deg[v] += 1
    
    print("\n📈 DEGREE ANALYSIS:")
    for node in sorted(nodes):
        if total_deg[node] > 0 or in_degree[node] > 0 or out_degree[node] > 0:
            balance = out_degree[node] - in_degree[node]
            print(f"   Node {node}: in={in_degree[node]}, out={out_degree[node]}, balance={balance:+d}, incident={total_deg[node]}")
    
    # Check connectivity
    if not _mixed_connectivity_ok(nodes, edges):
        print("❌ Graph is not connected")
        return False, None, "Graph is not connected", {}
    
    print("✅ Graph is connected")
    
    # Propose a start vertex
    start_candidates = [n for n in nodes if (out_degree[n] - in_degree[n]) == 1]
    end_candidates = [n for n in nodes if (in_degree[n] - out_degree[n]) == 1]

    # Prefer the classical directed start if it uniquely exists
    if len(start_candidates) == 1 and len(end_candidates) == 1:
        start_node = start_candidates[0]
        print(f"🛤️  Proposed start: {start_node} (directed start/end pattern)")
        return True, start_node, "Proposed start based on directed imbalance", {
            'type': 'path-or-cycle',
            'start': start_node,
            'end': end_candidates[0],
            'directed_edges': len(directed_edges),
            'undirected_edges': len(undirected_edges)
        }

    # Otherwise pick any vertex incident to at least one edge
    start_node = next((n for n in nodes if total_deg[n] > 0 or out_degree[n] > 0), None)
    if start_node is None:
        return False, None, "Graph has no edges", {}
        print(f"🔄 Proposed start (generic): {start_node}")
    return True, start_node, "Proposed generic start (connectivity ok)", {
        'type': 'unknown',
        'start': start_node,
        'directed_edges': len(directed_edges),
        'undirected_edges': len(undirected_edges)
    }

def _hierholzer_mixed(nodes: Set[str], edges: List[dict]) -> Optional[List[Tuple[str, str, str]]]:
    """Proper Hierholzer traversal for mixed graphs (directed + undirected).

    Builds a single continuous trail (no teleports). Returns a list of edge IDs
    in traversal order, or None if an Euler trail doesn't exist.
    """

    # Analyze to pick a valid starting vertex
    ok, start, reason, info = _analyze_mixed_graph(nodes, edges)
    if not ok or start is None:
        print(f"❌ Mixed graph analysis failed: {reason}")
        return None

    print(f"🖊️  Starting Hierholzer traversal at: {start}")

    # Map edge id -> edge for quick lookup
    edge_map: Dict[str, dict] = {e['id']: e for e in edges}

    # Build adjacency: for directed edges add u->v only; for undirected add both ways.
    adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for e in edges:
        u, v = e['source'], e['target']
        if e.get('directed', False):
            adj[u].append((e['id'], v))
        else:
            adj[u].append((e['id'], v))
            adj[v].append((e['id'], u))

    # Iterators we can pop from as we traverse
    iters: Dict[str, List[Tuple[str, str]]] = {u: list(adj[u]) for u in adj}

    used: Set[str] = set()  # edge ids used
    stack: List[str] = [start]
    stack_e: List[Tuple[str, str, str]] = []  # (eid, from, to)
    circuit: List[Tuple[str, str, str]] = []  # oriented edges in reverse

    while stack:
        v = stack[-1]
        # Advance along unused outgoing edges from v
        progressed = False
        while iters.get(v):
            eid, u = iters[v].pop()
            if eid in used:
                continue
            # Ensure directed constraint: we only added legal directions above
            used.add(eid)
            stack.append(u)
            stack_e.append((eid, v, u))
            progressed = True
            v = u
        if not progressed:
            # Backtrack, add the last edge to circuit
            stack.pop()
            if stack_e:
                circuit.append(stack_e.pop())

    circuit.reverse()

    # Validate: we must have used exactly all edges once
    if len(circuit) != len(edges):
        print("❌ Hierholzer failed: circuit doesn't cover all edges")
        return None

    print("✅ Successfully built a continuous Euler trail for mixed graph")
    return circuit

# Resolve absolute path to the frontend directory (../frontend relative to this file)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FRONTEND_DIR = os.path.abspath(os.path.join(_BASE_DIR, '..', 'frontend'))

@app.route('/')
def serve_frontend():
    """Serve index.html for the app root."""
    return send_from_directory(_FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory(_FRONTEND_DIR, path)

@app.route('/api/euler-trail', methods=['POST'])
def find_euler_trail():
    """Find Euler trail for mixed directed/undirected graph with multiple edges."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided', 'trail': None}), 400

        nodes, edges, norm_to_orig, orig_to_norm = _normalize_graph_payload(data)

        if not edges:
            return jsonify({
                'success': False,
                'error': 'No edges provided',
                'trail': None,
                'analysis': None
            })
        
        # Choose algorithm based on edge types
        all_directed = all(e.get('directed', False) for e in edges)
        none_directed = all(not e.get('directed', False) for e in edges)

        analysis = None
        if none_directed:
            # Undirected
            ok, start, reason = _choose_start_undirected(nodes, [(e['source'], e['target']) for e in edges])
            if not ok or start is None:
                return jsonify({'success': False, 'error': reason, 'trail': None, 'analysis': {'type': 'undirected'}})
            trail = _hierholzer_undirected(nodes, [(e['id'], e['source'], e['target']) for e in edges])
        elif all_directed:
            # Directed
            ok, start, reason = _choose_start_directed(nodes, [(e['source'], e['target']) for e in edges])
            if not ok or start is None:
                return jsonify({'success': False, 'error': reason, 'trail': None, 'analysis': {'type': 'directed'}})
            trail = _hierholzer_directed(nodes, [(e['id'], e['source'], e['target']) for e in edges])
        else:
            # Mixed
            ok, start, reason, analysis = _analyze_mixed_graph(nodes, edges)
            if not ok or start is None:
                return jsonify({'success': False, 'error': reason, 'trail': None, 'analysis': analysis})
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

        for i, (edge_id, src, dst) in enumerate(trail, 1):
            edge = edge_map[edge_id]
            # Map back to original node IDs for the response
            src_orig = norm_to_orig.get(src, src)
            dst_orig = norm_to_orig.get(dst, dst)
            trail_steps.append({
                'step': i,
                'edge_id': edge_id,
                'source': src_orig,
                'target': dst_orig,
                'directed': edge.get('directed', False)
            })

        return jsonify({
            'success': True,
            'error': None,
            'trail': trail_steps,
            'analysis': analysis
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
        nodes, edges, norm_to_orig, orig_to_norm = _normalize_graph_payload(data)

        # Calculate degrees for mixed graph
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)

        # Separate directed and undirected edges
        directed_count = 0
        undirected_count = 0

        for edge in edges:
            source, target = edge['source'], edge['target']
            is_directed = edge.get('directed', False)

            if is_directed:
                directed_count += 1
                out_degree[source] += 1
                in_degree[target] += 1
            else:
                undirected_count += 1
                out_degree[source] += 1
                in_degree[source] += 1
                out_degree[target] += 1
                in_degree[target] += 1

        # Prepare node info
        node_info = []
        for node in nodes:
            node_info.append({
                'id': norm_to_orig.get(node, node),
                'in_degree': in_degree[node],
                'out_degree': out_degree[node],
                'total_degree': in_degree[node] + out_degree[node]
            })

        return jsonify({
            'nodes': node_info,
            'edge_count': len(edges),
            'node_count': len(nodes),
            'directed_edges': directed_count,
            'undirected_edges': undirected_count
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
