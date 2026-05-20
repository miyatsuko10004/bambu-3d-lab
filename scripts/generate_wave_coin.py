#!/usr/bin/env python3
import math
import os
import sys

class Facet:
    def __init__(self, v1, v2, v3):
        self.v1 = v1  # (x, y, z)
        self.v2 = v2
        self.v3 = v3
        self.normal = self.calculate_normal()

    def calculate_normal(self):
        # Calculate normal vector using cross product
        u = (self.v2[0] - self.v1[0], self.v2[1] - self.v1[1], self.v2[2] - self.v1[2])
        v = (self.v3[0] - self.v1[0], self.v3[1] - self.v1[1], self.v3[2] - self.v1[2])
        nx = u[1] * v[2] - u[2] * v[1]
        ny = u[2] * v[0] - u[0] * v[2]
        nz = u[0] * v[1] - u[1] * v[0]
        l = math.sqrt(nx**2 + ny**2 + nz**2)
        if l == 0:
            return (0.0, 0.0, 0.0)
        return (nx / l, ny / l, nz / l)

def write_ascii_stl(facets, filepath, name="wave_coin"):
    with open(filepath, 'w') as f:
        f.write(f"solid {name}\n")
        for facet in facets:
            f.write(f"  facet normal {facet.normal[0]:.6f} {facet.normal[1]:.6f} {facet.normal[2]:.6f}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {facet.v1[0]:.6f} {facet.v1[1]:.6f} {facet.v1[2]:.6f}\n")
            f.write(f"      vertex {facet.v2[0]:.6f} {facet.v2[1]:.6f} {facet.v2[2]:.6f}\n")
            f.write(f"      vertex {facet.v3[0]:.6f} {facet.v3[1]:.6f} {facet.v3[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write(f"endsolid {name}\n")

def generate_wave_coin():
    # Parameters
    R_max = 20.0       # Coin radius in mm (diameter = 40mm)
    H_base = 5.0       # Base height in mm
    D_dep = 1.2        # Max depth of thumb depression in mm
    A_wave = 0.4       # Amplitude of waves in mm
    F_r = 3.0          # Frequency of radial waves (concentric rings)
    F_theta = 8.0      # Frequency of angular waves (ripple effect)
    
    A_knurl = 0.4      # Knurling amplitude on the edge
    N_knurl = 60       # Number of knurled ridges on the edge
    
    # Grid resolution
    M = 30             # Radial divisions
    N = 120            # Angular divisions
    
    facets = []
    
    # Helper to calculate Z on the top surface
    def get_z_top(r, theta):
        # 1. Thumb depression (concave center)
        # Using a smooth cosine curve for the depression
        # at r=0, depression is -D_dep, at r=R_max, depression is 0
        depression = -D_dep * (1.0 - (r / R_max)**2) if r < R_max else 0.0
        
        # 2. Mathematical waves
        # Radial concentric waves combined with angular ripples
        # Creates a beautiful "sunburst ripple" texture
        wave = A_wave * math.sin(F_r * math.pi * (r / R_max)) * math.cos(F_theta * theta)
        
        # 3. Smooth blend near the edge (waves fade out near the absolute edge to keep it clean)
        edge_blend = 1.0 - (r / R_max)**8
        
        return H_base + depression + (wave * max(0.0, edge_blend))

    # Helper to calculate edge radius with knurling
    def get_r_edge(theta):
        return R_max + A_knurl * math.cos(N_knurl * theta)

    # 1. Generate TOP surface
    # We will generate a grid of vertices on the top surface
    # top_vertices[i][j] where i is radial index (0 to M) and j is angular index (0 to N-1)
    top_vertices = []
    for i in range(M + 1):
        row = []
        r = (i / M) * R_max
        for j in range(N):
            theta = (j / N) * 2 * math.pi
            
            # Apply edge knurling to the outermost radius
            current_r = r
            if i == M:
                current_r = get_r_edge(theta)
                
            x = current_r * math.cos(theta)
            y = current_r * math.sin(theta)
            z = get_z_top(current_r, theta)
            row.append((x, y, z))
        top_vertices.append(row)

    # Top surface facets
    # Center cap (i = 0 to 1) - triangles connecting to center point (0, 0, z_center)
    z_center = get_z_top(0.0, 0.0)
    center_pt = (0.0, 0.0, z_center)
    for j in range(N):
        next_j = (j + 1) % N
        # Triangle from center to row 1 vertices
        # Clockwise/Counter-clockwise check for normal pointing UP
        # Vertex order: center -> (1, next_j) -> (1, j)
        facets.append(Facet(center_pt, top_vertices[1][next_j], top_vertices[1][j]))

    # Outer rings (i = 1 to M-1) - quads split into 2 triangles
    for i in range(1, M):
        for j in range(N):
            next_j = (j + 1) % N
            v_curr_inner = top_vertices[i][j]
            v_next_inner = top_vertices[i][next_j]
            v_curr_outer = top_vertices[i+1][j]
            v_next_outer = top_vertices[i+1][next_j]
            
            # Triangle 1
            facets.append(Facet(v_curr_inner, v_next_outer, v_curr_outer))
            # Triangle 2
            facets.append(Facet(v_curr_inner, v_next_inner, v_next_outer))

    # 2. Generate BOTTOM surface (Flat at z = 0)
    bottom_vertices = []
    for i in range(M + 1):
        row = []
        r = (i / M) * R_max
        for j in range(N):
            theta = (j / N) * 2 * math.pi
            
            current_r = r
            if i == M:
                current_r = get_r_edge(theta)
                
            x = current_r * math.cos(theta)
            y = current_r * math.sin(theta)
            z = 0.0  # Flat bottom
            row.append((x, y, z))
        bottom_vertices.append(row)

    # Bottom surface facets (Normals must point DOWN, so reverse winding)
    bottom_center = (0.0, 0.0, 0.0)
    for j in range(N):
        next_j = (j + 1) % N
        # Vertex order: center -> (1, j) -> (1, next_j)
        facets.append(Facet(bottom_center, bottom_vertices[1][j], bottom_vertices[1][next_j]))

    # Outer rings for bottom
    for i in range(1, M):
        for j in range(N):
            next_j = (j + 1) % N
            v_curr_inner = bottom_vertices[i][j]
            v_next_inner = bottom_vertices[i][next_j]
            v_curr_outer = bottom_vertices[i+1][j]
            v_next_outer = bottom_vertices[i+1][next_j]
            
            # Normals down: inner -> outer -> next_outer (reverse of top)
            facets.append(Facet(v_curr_inner, v_curr_outer, v_next_outer))
            facets.append(Facet(v_curr_inner, v_next_outer, v_next_inner))

    # 3. Generate SIDE wall (connecting top outer edge to bottom outer edge)
    # i = M is the outermost edge
    for j in range(N):
        next_j = (j + 1) % N
        t_curr = top_vertices[M][j]
        t_next = top_vertices[M][next_j]
        b_curr = bottom_vertices[M][j]
        b_next = bottom_vertices[M][next_j]
        
        # Side wall quad split into 2 triangles
        # Normal pointing OUTWARD
        # Triangle 1: b_curr -> t_curr -> t_next
        facets.append(Facet(b_curr, t_curr, t_next))
        # Triangle 2: b_curr -> t_next -> b_next
        facets.append(Facet(b_curr, t_next, b_next))
        
    return facets

def main():
    print("Generating mathematical wave fidget coin STL...")
    facets = generate_wave_coin()
    
    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)
    output_path = os.path.join("models", "wave_coin.stl")
    
    write_ascii_stl(facets, output_path, name="wave_coin")
    print(f"Successfully generated: {output_path}")
    print(f"Total facets (triangles): {len(facets)}")

if __name__ == "__main__":
    main()
