cat > README.md << 'EOF'
# Offgrid SOS India (ResQMesh)

A priority-aware emergency SOS network for areas where mobile networks fail
during disasters. A victim's phone connects to a nearby ESP32 node, the report
hops across nodes over ESP-NOW, and reaches a rescue-station dashboard where
critical cases are shown first.

## What this project adds
- Priority levels (1 = critical to 4 = low) for each report, in the backend,
  database and dashboard
- A flashing banner and beep when a critical report arrives
- Tests for the priority mapping and sorting

## Planned
- A Python simulation of the mesh (delivery ratio, latency, hop count, and
  priority queue on vs off)
- India-specific emergency types, languages (Hindi, Kannada) and responders

## Status
- Backend, database and dashboard: working with test data
- Firmware: inherited from net0, not flashed or tested on boards
- Any simulation results will be SIMULATED, not measured on hardware

