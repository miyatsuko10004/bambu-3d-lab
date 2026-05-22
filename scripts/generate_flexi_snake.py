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
        u = (self.v2[0] - self.v1[0], self.v2[1] - self.v1[1], self.v2[2] - self.v1[2])
        v = (self.v3[0] - self.v1[0], self.v3[1] - self.v1[1], self.v3[2] - self.v1[2])
        nx = u[1] * v[2] - u[2] * v[1]
        ny = u[2] * v[0] - u[0] * v[2]
        nz = u[0] * v[1] - u[1] * v[0]
        l = math.sqrt(nx**2 + ny**2 + nz**2)
        if l == 0:
            return (0.0, 0.0, 0.0)
        return (nx / l, ny / l, nz / l)

def write_ascii_stl(facets, filepath, name="flexi_snake"):
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

def generate_box(x_min, x_max, y_min, y_max, z_min, z_max):
    facets = []
    # 8 corners
    v000 = (x_min, y_min, z_min)
    v100 = (x_max, y_min, z_min)
    v010 = (x_min, y_max, z_min)
    v110 = (x_max, y_max, z_min)
    v001 = (x_min, y_min, z_max)
    v101 = (x_max, y_min, z_max)
    v011 = (x_min, y_max, z_max)
    v111 = (x_max, y_max, z_max)
    
    # Bottom face (Z-)
    facets.append(Facet(v000, v010, v110))
    facets.append(Facet(v000, v110, v100))
    # Top face (Z+)
    facets.append(Facet(v001, v101, v111))
    facets.append(Facet(v001, v111, v011))
    # Front face (Y-)
    facets.append(Facet(v000, v100, v101))
    facets.append(Facet(v000, v101, v001))
    # Back face (Y+)
    facets.append(Facet(v010, v011, v111))
    facets.append(Facet(v010, v111, v110))
    # Left face (X-)
    facets.append(Facet(v000, v001, v011))
    facets.append(Facet(v000, v011, v010))
    # Right face (X+)
    facets.append(Facet(v100, v110, v111))
    facets.append(Facet(v100, v111, v101))
    
    return facets

def generate_cylinder(cx, cy, r_out, r_in, z_min, z_max, segments=32):
    facets = []
    is_solid = (r_in <= 0)
    
    v_bo = []
    v_to = []
    v_bi = []
    v_ti = []
    
    for i in range(segments):
        theta = (i / segments) * 2 * math.pi
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        v_bo.append((cx + r_out * cos_t, cy + r_out * sin_t, z_min))
        v_to.append((cx + r_out * cos_t, cy + r_out * sin_t, z_max))
        if not is_solid:
            v_bi.append((cx + r_in * cos_t, cy + r_in * sin_t, z_min))
            v_ti.append((cx + r_in * cos_t, cy + r_in * sin_t, z_max))
            
    for i in range(segments):
        next_i = (i + 1) % segments
        
        # Outer wall
        facets.append(Facet(v_bo[i], v_to[next_i], v_to[i]))
        facets.append(Facet(v_bo[i], v_bo[next_i], v_to[next_i]))
        
        if is_solid:
            # Bottom cap
            facets.append(Facet((cx, cy, z_min), v_bo[i], v_bo[next_i]))
            # Top cap
            facets.append(Facet((cx, cy, z_max), v_to[next_i], v_to[i]))
        else:
            # Inner wall
            facets.append(Facet(v_bi[i], v_ti[i], v_ti[next_i]))
            facets.append(Facet(v_bi[i], v_ti[next_i], v_bi[next_i]))
            # Bottom ring
            facets.append(Facet(v_bo[i], v_bi[next_i], v_bi[i]))
            facets.append(Facet(v_bo[i], v_bo[next_i], v_bi[next_i]))
            # Top ring
            facets.append(Facet(v_to[i], v_ti[i], v_ti[next_i]))
            facets.append(Facet(v_to[i], v_ti[next_i], v_to[next_i]))
            
    return facets

def generate_spine_fin(cx, cy, cz_base, length, width, height):
    # Generates a cool triangular pyramid fin on the top of the segment
    facets = []
    
    # Base vertices on body top
    v_fl = (cx - length/2, cy - width/2, cz_base)
    v_fr = (cx - length/2, cy + width/2, cz_base)
    v_bl = (cx + length/2, cy - width/2, cz_base)
    v_br = (cx + length/2, cy + width/2, cz_base)
    
    # Peak vertex
    v_peak = (cx, cy, cz_base + height)
    
    # Front-left face
    facets.append(Facet(v_fl, v_fr, v_peak))
    # Back-right face
    facets.append(Facet(v_bl, v_peak, v_br))
    # Left face
    facets.append(Facet(v_fl, v_peak, v_bl))
    # Right face
    facets.append(Facet(v_fr, v_br, v_peak))
    
    # Base face (Z-) - pointing down inside the body
    facets.append(Facet(v_fl, v_bl, v_br))
    facets.append(Facet(v_fl, v_br, v_fr))
    
    return facets

def generate_snake_head(cx, cy, z_min, z_max):
    # Rounded head for the snake first segment
    facets = []
    # Base box for head
    facets.extend(generate_box(cx - 5.0, cx + 3.0, cy - 6.0, cy + 6.0, z_min, z_max))
    
    # Add two eyes (small cylinders)
    facets.extend(generate_cylinder(cx - 2.0, cy - 4.5, 1.2, 0, z_max, z_max + 1.2, segments=16))
    facets.extend(generate_cylinder(cx - 2.0, cy + 4.5, 1.2, 0, z_max, z_max + 1.2, segments=16))
    
    # Rounded nose
    facets.extend(generate_cylinder(cx - 5.0, cy, 3.0, 0, z_min, z_max, segments=16))
    
    # Cool head fin
    facets.extend(generate_spine_fin(cx, cy, z_max, length=6.0, width=4.0, height=4.0))
    
    return facets

def main():
    print("Generating Print-in-Place Flexi Snake STL...")
    
    num_segments = 10  # Length of the snake
    pitch = 12.0      # Distance between segment centers
    
    # Joint specs
    z_height = 6.8
    clearance = 0.35
    
    r_pin = 1.5
    r_loop_out = 3.5
    r_loop_in = r_pin + clearance # 1.85
    
    all_facets = []
    
    for k in range(num_segments):
        cx = k * pitch
        
        # Determine if head, tail, or body
        is_head = (k == 0)
        is_tail = (k == num_segments - 1)
        
        # 1. Main Body segment
        if is_head:
            # Special Head segment
            all_facets.extend(generate_snake_head(cx, 0.0, 0.0, z_height))
        else:
            # Normal segment body
            # Tail gets smaller towards the end
            scale = 1.0 - (k / num_segments) * 0.5  # Shrinks down to 50% at tail
            seg_w = 12.0 * scale
            seg_l = 6.0 * scale
            
            # Box body
            all_facets.extend(generate_box(cx - seg_l/2, cx + seg_l/2, -seg_w/2, seg_w/2, 0.0, z_height * scale))
            
            # Back fin
            all_facets.extend(generate_spine_fin(cx, 0.0, z_height * scale, length=seg_l * 0.8, width=seg_w * 0.4, height=4.0 * scale))
            
        # 2. Rear Joint (Pins & Plates) - present on all except tail
        if not is_tail:
            # Scaling factors
            scale = 1.0 - (k / num_segments) * 0.5
            
            # Rear joint center
            rx = cx + 6.0
            
            # Rear plates
            # Bottom Plate (z: 0 to 2.0)
            all_facets.extend(generate_box(cx + 3.0 * scale, rx, -r_loop_out * scale, r_loop_out * scale, 0.0, 2.0))
            all_facets.extend(generate_cylinder(rx, 0.0, r_loop_out * scale, 0, 0.0, 2.0))
            
            # Top Plate (z: 4.8 to 6.8)
            all_facets.extend(generate_box(cx + 3.0 * scale, rx, -r_loop_out * scale, r_loop_out * scale, 4.8, 6.8))
            all_facets.extend(generate_cylinder(rx, 0.0, r_loop_out * scale, 0, 4.8, 6.8))
            
            # Vertical Pin (z: 0 to 6.8)
            # The pin radius is constant 1.5 to maintain fit, or scaled down slightly
            # We keep pin_radius standard to make joints consistent, but scale down slightly for the tail
            curr_pin_r = r_pin * scale
            all_facets.extend(generate_cylinder(rx, 0.0, curr_pin_r, 0, 0.0, 6.8))
            
        # 3. Front Joint (Middle Plate with Hole) - present on all except head
        if not is_head:
            # Front joint center matches the previous segment's rear pin
            # Previous rear pin was at (k-1)*pitch + 6.0 = k*pitch - 6.0
            fx = cx - 6.0
            
            # Scale of previous segment (k-1)
            scale_prev = 1.0 - ((k - 1) / num_segments) * 0.5
            
            # Scale of current segment (k)
            scale_curr = 1.0 - (k / num_segments) * 0.5
            
            # Middle plate (z: 2.4 to 4.4, with clearance 0.4 from top/bottom plates)
            # Connecting arm from current body to the loop
            all_facets.extend(generate_box(fx, cx - 3.0 * scale_curr, -2.0 * scale_curr, 2.0 * scale_curr, 2.4, 4.4))
            
            # Loop with Hole
            curr_loop_out = r_loop_out * scale_prev
            curr_loop_in = (r_pin * scale_prev) + clearance
            all_facets.extend(generate_cylinder(fx, 0.0, curr_loop_out, curr_loop_in, 2.4, 4.4))
            
    # Output
    os.makedirs("models", exist_ok=True)
    output_path = os.path.join("models", "flexi_snake.stl")
    write_ascii_stl(all_facets, output_path, name="flexi_snake")
    print(f"Successfully generated: {output_path}")
    print(f"Total facets: {len(all_facets)}")

if __name__ == "__main__":
    main()
