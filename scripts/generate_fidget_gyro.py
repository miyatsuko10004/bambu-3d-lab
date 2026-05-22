#!/usr/bin/env python3
import math
import os

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

def write_ascii_stl(facets, filepath, name="fidget_gyro"):
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

def generate_gyro_ring(r_out, r_in, height, clearance, pin_rad, pin_len, has_inner_pins, has_outer_holes, rot_angle):
    # Grid resolution for the ring
    N = 96  # Number of angular segments
    H_half = height / 2.0
    
    facets = []
    
    # Pre-calculate sine/cosine table for rot_angle
    cos_rot = math.cos(rot_angle)
    sin_rot = math.sin(rot_angle)
    
    def rotate_pt(x, y, z):
        # Rotate point around Z axis by rot_angle
        rx = x * cos_rot - y * sin_rot
        ry = x * sin_rot + y * cos_rot
        return (rx, ry, z)

    # Pin and hole geometry parameters
    # Hole is slightly larger than the pin
    hole_rad = pin_rad + clearance
    hole_len = pin_len + clearance
    
    # Outer pins / Inner holes are placed on X or Y axis relative to the ring
    # In our coordinate system:
    # Inner holes (if present) are at angle = 0 and angle = pi (X-axis)
    # Outer pins (if present) are at angle = pi/2 and angle = 3*pi/2 (Y-axis)
    
    def get_inner_radius(theta, z):
        r = r_in
        if not has_outer_holes: # Inner-most ring has no inner holes (receives pins from core)
            return r
            
        # Check proximity to X-axis positive (theta = 0)
        # We wrap theta to [-pi, pi]
        theta_wrapped = (theta + math.pi) % (2 * math.pi) - math.pi
        
        # Distance from the hole center axis (X-axis)
        # Y coord is approx R * theta, Z coord is z
        d_pos = math.sqrt((r_in * theta_wrapped)**2 + z**2)
        if d_pos < hole_rad:
            # We are inside the hole cone
            depth = hole_len * (1.0 - d_pos / hole_rad)
            r += depth
            
        # Check proximity to X-axis negative (theta = pi)
        theta_wrapped_neg = (theta - math.pi + math.pi) % (2 * math.pi) - math.pi
        d_neg = math.sqrt((r_in * theta_wrapped_neg)**2 + z**2)
        if d_neg < hole_rad:
            depth = hole_len * (1.0 - d_neg / hole_rad)
            r += depth
            
        return r

    def get_outer_radius(theta, z):
        r = r_out
        if not has_inner_pins: # Outer-most ring has no outer pins
            return r
            
        # Outer pins are on the Y-axis (theta = pi/2 and theta = 3*pi/2)
        # Check proximity to Y-axis positive (theta = pi/2)
        theta_wrapped_pos = (theta - math.pi/2 + math.pi) % (2 * math.pi) - math.pi
        d_pos = math.sqrt((r_out * theta_wrapped_pos)**2 + z**2)
        if d_pos < pin_rad:
            # Inside the pin cone
            height_pin = pin_len * (1.0 - d_pos / pin_rad)
            r += height_pin
            
        # Check proximity to Y-axis negative (theta = 3*pi/2 or -pi/2)
        theta_wrapped_neg = (theta + math.pi/2 + math.pi) % (2 * math.pi) - math.pi
        d_neg = math.sqrt((r_out * theta_wrapped_neg)**2 + z**2)
        if d_neg < pin_rad:
            height_pin = pin_len * (1.0 - d_neg / pin_rad)
            r += height_pin
            
        return r

    # Generate vertices
    # 4 rows of vertices: Inner Bottom, Inner Top, Outer Bottom, Outer Top
    vertices_ib = []
    vertices_it = []
    vertices_ob = []
    vertices_ot = []
    
    for j in range(N):
        theta = (j / N) * 2 * math.pi
        
        ri = get_inner_radius(theta, -H_half)
        vertices_ib.append(rotate_pt(ri * math.cos(theta), ri * math.sin(theta), -H_half))
        
        ri = get_inner_radius(theta, H_half)
        vertices_it.append(rotate_pt(ri * math.cos(theta), ri * math.sin(theta), H_half))
        
        ro = get_outer_radius(theta, -H_half)
        vertices_ob.append(rotate_pt(ro * math.cos(theta), ro * math.sin(theta), -H_half))
        
        ro = get_outer_radius(theta, H_half)
        vertices_ot.append(rotate_pt(ro * math.cos(theta), ro * math.sin(theta), H_half))

    # Connect vertices to form facets
    for j in range(N):
        next_j = (j + 1) % N
        
        # 1. Inner Wall (Normals point inward, so winding must be counter-clockwise from inside)
        # Vertices: ib[j], it[j], it[next_j], ib[next_j]
        facets.append(Facet(vertices_ib[j], vertices_it[next_j], vertices_it[j]))
        facets.append(Facet(vertices_ib[j], vertices_ib[next_j], vertices_it[next_j]))
        
        # 2. Outer Wall (Normals point outward)
        # Vertices: ob[j], ot[j], ot[next_j], ob[next_j]
        facets.append(Facet(vertices_ob[j], vertices_ot[j], vertices_ot[next_j]))
        facets.append(Facet(vertices_ob[j], vertices_ot[next_j], vertices_ob[next_j]))
        
        # 3. Top Ring Surface (Normals point UP)
        # Vertices: it[j], ot[j], ot[next_j], it[next_j]
        facets.append(Facet(vertices_it[j], vertices_ot[next_j], vertices_ot[j]))
        facets.append(Facet(vertices_it[j], vertices_it[next_j], vertices_ot[next_j]))
        
        # 4. Bottom Ring Surface (Normals point DOWN)
        # Vertices: ib[j], ob[j], ob[next_j], ib[next_j]
        facets.append(Facet(vertices_ib[j], vertices_ob[j], vertices_ob[next_j]))
        facets.append(Facet(vertices_ib[j], vertices_ob[next_j], vertices_ib[next_j]))
        
    return facets

def generate_core(r_out, height, pin_rad, pin_len, rot_angle):
    # Center core is a solid cylinder with pins sticking out on the Y-axis
    N = 96
    H_half = height / 2.0
    facets = []
    
    cos_rot = math.cos(rot_angle)
    sin_rot = math.sin(rot_angle)
    
    def rotate_pt(x, y, z):
        rx = x * cos_rot - y * sin_rot
        ry = x * sin_rot + y * cos_rot
        return (rx, ry, z)

    def get_outer_radius(theta, z):
        r = r_out
        # Pins are on the Y-axis (theta = pi/2 and theta = 3*pi/2)
        theta_wrapped_pos = (theta - math.pi/2 + math.pi) % (2 * math.pi) - math.pi
        d_pos = math.sqrt((r_out * theta_wrapped_pos)**2 + z**2)
        if d_pos < pin_rad:
            height_pin = pin_len * (1.0 - d_pos / pin_rad)
            r += height_pin
            
        theta_wrapped_neg = (theta + math.pi/2 + math.pi) % (2 * math.pi) - math.pi
        d_neg = math.sqrt((r_out * theta_wrapped_neg)**2 + z**2)
        if d_neg < pin_rad:
            height_pin = pin_len * (1.0 - d_neg / pin_rad)
            r += height_pin
            
        return r

    # Vertices
    vertices_b = []
    vertices_t = []
    for j in range(N):
        theta = (j / N) * 2 * math.pi
        ro = get_outer_radius(theta, -H_half)
        vertices_b.append(rotate_pt(ro * math.cos(theta), ro * math.sin(theta), -H_half))
        
        ro = get_outer_radius(theta, H_half)
        vertices_t.append(rotate_pt(ro * math.cos(theta), ro * math.sin(theta), H_half))

    # Center points for top/bottom caps
    center_b = (0.0, 0.0, -H_half)
    center_t = (0.0, 0.0, H_half)

    for j in range(N):
        next_j = (j + 1) % N
        
        # 1. Outer Wall (Normals point outward)
        facets.append(Facet(vertices_b[j], vertices_t[j], vertices_t[next_j]))
        facets.append(Facet(vertices_b[j], vertices_t[next_j], vertices_b[next_j]))
        
        # 2. Top Cap (Normals point UP)
        facets.append(Facet(center_t, vertices_t[next_j], vertices_t[j]))
        
        # 3. Bottom Cap (Normals point DOWN)
        facets.append(Facet(center_b, vertices_b[j], vertices_b[next_j]))
        
    return facets

def main():
    print("Generating print-in-place Fidget Gyroscope STL...")
    
    # Parameters matches the SCAD design
    clearance = 0.35
    num_rings = 4
    ring_width = 4.0
    ring_height = 8.0
    pin_radius = 1.5
    pin_len = 1.5
    
    all_facets = []
    
    for i in range(num_rings):
        # Calculate dimensions
        r_out = (ring_width + pin_radius * 1.5) if i == 0 else (i * (ring_width + clearance + pin_radius) + ring_width + pin_radius * 1.5)
        r_in = r_out - ring_width
        
        has_outer_holes = (i > 0)
        has_inner_pins = (i < num_rings - 1)
        rot_angle = i * (math.pi / 2)  # 90 degrees offset for each ring
        
        if i == 0:
            # Core
            facets = generate_core(r_out, ring_height, pin_radius, pin_len, rot_angle)
        else:
            # Ring
            facets = generate_gyro_ring(r_out, r_in, ring_height, clearance, pin_radius, pin_len, has_inner_pins, has_outer_holes, rot_angle)
            
        all_facets.extend(facets)
        print(f"Ring {i} generated: outer_r={r_out:.2f}, inner_r={r_in:.2f}")

    # Output
    os.makedirs("models", exist_ok=True)
    output_path = os.path.join("models", "fidget_gyro.stl")
    write_ascii_stl(all_facets, output_path, name="fidget_gyro")
    print(f"Successfully generated: {output_path}")
    print(f"Total facets: {len(all_facets)}")

if __name__ == "__main__":
    main()
