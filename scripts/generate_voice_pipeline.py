#!/usr/bin/env python3
"""
Generate End-to-End Performance Test Pipeline Diagram
Visualizes latency measurements for each component in the voice recognition system
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# Create figure with high DPI for museum quality
fig, ax = plt.subplots(1, 1, figsize=(14, 18), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 22)
ax.axis('off')

# Color palette - technical with performance coding
color_fast = '#27AE60'        # Green for fast components
color_medium = '#F39C12'      # Amber for medium components
color_slow = '#E74C3C'        # Red for slower components
color_neutral = '#34495E'     # Gray for timing data
color_line = '#7F8C8D'        # Neutral gray
color_text = '#2C3E50'        # Text color

# Margins and spacing
margin = 0.3
y_start = 19
y_spacing = 2.2

# Helper function to draw performance component boxes
def draw_performance_component(ax, x, y, width, height, label, sublabel, latency_ms, color):
    """Draw component box with latency annotation."""
    # Rectangle for components
    rect = FancyBboxPatch((x, y), width, height,
                         boxstyle="round,pad=0.05",
                         edgecolor=color, facecolor='white',
                         linewidth=2, zorder=2)
    ax.add_patch(rect)

    # Add latency bar (visual indicator of relative speed)
    bar_width = width * 0.8
    bar_height = 0.15
    bar_x = x + (width - bar_width) / 2
    latency_bar = Rectangle((bar_x, y + 0.15), bar_width, bar_height,
                            edgecolor='none', facecolor=color, alpha=0.3, zorder=1)
    ax.add_patch(latency_bar)

    # Add labels
    ax.text(x + width/2, y + height/2 + 0.15, label,
            fontsize=8.5, weight='bold', ha='center', va='center',
            fontfamily='sans-serif', color=color)

    # Latency annotation
    ax.text(x + width/2, y + height/2 - 0.25, f'{latency_ms:.0f}ms',
            fontsize=7, ha='center', va='center',
            fontfamily='monospace', color=color, weight='bold')

    if sublabel:
        ax.text(x + width/2, y + 0.05, sublabel,
                fontsize=5.5, ha='center', va='bottom',
                fontfamily='sans-serif', color='#7F8C8D', style='italic')

# Helper function to draw arrows
def draw_arrow(ax, x1, y1, x2, y2, style='simple', color=None):
    if color is None:
        color = color_line
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->', mutation_scale=15,
                           linewidth=1.2, color=color, zorder=1)
    ax.add_patch(arrow)

# Draw title/header
ax.text(5.5, 21, 'END-TO-END PERFORMANCE TEST PIPELINE',
        fontsize=12, weight='bold', ha='center', fontfamily='sans-serif',
        color=color_text)
ax.text(5.5, 20.5, 'Voice Recognition System - Latency Analysis',
        fontsize=8, ha='center', fontfamily='sans-serif',
        color=color_line, style='italic')

# Performance metrics (typical values from testing)
# Estimated based on end_to_end_performance_test.py
latencies = {
    'wake_word': 2000,      # Wake word detection: ~2000ms
    'stt': 250,             # Speech-to-text: ~250ms
    'camera': 75,           # Camera capture: ~75ms
    'encoding': 50,         # Face encoding: ~50ms
    'recognition': 800,     # Face recognition (MCP): ~800ms
    'response_gen': 200,    # Response generation: ~200ms
    'tts': 1500,           # Text-to-speech: ~1500ms (varies by text length)
    'total': 4875          # Total end-to-end: ~4875ms
}

# Determine color based on latency (faster = green, slower = red)
def get_latency_color(ms):
    if ms < 100:
        return color_fast
    elif ms < 500:
        return color_medium
    else:
        return color_slow

# Layer 1: Wake Word Detection
y_pos = 19.5
color1 = get_latency_color(latencies['wake_word'])
draw_performance_component(ax, 2.5, y_pos, 5, 0.8,
                          'WAKE WORD DETECTION', 'Vosk - "skyy" trigger',
                          latencies['wake_word'], color1)
ax.text(9, y_pos + 0.4, '◆ Decision Point\n(Continuous listening)',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 2: Speech-to-Text
y_pos -= 2.0
color2 = get_latency_color(latencies['stt'])
draw_performance_component(ax, 3, y_pos, 4, 0.7,
                          'SPEECH-TO-TEXT', 'Whisper Transcription',
                          latencies['stt'], color2)
ax.text(8.5, y_pos + 0.35, 'Fast processing\nof audio input',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 3: Camera Capture
y_pos -= 2.0
color3 = get_latency_color(latencies['camera'])
draw_performance_component(ax, 3.5, y_pos, 3, 0.7,
                          'CAMERA CAPTURE', 'OpenCV Frame Grab',
                          latencies['camera'], color3)
ax.text(8.5, y_pos + 0.35, 'Single-frame\nacquisition',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 4: Face Encoding
y_pos -= 2.0
color4 = get_latency_color(latencies['encoding'])
draw_performance_component(ax, 3.5, y_pos, 3, 0.7,
                          'FACE ENCODING', 'JPEG Base64 Conversion',
                          latencies['encoding'], color4)
ax.text(8.5, y_pos + 0.35, 'Image compression\nfor transmission',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 5: Face Recognition (MCP)
y_pos -= 2.0
color5 = get_latency_color(latencies['recognition'])
draw_performance_component(ax, 2.5, y_pos, 5, 0.8,
                          'FACE RECOGNITION', 'MCP Tool - InsightFace + ChromaDB',
                          latencies['recognition'], color5)
ax.text(9, y_pos + 0.4, 'Includes face\ndetection & matching',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 6: Response Generation
y_pos -= 2.0
color6 = get_latency_color(latencies['response_gen'])
draw_performance_component(ax, 3, y_pos, 4, 0.7,
                          'RESPONSE GEN', 'Gemma 3 (Simulated)',
                          latencies['response_gen'], color6)
ax.text(8.5, y_pos + 0.35, 'LLM-based\ngreeting',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 7: Text-to-Speech
y_pos -= 2.0
color7 = get_latency_color(latencies['tts'])
draw_performance_component(ax, 3.5, y_pos, 3, 0.7,
                          'TEXT-TO-SPEECH', 'pyttsx3 Synthesis',
                          latencies['tts'], color7)
ax.text(8.5, y_pos + 0.35, 'Audio synthesis\nof response',
        fontsize=5.5, ha='left', va='center', color='#7F8C8D', style='italic')

# Arrow down
draw_arrow(ax, 5.5, y_pos, 5.5, y_pos - 0.55, color=color_line)

# Layer 8: END-TO-END TOTAL
y_pos -= 1.8
total_color = color_medium
# Highlight box for total
total_rect = FancyBboxPatch((2.5, y_pos), 5, 0.9,
                           boxstyle="round,pad=0.1",
                           edgecolor=total_color, facecolor='#f8f8f8',
                           linewidth=2.5, zorder=2)
ax.add_patch(total_rect)

ax.text(5.5, y_pos + 0.6, 'END-TO-END LATENCY',
        fontsize=10, weight='bold', ha='center', va='center',
        fontfamily='sans-serif', color=total_color)
ax.text(5.5, y_pos + 0.2, f'{latencies["total"]:.0f}ms ({latencies["total"]/1000:.2f}s)',
        fontsize=9, ha='center', va='center',
        fontfamily='monospace', color=total_color, weight='bold')

# Add performance characteristics
perf_y = 1.0
ax.text(5.5, perf_y + 0.5, 'PERFORMANCE CHARACTERISTICS',
        fontsize=8, weight='bold', ha='center', fontfamily='sans-serif', color=color_text)

# Latency breakdown table
breakdown_y = perf_y
ax.text(0.8, breakdown_y, 'Slowest Component:', fontsize=6, weight='bold', color=color_slow)
ax.text(2.5, breakdown_y, 'Wake Word Detection (2000ms)', fontsize=5.5, color=color_slow)

ax.text(0.8, breakdown_y - 0.35, 'Heavy Components:', fontsize=6, weight='bold', color=color_slow)
ax.text(2.5, breakdown_y - 0.35, 'TTS (1500ms) • Face Recognition (800ms)',
        fontsize=5.5, color=color_slow)

ax.text(0.8, breakdown_y - 0.7, 'Test Framework:', fontsize=6, weight='bold', color=color_neutral)
ax.text(2.5, breakdown_y - 0.7, 'end_to_end_performance_test.py (Speech • Camera • MCP • Audio)',
        fontsize=5.5, color=color_neutral)

# Color legend for latency
legend_y = 0.15
ax.plot([0.5, 0.7], [legend_y, legend_y], linewidth=3, color=color_fast)
ax.text(0.85, legend_y, 'Fast (<100ms)', fontsize=5, va='center')

ax.plot([3.2, 3.4], [legend_y, legend_y], linewidth=3, color=color_medium)
ax.text(3.55, legend_y, 'Medium (100-500ms)', fontsize=5, va='center')

ax.plot([6.0, 6.2], [legend_y, legend_y], linewidth=3, color=color_slow)
ax.text(6.35, legend_y, 'Slow (>500ms)', fontsize=5, va='center')

plt.tight_layout(pad=0.5)
plt.savefig('C:\\Users\\Fritz\\Documents\\MDC\\Advanced NLP\\PROJECT\\FACIAL_RECOGNITION_MCP\\voice_pipeline_diagram.png',
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("Voice pipeline diagram created successfully!")
print("Saved to: voice_pipeline_diagram.png")
