"""
net0 mesh simulator -- a small, readable model of the ESP32 flood mesh.

This file has NO hardware dependency: it is pure Python (standard library only).
It imitates what the firmware does (see net0-firmware/src/node/main.cpp):

  * nodes sit in a line, each one only talks to its immediate neighbours
  * a report is FLOODED: every node forwards a copy it has not seen before
  * duplicates are suppressed with a ring buffer of the last 64
    (msg_id, attempt) keys
  * a TTL counts the hops a packet may still travel; ttl <= 1 means "do not
    forward any more"
  * the gateway receives the report and floods an ACK back
  * the origin node re-sends with the same msg_id and attempt+1 after
    3 s, 6 s and 12 s until the ACK arrives
  * every node can send one packet per 20 ms (a 20 ms transmit slot), so
    packets wait in a queue when traffic is heavy
  * the queue can be served priority-first (1 = CRITICAL first) or plain
    first-come-first-served, so the two can be compared

Time is simulated in milliseconds with a discrete-event loop (a heap of
events). Nothing is real time, nothing touches the radio.
"""

from __future__ import annotations

import heapq
import random
from collections import deque
from dataclasses import dataclass, field

# The gateway is node 0 on the mesh, exactly like GATEWAY_ID in packet.h.
GATEWAY = 0

# Packet kinds we model. (The firmware also has heartbeats and messages; they
# only add noise here, so they are left out.)
REPORT = "report"
ACK = "ack"

# Priority numbers match the rest of the project: 1 = CRITICAL ... 4 = LOW.
PRIORITY_CRITICAL = 1
PRIORITY_LOW = 4


@dataclass(frozen=True)
class SimConfig:
    """Every knob of the model lives here, so an experiment is one line."""

    nodes: int = 6                 # number of access/relay nodes in the line
    ttl: int = 6                   # hops a packet may travel (DEFAULT_TTL)
    delay_min_ms: float = 10.0     # random per-link propagation delay
    delay_max_ms: float = 60.0
    loss: float = 0.10             # chance a single transmission is lost
    tx_slot_ms: float = 20.0       # one packet per node per 20 ms
    retry_ms: tuple[float, ...] = (3000.0, 6000.0, 12000.0)  # 3 s, 6 s, 12 s
    retries_enabled: bool = True   # experiment 3 turns this off
    dedup_size: int = 64           # ring buffer size (mesh.h)
    priority_queue: bool = True    # False = first come, first served


@dataclass
class Packet:
    """One over-the-air copy of a report or an ACK."""

    msg_id: int          # stays the same on every retry of the same report
    attempt: int         # 0 on the first send, +1 per retry
    kind: str            # REPORT or ACK
    origin: int          # node that created it
    priority: int        # 1 = CRITICAL ... 4 = LOW
    ttl: int             # hops left
    created_ms: float    # when the report was first created
    ref_id: int = 0      # ACK: msg_id it acknowledges
    path: list[int] = field(default_factory=list)  # node IDs visited

    @property
    def key(self) -> tuple[int, int]:
        """De-duplication key: same report retried = same id, new attempt."""
        return (self.msg_id, self.attempt)


@dataclass
class Delivery:
    """What the gateway recorded when a report first arrived."""

    msg_id: int
    priority: int
    origin: int
    arrived_ms: float
    hops: int
    attempt: int

    @property
    def latency_ms(self) -> float:
        return self.arrived_ms - self.created_ms if hasattr(self, "created_ms") else 0.0


class Node:
    """Queue + de-duplication state for one radio."""

    def __init__(self, node_id: int, config: SimConfig) -> None:
        self.id = node_id
        self.config = config
        # Waiting packets as (arrival_order, packet) so ties keep FIFO order.
        self.queue: list[tuple[int, Packet]] = []
        # Ring buffer of the last N keys we transmitted or accepted.
        self.seen: deque[tuple[int, int]] = deque(maxlen=config.dedup_size)
        self.busy_until: float = 0.0   # when the radio is free again
        self.tx_pending: bool = False  # a "tx" event is already scheduled
        self.sent: int = 0             # packets this node transmitted

    def __repr__(self) -> str:  # helps when reading test output
        return f"<Node {self.id} queue={len(self.queue)} sent={self.sent}>"


# __APPEND__
