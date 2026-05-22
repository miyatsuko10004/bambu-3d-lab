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

def write_ascii_stl(facets, filepath, name="fidget_button"):
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

def generate_cylinder(r_out, r_in, h_min, h_max, segments=64):
    facets = []
    # If r_in is 0, it's a solid cylinder
    is_solid = (r_in <= 0)
    
    # Vertices
    v_bottom_outer = []
    v_top_outer = []
    v_bottom_inner = []
    v_top_inner = []
    
    for i in range(segments):
        theta = (i / segments) * 2 * math.pi
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        v_bottom_outer.append((r_out * cos_t, r_out * sin_t, h_min))
        v_top_outer.append((r_out * cos_t, r_out * sin_t, h_max))
        
        if not is_solid:
            v_bottom_inner.append((r_in * cos_t, r_in * sin_t, h_min))
            v_top_inner.append((r_in * cos_t, r_in * sin_t, h_max))

    for i in range(segments):
        next_i = (i + 1) % segments
        
        # Outer wall
        facets.append(Facet(v_bottom_outer[i], v_top_outer[next_i], v_top_outer[i]))
        facets.append(Facet(v_bottom_outer[i], v_bottom_outer[next_i], v_top_outer[next_i]))
        
        if is_solid:
            # Bottom cap (solid)
            facets.append(Facet((0, 0, h_min), v_bottom_outer[i], v_bottom_outer[next_i]))
            # Top cap (solid)
            facets.append(Facet((0, 0, h_max), v_top_outer[next_i], v_top_outer[i]))
        else:
            # Inner wall (normal pointing inward)
            facets.append(Facet(v_bottom_inner[i], v_top_inner[i], v_top_inner[next_i]))
            facets.append(Facet(v_bottom_inner[i], v_top_inner[next_i], v_bottom_inner[next_i]))
            
            # Bottom ring cap
            facets.append(Facet(v_bottom_outer[i], v_bottom_inner[next_i], v_bottom_inner[i]))
            facets.append(Facet(v_bottom_outer[i], v_bottom_outer[next_i], v_bottom_inner[next_i]))
            
            # Top ring cap
            facets.append(Facet(v_top_outer[i], v_top_inner[i], v_top_inner[next_i]))
            facets.append(Facet(v_top_outer[i], v_top_inner[next_i], v_top_outer[next_i]))
            
    return facets

def generate_spiral_arm(r_start, r_end, h_max, width, start_angle, num_arms=3, segments=40):
    facets = []
    theta_max = 1.5 * math.pi  # 270 degrees wrap
    A = (r_end - r_start) / theta_max
    
    for arm in range(num_arms):
        angle_offset = start_angle + arm * (2.0 * math.pi / num_arms)
        
        # We will generate left and right vertices along the spiral path
        v_bl = []  # Bottom Left
        v_br = []  # Bottom Right
        v_tl = []  # Top Left
        v_tr = []  # Top Right
        
        for i in range(segments + 1):
            theta = (i / segments) * theta_max
            r = r_start + A * theta
            phi = theta + angle_offset
            
            cos_p = math.cos(phi)
            sin_p = math.sin(phi)
            
            # Centerline position
            cx = r * cos_p
            cy = r * sin_p
            
            # Tangent vector dx/dtheta, dy/dtheta
            # x = (r_start + A*theta)*cos(theta+offset)
            # dx = A*cos(phi) - r*sin(phi)
            # dy = A*sin(phi) + r*cos(phi)
            tx = A * cos_p - r * sin_p
            ty = A * sin_p + r * cos_p
            
            # Normalize tangent
            t_len = math.sqrt(tx**2 + ty**2)
            tx /= t_len
            ty /= t_len
            
            # Normal vector (perpendicular to tangent in 2D)
            nx = -ty
            ny = tx
            
            half_w = width / 2.0
            
            # Left and right boundary points
            lx = cx + half_w * nx
            ly = cy + half_w * ny
            
            rx = cx - half_w * nx
            ry = cy - half_w * ny
            
            v_bl.append((lx, ly, 0.0))
            v_br.append((rx, ry, 0.0))
            v_tl.append((lx, ly, h_max))
            v_tr.append((rx, ry, h_max))
            
        # Create facets along the arm segments
        for i in range(segments):
            # Top face (Normal UP)
            facets.append(Facet(v_tl[i], v_tr[next_i := i+1], v_tr[i]))
            facets.append(Facet(v_tl[i], v_tl[next_i], v_tr[next_i]))
            
            # Bottom face (Normal DOWN)
            facets.append(Facet(v_bl[i], v_br[i], v_br[next_i]))
            facets.append(Facet(v_bl[i], v_br[next_i], v_bl[next_i]))
            
            # Left side wall (Normal OUTWARD Left)
            facets.append(Facet(v_bl[i], v_tl[next_i], v_tl[i]))
            facets.append(Facet(v_bl[i], v_bl[next_i], v_tl[next_i]))
            
            # Right side wall (Normal OUTWARD Right)
            facets.append(Facet(v_br[i], v_tr[i], v_tr[next_i]))
            facets.append(Facet(v_br[i], v_tr[next_i], v_br[next_i]))
            
        # End caps (to close the volume, though they are inside the rings)
        # Start cap (at button)
        facets.append(Facet(v_bl[0], v_tl[0], v_tr[0]))
        facets.append(Facet(v_bl[0], v_tr[0], v_br[0]))
        
        # End cap (at housing)
        facets.append(Facet(v_bl[-1], v_tr[-1], v_tl[-1]))
        facets.append(Facet(v_bl[-1], v_br[-1], v_tr[-1]))
        
    return facets

def main():
    print("Generating print-in-place Fidget Push Button STL...")
    
    # Parameters
    R_btn = 8.0
    R_housing_in = 22.0
    R_housing_out = 25.0
    H_housing = 8.0
    H_btn = 11.0  # Taller than housing to push easily
    H_spring = 1.6  # 1.6mm thickness (strong yet elastic)
    W_spring = 1.2  # 1.2mm width
    
    all_facets = []
    
    # 1. Central Button Cylinder
    btn_facets = generate_cylinder(R_btn, r_in=0, h_min=0, h_max=H_btn, segments=64)
    all_facets.extend(btn_facets)
    print(f"Button cylinder generated: r={R_btn}, h={H_btn}")
    
    # 2. Outer Housing Ring
    housing_facets = generate_cylinder(R_housing_out, R_housing_in, h_min=0, h_max=H_housing, segments=64)
    all_facets.extend(housing_facets)
    print(f"Outer housing ring generated: inner_r={R_housing_in}, outer_r={R_housing_out}, h={H_housing}")
    
    # 3. Spiral springs connecting button to housing
    spring_facets = generate_spiral_arm(R_btn - 0.5, R_housing_in + 0.5, H_spring, W_spring, start_angle=0, num_arms=3, segments=60)
    all_facets.extend(spring_facets)
    print(f"Spiral spring arms generated: thickness={H_spring}, width={W_spring}")
    
    # Output
    os.makedirs("models", exist_ok=True)
    output_path = os.path.join("models", "fidget_button.stl")
    write_ascii_stl(all_facets, output_path, name="fidget_button")
    print(f"Successfully generated: {output_path}")
    print(f"Total facets: {len(all_facets)}")

if __name__ == "__main__":
    main()
