Both languages transcribed accurately in real-time at RTF ≈ 1.0x on a single GPU. Native punctuation, capitalization, and domain-specific vocabulary handled correctly with no post-processing needed. Last utterance capture working after EOF fix.

Metric                   Spanish (es-US)    English (en-US)
-----------------------  -----------------  ---------------
Audio Duration           57.8s              124.7s
Wall Time                58.64s             125.41s
RTF                      1.01x              1.01x
Min TTFB                 268ms              275ms
Max TTFB                 603ms              1844ms
Typical TTFB             ~350ms             ~850ms
Last Utterance Captured  Yes                Yes
Accuracy                 Excellent          Excellent
