// =========================================================================
// Bambu Lab A1 mini - Print-in-Place Fidget Gyroscope
// =========================================================================
// Designed for 3D Printing without supports.
// The rings are connected by conical pins that allow 3D rotation.
//
// Recommended Bambu Studio Settings:
// - Layer Height: 0.12mm (Fine) or 0.20mm (Standard)
// - Wall Loops: 3
// - Infill: 15% (Grid or Gyroid)
// - Support: None (Crucial! Do not enable supports)
// =========================================================================

/* [Parameters] */
// The gap between mating parts. A1 mini is precise; 0.35mm works perfectly.
clearance = 0.35; // [0.25:0.05:0.6]

// Number of rings (including the center core)
num_rings = 4; // [2:1:6]

// Width of each individual ring (mm)
ring_width = 4.0; // [3.0:0.5:8.0]

// Height/Thickness of the rings (mm)
ring_height = 8.0; // [5.0:0.5:15.0]

// Radius of the pivot pin (mm)
pin_radius = 1.5; // [1.0:0.1:3.0]

// Enable beautiful wave texture on ring outer edges
enable_texture = true;

/* [Hidden] */
// Rendering detail
$fn = $preview ? 48 : 96;

// Conical pin model (45-degree angle ensures support-free printing)
module pivot_pin() {
    // 45 degree overhang cone
    cylinder(h = pin_radius, r1 = pin_radius, r2 = 0, center = false);
}

// Conical hole for the pin (with clearance)
module pivot_hole() {
    // A slightly larger cone to accommodate the pin and clearance
    translate([0, 0, -0.05]) // minor offset to prevent Z-fighting in OpenSCAD
    cylinder(h = pin_radius + clearance + 0.1, 
             r1 = pin_radius + clearance, 
             r2 = 0, 
             center = false);
}

// Single ring module
module gyro_ring(r_out, r_in, has_inner_pins, has_outer_holes, rot_angle) {
    rotate([0, 0, rot_angle]) {
        difference() {
            // 1. Main Outer Ring Body
            cylinder(h = ring_height, r = r_out, center = true);
            
            // 2. Inner Hole cutout
            cylinder(h = ring_height + 2, r = r_in, center = true);
            
            // 3. Cut outer holes (placed on X axis: left and right)
            if (has_outer_holes) {
                // Right hole
                translate([r_out - 0.1, 0, 0])
                    rotate([0, -90, 0])
                        pivot_hole();
                
                // Left hole
                translate([-(r_out - 0.1), 0, 0])
                    rotate([0, 90, 0])
                        pivot_hole();
            }
            
            // 4. (Optional) Beautiful vertical grips on the outermost ring
            if (enable_texture && !has_outer_holes) {
                for (a = [0 : 15 : 359]) {
                    if (abs(a - 0) > 20 && abs(a - 180) > 20) { // Keep pins area flat
                        rotate([0, 0, a])
                            translate([r_out, 0, 0])
                                cylinder(h = ring_height + 1, r = 0.8, center = true, $fn=12);
                    }
                }
            }
        }
        
        // 5. Add inner pins (placed on Y axis: top and bottom - 90 degrees offset from holes)
        if (has_inner_pins) {
            // Top pin (pointing inward)
            translate([0, r_in + pin_radius - 0.1, 0])
                rotate([90, 0, 0])
                    pivot_pin();
            
            // Bottom pin (pointing inward)
            translate([0, -(r_in + pin_radius - 0.1), 0])
                rotate([-90, 0, 0])
                    pivot_pin();
        }
    }
}

// Assemble the gyroscope
union() {
    for (i = [0 : num_rings - 1]) {
        // Calculate dimensions
        // Each ring needs to fit outside the previous one, leaving space for the pins and clearance
        // Radius math:
        // Ring 0 (Center core): Outer radius = core_r
        // Ring 1: Inner radius = core_r + clearance + pin_radius
        //         Outer radius = Inner radius + ring_width
        
        // Let's calculate from inside out:
        // Outer radius of ring i:
        r_out = (i == 0) ? 
            (ring_width + pin_radius * 1.5) : 
            (i * (ring_width + clearance + pin_radius) + ring_width + pin_radius * 1.5);
            
        r_in = r_out - ring_width;
        
        // Ring configuration
        has_outer_holes = (i > 0);
        has_inner_pins = (i < num_rings - 1);
        
        // Alternate pin directions by 90 degrees for each ring
        rot = i * 90;
        
        if (i == 0) {
            // Center Core: solid cylinder with a cool decorative design or logo hole
            difference() {
                union() {
                    cylinder(h = ring_height, r = r_out, center = true);
                    // Inner pins for the center core (pointing outward)
                    // The core needs to have pins that go OUT into the next ring's holes
                    rotate([0, 0, rot]) {
                        translate([r_out - 0.1, 0, 0])
                            rotate([0, 90, 0])
                                pivot_pin();
                        translate([-(r_out - 0.1), 0, 0])
                            rotate([0, -90, 0])
                                pivot_pin();
                    }
                }
                // Decorative central hole
                cylinder(h = ring_height + 2, r = r_out / 2, center = true);
            }
        } else {
            // Regular Ring
            // Since Ring 0 has outer pins, Ring 1 needs inner holes at the same angle
            // Ring i has:
            // - Inner holes (to receive pins from Ring i-1) on one axis
            // - Outer pins (to insert into Ring i+1) on the perpendicular axis
            
            // To make this work:
            // Ring i's inner holes must match Ring i-1's outer pins (same angle)
            // Ring i's outer pins must be rotated 90 degrees relative to its inner holes
            
            // Let's implement Ring:
            // Inner holes are on the X axis of the ring.
            // Outer pins are on the Y axis of the ring.
            // The ring rotation alternates 90 degrees each iteration to align holes with previous pins.
            
            gyro_ring(r_out, r_in, has_inner_pins, has_outer_holes, rot);
        }
    }
}
