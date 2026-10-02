"""
tracker.py — Sentinel
=====================
Two classes work together to implement directional tripwire detection:

CentroidTracker
    Assigns stable integer IDs to detected face bounding boxes across frames.
    Uses Euclidean distance between centroids in consecutive frames to match
    objects, and de-registers objects that haven't been seen for max_disappeared
    consecutive frames.

TripwireMonitor
    Maintains a per-object-ID state machine (ABOVE / BELOW the tripwire).
    When a centroid transitions from one side to the other it emits a crossing
    event ('ENTER' when going downward, 'EXIT' when going upward).
    A 5-second debounce window prevents the same object from triggering
    duplicate events when it hovers near the line.
"""

import logging
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.spatial import distance as dist

logger = logging.getLogger(__name__)

# Type aliases
Rect = Tuple[int, int, int, int]   # (startX, startY, endX, endY)
Centroid = Tuple[int, int]          # (cx, cy)


class CentroidTracker:
    """
    Lightweight centroid-based object tracker.

    Attributes:
        next_object_id:  Counter for assigning new object IDs.
        objects:         OrderedDict mapping objectID → centroid (cx, cy).
        disappeared:     OrderedDict mapping objectID → consecutive-missing-frame count.
        max_disappeared: How many frames an object can be absent before de-registration.
    """

    def __init__(self, max_disappeared: int = 40) -> None:
        self.next_object_id: int = 0
        self.objects: OrderedDict[int, Centroid] = OrderedDict()
        self.disappeared: OrderedDict[int, int] = OrderedDict()
        self.max_disappeared = max_disappeared

    # ------------------------------------------------------------------
    def _register(self, centroid: Centroid) -> None:
        """Register a new object with the next available ID."""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def _deregister(self, object_id: int) -> None:
        """Remove a lost object."""
        del self.objects[object_id]
        del self.disappeared[object_id]

    # ------------------------------------------------------------------
    def update(self, rects: List[Rect]) -> Dict[int, Centroid]:
        """
        Update tracker with the latest list of bounding boxes.

        Args:
            rects: List of (startX, startY, endX, endY) bounding boxes.

        Returns:
            Dictionary of {objectID: (cx, cy)} for all currently tracked objects.
        """
        # ---- No detections this frame ----
        if not rects:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self._deregister(oid)
            return dict(self.objects)

        # Compute input centroids
        input_centroids = np.array(
            [((x1 + x2) // 2, (y1 + y2) // 2) for (x1, y1, x2, y2) in rects],
            dtype="int",
        )

        # ---- First frame — register all ----
        if not self.objects:
            for c in input_centroids:
                self._register(tuple(c))
            return dict(self.objects)

        # ---- Match existing objects to new centroids ----
        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())

        # Pairwise Euclidean distances: rows=existing, cols=input
        D = dist.cdist(np.array(object_centroids), input_centroids)

        # Sort by minimum distance: rows first, then cols
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows: set = set()
        used_cols: set = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            object_id = object_ids[row]
            self.objects[object_id] = tuple(input_centroids[col])
            self.disappeared[object_id] = 0
            used_rows.add(row)
            used_cols.add(col)

        # Handle unmatched existing objects (disappeared)
        for row in set(range(len(object_ids))) - used_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self._deregister(object_id)

        # Register brand-new centroids
        for col in set(range(len(input_centroids))) - used_cols:
            self._register(tuple(input_centroids[col]))

        return dict(self.objects)


# ---------------------------------------------------------------------------

class _ObjectState:
    """Internal state for a single tracked face in the TripwireMonitor."""
    __slots__ = ("side", "last_event_time")

    ABOVE = "ABOVE"
    BELOW = "BELOW"
    UNKNOWN = "UNKNOWN"

    def __init__(self) -> None:
        self.side: str = _ObjectState.UNKNOWN
        self.last_event_time: float = 0.0


class TripwireMonitor:
    """
    Monitors centroid positions relative to a configurable horizontal tripwire.

    Crossing downward  (ABOVE → BELOW)  → "ENTER"
    Crossing upward    (BELOW → ABOVE)  → "EXIT"

    A 5-second per-object debounce prevents duplicate events.

    Args:
        line_y_ratio:   Tripwire position as a fraction of frame height (0–1).
        debounce_secs:  Minimum seconds between consecutive events per object.
    """

    def __init__(self, line_y_ratio: float = 0.5, debounce_secs: float = 5.0) -> None:
        self.line_y_ratio = line_y_ratio
        self.debounce_secs = debounce_secs
        self._states: Dict[int, _ObjectState] = {}

    # ------------------------------------------------------------------
    def set_line_ratio(self, ratio: float) -> None:
        """Update tripwire position at runtime (0.0–1.0)."""
        self.line_y_ratio = max(0.05, min(0.95, ratio))

    def get_line_y(self, frame_height: int) -> int:
        """Return the absolute Y pixel coordinate of the tripwire."""
        return int(self.line_y_ratio * frame_height)

    # ------------------------------------------------------------------
    def check_crossing(
        self, object_id: int, centroid_y: int, frame_height: int
    ) -> Optional[str]:
        """
        Check whether object_id has crossed the tripwire this frame.

        Args:
            object_id:    Tracker-assigned ID.
            centroid_y:   Current centroid Y-coordinate in pixels.
            frame_height: Total frame height in pixels.

        Returns:
            'ENTER', 'EXIT', or None if no qualifying crossing occurred.
        """
        line_y = self.get_line_y(frame_height)

        # Initialise state for new objects
        if object_id not in self._states:
            self._states[object_id] = _ObjectState()

        state = self._states[object_id]
        current_side = (
            _ObjectState.ABOVE if centroid_y < line_y else _ObjectState.BELOW
        )

        event: Optional[str] = None

        if state.side == _ObjectState.UNKNOWN:
            # First observation — just record the side, no event
            state.side = current_side

        elif state.side != current_side:
            # Side changed — potential crossing
            now = time.monotonic()
            if now - state.last_event_time >= self.debounce_secs:
                if current_side == _ObjectState.BELOW:
                    event = "ENTER"
                else:
                    event = "EXIT"
                state.last_event_time = now
                logger.debug(
                    "Object %d crossed tripwire → %s (cy=%d, line_y=%d)",
                    object_id, event, centroid_y, line_y,
                )
            state.side = current_side

        return event

    # ------------------------------------------------------------------
    def remove_object(self, object_id: int) -> None:
        """Clean up state for a de-registered object."""
        self._states.pop(object_id, None)

    def prune_stale(self, active_ids: set) -> None:
        """Remove state entries for objects no longer tracked."""
        stale = set(self._states.keys()) - active_ids
        for oid in stale:
            self._states.pop(oid, None)
