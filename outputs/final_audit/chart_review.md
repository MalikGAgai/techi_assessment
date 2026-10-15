# Manual chart review

Both final PNG figures were opened and visually inspected during the final audit.

- `outputs/synthetic_traffic/traffic_by_month.png`: six labelled panels use black
  lines and markers, month labels and session units. Individual y scales are
  disclosed in the title; they are not a shared-size comparison. Axes are not
  zero-based, which is visible on the labelled ticks. The November Crypto spike,
  common February jump and Guides decline are readable without color.
- `outputs/traffic_investigation/measurement_and_newsletter.png`: solid circles,
  dashed squares and dotted triangles distinguish series in black and white.
  The upper panel labels the adjustment as a central scenario. The lower panel
  uses September 2025 = 100, permitting an honest comparison of sessions and
  signup trends without implying equal units or subscriber stock. Both panels
  retain labelled scales and legend text; no unique-reader count is implied.

There are two figures, each with panels, rather than additional hidden charts.
They are generated directly by the included source code. Interpretation of the
recording break remains assumption-dependent, as stated in the memo and report.
