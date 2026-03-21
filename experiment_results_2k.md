# Experiment Results: 2000 Novel Pattern Experiments

**Total experiments**: 2000
**Successful**: 2000
**Failed**: 0
**Spread range**: 672.00 - 1344.00

## Top 50 Patterns by Spread Score

### #1: symmetry_1402_mobius_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "mobius",
        "surface": "mobius",
        "major_radius": 91.11823107618815,
        "width": 85.33771871502577,
        "v_lines": 49,
        "view_angle_x": -51.315536239649994,
        "view_angle_y": 30.01565069198061
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 86.33751191386045,
        "sweep_angle": 647.5945151351888
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 16.835729544927833,
        "outer_radius": 189.2166355731958,
        "sweep_angle": 1957.3142248736226,
        "start_angle": 184.12204110914126
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #2: symmetry_1403_harmonograph_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 1.66,
        "freq2": 3.58,
        "amp1": 122.89648659340025,
        "amp2": 119.69485316612673,
        "phase1": 266.3183024342117,
        "phase2": 284.53742818272343,
        "decay1": 0.009132805789375698,
        "decay2": 0.019473301578689435,
        "freq3": 0.85,
        "amp3": 61.8839012020363,
        "phase3": 6.331492881262473,
        "decay3": 0.0051951935299476785,
        "duration": 53.566201292898384,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 24.964683381534932,
        "frequency": 189.15657081645674
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### #3: symmetry_1415_sphere_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 81.60588983566018,
        "v_lines": 29
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 20.512231676663834,
        "frequency": 177.76093259021053
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #4: symmetry_1417_rack_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rack",
        "straight_teeth": 26,
        "end_teeth": 37,
        "gear_teeth": 36,
        "tooth_pitch": 1.9015967639101499,
        "hole_position": 1.1471482899704541,
        "laps": 1,
        "cycles": 2
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -19.923431471168456,
        "end_x": 4.647950931634796,
        "start_y": -8.013349301965661,
        "end_y": -70.10606637354965
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 2.4781487645995504,
        "frequency": 104.79939424999702
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #5: symmetry_1419_spirograph_rail_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_rail",
        "rail_length": 60.44167116641742,
        "gear_teeth": 51,
        "tooth_pitch": 1.213408311969517,
        "hole_position": 0.5457259102777094,
        "passes": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 182.1076914591159,
        "sweep_angle": 109.02297108311237,
        "start_angle": 30.27140357662131,
        "cycles": 5
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #6: symmetry_1420_klein_bottle_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "klein_bottle",
        "surface": "klein",
        "major_radius": 175.36512693741312,
        "minor_radius": 31.320626004567757,
        "v_lines": 52,
        "view_angle_x": -27.31984848304333,
        "view_angle_y": -1.2667034253133522
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 858.5318494049797,
        "origin_x": 8.846367115351804,
        "origin_y": 11.595858663209654
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 199.76375995266056,
        "sweep_angle": 76.81797933710146
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### #7: symmetry_1422_polygon_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "polygon",
        "sides": 9,
        "radius": 90.38652030760039,
        "cycles": 28,
        "rotation": 262.54841185361585
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 26.024515770387936,
        "frequency": 10.952670399358036
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### #8: symmetry_1425_rose_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rose",
        "k_num": 10,
        "k_den": 2,
        "radius": 41.61202788676695,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 15.512289895321647,
        "frequency": 273.97988182540547
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.4396222917122374,
        "scale_y": 4.785360503450763,
        "end_scale_x": 3.1976989464468617,
        "end_scale_y": 2.1408060321509716
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 9.120001539197988,
        "frequency": 217.11759906432104
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### #9: symmetry_1427_sphere_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 175.19137850640476,
        "v_lines": 42
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 20.52130446656738,
        "sweep_angle": 127.23919600395905,
        "start_angle": 264.3245698349349,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.05859077721456537,
        "duration": 16.319001174417167
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #10: symmetry_1428_lissajous_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 1,
        "freq_y": 12,
        "amplitude_x": 74.96513605568792,
        "amplitude_y": 145.96887097370052,
        "phase": 14.526080787419314,
        "cycles": 4
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 223.9002074600472,
        "sweep_angle": 141.31669813216345
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #11: symmetry_1430_torus_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 111.17981817320322,
        "minor_radius": 67.68068374241028,
        "v_lines": 51,
        "view_angle_x": 59.014537879102775,
        "view_angle_y": -6.557346821340303
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.1262657186109004,
        "duration": 108.31449774632146
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 90.94992826405911,
        "end_x": -3.137008980235123,
        "start_y": -86.61464019081204,
        "end_y": -88.0323561437315
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 26.87628073731583,
        "outer_radius": 156.66104513614047,
        "sweep_angle": 2113.562035560947,
        "start_angle": 127.65824312807162
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### #12: symmetry_1432_polygon_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "polygon",
        "sides": 4,
        "radius": 73.17113897703629,
        "cycles": 13,
        "rotation": 304.82007129425546
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 2.505424729934132,
        "scale_y": 4.998373079321305,
        "end_scale_x": 4.954940646496398,
        "end_scale_y": 4.430463079734345
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.019874954437214064,
        "duration": 70.19642658396593
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #13: symmetry_1443_lissajous_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 4,
        "freq_y": 5,
        "amplitude_x": 74.19399350306577,
        "amplitude_y": 31.59335487762422,
        "phase": 99.8033979979719,
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.704840410944673,
        "scale_y": 4.061754664752801,
        "end_scale_x": 1.8098542063806442,
        "end_scale_y": 0.9256082706120439
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.8120307748384294,
        "scale_y": 3.440709654958201
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### #14: symmetry_1445_star_shape_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 10,
        "outer_radius": 122.16649245404652,
        "inner_radius": 57.16209058919729,
        "cycles": 18,
        "rotation": 59.76946529113704
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 220.67077771341272,
        "sweep_angle": 366.3981358730233
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### #15: symmetry_1450_lissajous_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 7,
        "freq_y": 7,
        "amplitude_x": 66.07496934999469,
        "amplitude_y": 130.580706610387,
        "phase": 330.84618646222845,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 886.2926160106507,
        "origin_x": 7.469946610645714,
        "origin_y": -15.463640653070321
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #16: symmetry_1452_rose_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rose",
        "k_num": 5,
        "k_den": 8,
        "radius": 70.12125710478058,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 66.53280325429253,
        "sweep_angle": 180.12343668904802
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### #17: symmetry_1453_rack_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rack",
        "straight_teeth": 56,
        "end_teeth": 41,
        "gear_teeth": 26,
        "tooth_pitch": 1.301487221272439,
        "hole_position": 0.5968607792151721,
        "laps": 5,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 15.321745344102624,
        "end_x": -37.54158633274991,
        "start_y": 92.87272399088258,
        "end_y": 3.6156344700571452
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 34.416572876379135,
        "outer_radius": 203.06499722861167,
        "sweep_angle": 1063.7191116646386,
        "start_angle": 50.6729355686784
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.07966893566331339,
        "duration": 59.40183743122062
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #18: symmetry_1456_sphere_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 160.9294901870228,
        "v_lines": 54
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.12607900985589945,
        "duration": 124.96673736554276
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 539.187769481447,
        "origin_x": 46.19001655535746,
        "origin_y": 42.83125908814556
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.491281706592627,
        "scale_y": 0.28519000129451155,
        "end_scale_x": 2.586240878605808,
        "end_scale_y": 3.4541307916579185
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #19: symmetry_1458_star_shape_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 8,
        "outer_radius": 110.03351945896186,
        "inner_radius": 20.26651241072664,
        "cycles": 10,
        "rotation": 70.74622995268581
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -62.74414815041345,
        "end_x": -52.33332554108501,
        "start_y": 40.04432577445547,
        "end_y": 65.39660770980726
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #20: symmetry_1459_torus_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 194.94981780871032,
        "minor_radius": 69.97215427546425,
        "v_lines": 16,
        "view_angle_x": 46.61227353622078,
        "view_angle_y": -9.35654761815271
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 128.25968549308314,
        "sweep_angle": 496.9167705617271,
        "start_angle": 48.86761330378131,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.5145772642421886,
        "end_scale": 2.630199859130376
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 20.35346527993657,
        "sweep_angle": 235.19052714747954,
        "start_angle": 90.11620468559755,
        "cycles": 4
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #21: symmetry_1460_circle_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "circle",
        "radius": 71.2564825439429,
        "cycles": 26
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.685480835503917,
        "frequency": 214.91315607223655
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 67.9915128644704,
        "outer_radius": 130.017692649766,
        "sweep_angle": 2711.651232260295,
        "start_angle": 335.67192779258244
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.8396023985565582,
        "scale_y": 1.2163676950266187
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #22: symmetry_1461_rose_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rose",
        "k_num": 5,
        "k_den": 3,
        "radius": 66.81084398224527,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.11664457955443427,
        "duration": 73.83832010527168
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 103.28575404403577,
        "sweep_angle": 514.9052634359784,
        "start_angle": 17.24453106036766,
        "cycles": 1
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### #23: symmetry_1464_spirograph_rail_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_rail",
        "rail_length": 194.05707028054178,
        "gear_teeth": 56,
        "tooth_pitch": 1.709966354187952,
        "hole_position": 0.8824694617818527,
        "passes": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 3.2970273246396387,
        "scale_y": 0.46193824351597196,
        "end_scale_x": 4.681809698959559,
        "end_scale_y": 1.6903355505693793
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #24: symmetry_1465_torus_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 156.90323635767913,
        "minor_radius": 59.285404273706924,
        "v_lines": 70,
        "view_angle_x": 11.046320155490989,
        "view_angle_y": -25.222663511476476
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.081174183795999,
        "duration": 121.03486783470778
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 29.81309267856606,
        "frequency": 173.00446147062095
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 109.6422291957166,
        "sweep_angle": 315.842807106239
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #25: symmetry_1467_helix_ribbon_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "helix_ribbon",
        "surface": "helix_ribbon",
        "major_radius": 113.377970610901,
        "width": 46.09255396367263,
        "twists": 1.581861367661495,
        "v_lines": 58,
        "view_angle_x": 46.00091978666069,
        "view_angle_y": -17.63048950547602
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.08767788572203157,
        "duration": 109.12000735861592
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 18.997802746549638,
        "frequency": 50.34177477640492
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.2975613132950947,
        "scale_y": 2.8406750697409717,
        "end_scale_x": 0.3115584298012596,
        "end_scale_y": 0.34475971808733696
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #26: symmetry_1471_rose_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rose",
        "k_num": 7,
        "k_den": 6,
        "radius": 89.16421965544616,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 667.0194884916251,
        "origin_x": -43.0401056937314,
        "origin_y": -20.044350841001148
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.09189349881084108,
        "duration": 45.9465034316579
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### #27: symmetry_1473_torus_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 140.63715759248896,
        "minor_radius": 44.827528508579356,
        "v_lines": 44,
        "view_angle_x": -3.051922781859979,
        "view_angle_y": 35.238565067664155
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 2.3268863896018144,
        "end_scale": 0.5938070426919294
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -26.349537983464913,
        "end_x": -15.360920875591063,
        "start_y": 31.28671319733266,
        "end_y": -51.00402417386416
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### #28: symmetry_1474_spirograph_gear_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 84,
        "rolling_teeth": 21,
        "tooth_pitch": 1.3706621035406072,
        "hole_position": 0.416948180090957,
        "inside": "false",
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.641933697950709,
        "frequency": 222.09846274844418
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 211.15948883105597,
        "sweep_angle": 250.92139090011725
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #29: symmetry_1477_spirograph_rail_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_rail",
        "rail_length": 224.50893353319387,
        "gear_teeth": 26,
        "tooth_pitch": 0.6790407641690993,
        "hole_position": 1.067488486782115,
        "passes": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 45.392383560394194,
        "outer_radius": 244.05385649303633,
        "sweep_angle": 908.6344277640408,
        "start_angle": 5.943555401259228
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #30: symmetry_1479_spirograph_gear_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 96,
        "rolling_teeth": 48,
        "tooth_pitch": 0.7702354656608017,
        "hole_position": 0.424929874502012,
        "inside": "false",
        "cycles": 4
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 20.870407544994293,
        "end_x": -27.021908862874426,
        "start_y": -67.98168646882374,
        "end_y": 84.38271824808217
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 3.874024026458736,
        "scale_y": 3.0593456858480996,
        "end_scale_x": 2.811801471444381,
        "end_scale_y": 2.3152004168323597
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.10606109312826714,
        "duration": 56.84947573003088
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### #31: symmetry_1482_ellipse_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ellipse",
        "radius_x": 38.325521942615,
        "radius_y": 99.42953767053716,
        "cycles": 12,
        "rotation": 22.724754959910577
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.576887309376,
        "end_scale": 2.032656842204373
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 40.239692853523415,
        "outer_radius": 172.2455310584949,
        "sweep_angle": 750.9490993223236,
        "start_angle": 249.37943557423748
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #32: symmetry_1485_figure8_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "figure8",
        "surface": "figure8",
        "major_radius": 152.66725326056468,
        "minor_radius": 72.7806380867545,
        "v_lines": 41,
        "view_angle_x": -47.67499319476681,
        "view_angle_y": -58.82306195202355
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 75.33769474615521,
        "outer_radius": 113.71534147160872,
        "sweep_angle": 1736.7538851780932,
        "start_angle": 336.46679307775986
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.05083334035018522,
        "duration": 113.60483947001299
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 77.51509616002852,
        "outer_radius": 234.53466853127563,
        "sweep_angle": 1212.8143826738014,
        "start_angle": 40.0011902614214
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #33: symmetry_1490_torus_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 53.963094157331085,
        "minor_radius": 43.474064324057494,
        "v_lines": 64,
        "view_angle_x": -40.33854014113035,
        "view_angle_y": -50.87577557294256
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.07038004159372459,
        "duration": 146.71093416090164
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 169.7301968630228,
        "sweep_angle": 424.7768808716305
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 62.254025640611616,
        "outer_radius": 195.3587299210363,
        "sweep_angle": 594.6972774452787,
        "start_angle": 270.4952975160927
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #34: symmetry_1491_star_shape_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 9,
        "outer_radius": 82.30045381024959,
        "inner_radius": 16.274220748021218,
        "cycles": 15,
        "rotation": 52.395892369292994
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.1219046404094892,
        "duration": 80.83512294777567
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 91.28422594750036,
        "outer_radius": 269.5398387349198,
        "sweep_angle": 1500.7619364075404,
        "start_angle": 88.10650557848314
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 7.968376478523742,
        "frequency": 82.42108078944744
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### #35: symmetry_1495_helix_ribbon_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "helix_ribbon",
        "surface": "helix_ribbon",
        "major_radius": 83.61757316877961,
        "width": 37.262509489806355,
        "twists": 1.5169744796862767,
        "v_lines": 62,
        "view_angle_x": -44.917794889454036,
        "view_angle_y": 18.92495221440575
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.1045303801322357,
        "scale_y": 1.3246062247859065,
        "end_scale_x": 4.569311585020707,
        "end_scale_y": 3.9189275018813117
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #36: symmetry_1497_guilloche_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "guilloche",
        "inner": 88.29514558398185,
        "outer": 231.23786704223505,
        "nodes": 195.69864030716838,
        "div": 43,
        "n0": 13.024984545581782,
        "h0": 20.665645773813015,
        "n1": 17.3317176139994,
        "h1": 6.7057061519655035
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.12853122086241942,
        "duration": 69.48926653457532
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### #37: symmetry_1501_lissajous_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 2,
        "freq_y": 8,
        "amplitude_x": 77.46997297952628,
        "amplitude_y": 46.42857719903424,
        "phase": 198.41241495653873,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 204.35574730207873,
        "sweep_angle": 288.910821369126,
        "start_angle": 32.601852849155684,
        "cycles": 5
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### #38: symmetry_1502_ribbon_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ribbon",
        "surface": "ribbon",
        "major_radius": 119.05297227642995,
        "width": 13.086907404659094,
        "twists": 3.2831139727824175,
        "v_lines": 74,
        "view_angle_x": -23.50100218610828,
        "view_angle_y": -0.6187003886722167
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 24.289209943752628,
        "frequency": 112.54706004828215
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### #39: symmetry_1508_harmonograph_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 1.62,
        "freq2": 3.07,
        "amp1": 68.41881377034574,
        "amp2": 69.0400086598979,
        "phase1": 161.11946712769205,
        "phase2": 76.04287954673472,
        "decay1": 0.024221541920248668,
        "decay2": 0.014598053602901041,
        "freq3": 1.56,
        "amp3": 67.26308705604347,
        "phase3": 53.63237870281494,
        "decay3": 0.026319744818389473,
        "duration": 43.7624401296057,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 39.698841907569545,
        "sweep_angle": 127.33833534421022,
        "start_angle": 168.0894355822448,
        "cycles": 3
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #40: symmetry_1509_lissajous_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 7,
        "freq_y": 7,
        "amplitude_x": 21.79104766241909,
        "amplitude_y": 107.2452111203576,
        "phase": 154.12400481067317,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 67.16907995198045,
        "outer_radius": 204.21576975296665,
        "sweep_angle": 2802.4012820463563,
        "start_angle": 32.1596974368753
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #41: symmetry_1514_mobius_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "mobius",
        "surface": "mobius",
        "major_radius": 191.78314594307963,
        "width": 28.96810812217336,
        "v_lines": 73,
        "view_angle_x": 38.95617933325018,
        "view_angle_y": 54.28899638949589
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 384.9213999310324,
        "sweep_angle": 658.6110435206881
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.901771366685316,
        "end_scale": 0.15167288606230875
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### #42: symmetry_1516_helix_ribbon_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "helix_ribbon",
        "surface": "helix_ribbon",
        "major_radius": 125.08678896624033,
        "width": 45.519592877472775,
        "twists": 4.736522844196248,
        "v_lines": 30,
        "view_angle_x": 34.39585514895549,
        "view_angle_y": 53.29126854513218
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 132.30497758405295,
        "sweep_angle": 319.2317743106828,
        "start_angle": 199.9342741189432,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 18.69841051561761,
        "frequency": 138.14898319781742
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #43: symmetry_1519_torus_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 160.7810623154818,
        "minor_radius": 30.006451688617634,
        "v_lines": 57,
        "view_angle_x": -29.16582934292157,
        "view_angle_y": 19.183160370439737
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.08586721317066112,
        "duration": 45.600669408524006
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #44: symmetry_1526_spirograph_rail_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_rail",
        "rail_length": 152.21737717210067,
        "gear_teeth": 26,
        "tooth_pitch": 1.505838515501259,
        "hole_position": 0.8035383639032885,
        "passes": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 270.180031481356,
        "sweep_angle": 649.3194716647748
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #45: symmetry_1528_spirograph_gear_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 84,
        "rolling_teeth": 48,
        "tooth_pitch": 2.2014710145818386,
        "hole_position": 0.4437689878668842,
        "inside": "true",
        "cycles": 2
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.6826453271691149,
        "end_scale": 0.405660537289366
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 133.43260042372214,
        "sweep_angle": 594.285131080588
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.397748068214941,
        "scale_y": 0.8488254501013373
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### #46: symmetry_1529_sphere_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 83.3122329794613,
        "v_lines": 77
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.5979413602855117,
        "end_scale": 0.9004910904704859
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### #47: symmetry_1535_mobius_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "mobius",
        "surface": "mobius",
        "major_radius": 109.34904264479812,
        "width": 93.95007329937239,
        "v_lines": 16,
        "view_angle_x": 57.67437863355778,
        "view_angle_y": -34.26914296858216
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 27.93466872260685,
        "frequency": 203.7170977532297
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.7458110913363931,
        "scale_y": 0.40146645698039607,
        "end_scale_x": 2.461012720548102,
        "end_scale_y": 1.1406307478159738
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #48: symmetry_1545_lissajous_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 10,
        "freq_y": 10,
        "amplitude_x": 58.36342015219215,
        "amplitude_y": 80.4643653315401,
        "phase": 265.84977038217727,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 12.595721556746707,
        "outer_radius": 55.10819629974672,
        "sweep_angle": 2617.88784555028,
        "start_angle": 4.181252733205736
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### #49: symmetry_1548_figure8_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "figure8",
        "surface": "figure8",
        "major_radius": 116.56920159706681,
        "minor_radius": 15.680733148012179,
        "v_lines": 48,
        "view_angle_x": 9.597178140739942,
        "view_angle_y": -15.934992607696053
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 27.247868058117426,
        "outer_radius": 79.09373398776759,
        "sweep_angle": 1609.895043199009,
        "start_angle": 245.61703730118379
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.10564423940997636,
        "duration": 104.87654438302444
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### #50: symmetry_1553_harmonograph_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 4.49,
        "freq2": 8.44,
        "amp1": 129.39012019334172,
        "amp2": 40.54174970544313,
        "phase1": 58.43983866766719,
        "phase2": 337.5083986519324,
        "decay1": 0.04824048776846415,
        "decay2": 0.023506430755232018,
        "freq3": 4.47,
        "amp3": 115.50184968008246,
        "phase3": 151.88057164423287,
        "decay3": 0.0006107688064324546,
        "duration": 35.7286214923581,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 36.169253789044205,
        "outer_radius": 88.24889086049642,
        "sweep_angle": 1365.0034646798058,
        "start_angle": 20.610270317336482
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.08517852473174183,
        "duration": 144.29743201134607
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 37.27775661858624,
        "sweep_angle": 355.32183727729205,
        "start_angle": 100.85750217794717,
        "cycles": 3
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

## Best Deep Chains (4+ transforms)

### Deep #1: deep_209_harmonograph_spiral_arc_noise_scale_noise (spread: 1343.80)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 1.72,
        "freq2": 3.0,
        "amp1": 51.389807010890735,
        "amp2": 110.6508594313686,
        "phase1": 219.99231217751543,
        "phase2": 248.94490250904002,
        "decay1": 0.029748449315235983,
        "decay2": 0.0393653789766793,
        "freq3": 1.26,
        "amp3": 65.53378280202656,
        "phase3": 208.4278652792268,
        "decay3": 0.04657399096930029,
        "duration": 38.381365903959264,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 43.171248292756665,
        "outer_radius": 137.59093806313487,
        "sweep_angle": 530.5200281089083,
        "start_angle": 153.83658218079407
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 2.4153130623591297,
        "frequency": 143.89096904315804
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 2.175472483935963,
        "end_scale": 0.8958137739800268
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 12.705858323552185,
        "frequency": 66.9043839370437
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #2: deep_284_line_damping_scale_damping_arc (spread: 1343.60)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "line",
        "length": 292.51610137363497,
        "cycles": 22,
        "rotation": 80.72287643805011
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.08145541311268611,
        "duration": 100.61155478250153
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.0848981660916786,
        "end_scale": 1.3683310048999715
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.048557021927445716,
        "duration": 147.78607262589458
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 213.55372948341298,
        "sweep_angle": 419.5479959210085,
        "start_angle": 106.37338820601141,
        "cycles": 1
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #3: deep_233_klein_bottle_rotation_rotation_noise_noise_scale (spread: 1343.56)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "klein_bottle",
        "surface": "klein",
        "major_radius": 108.31513002104232,
        "minor_radius": 65.4917420285839,
        "v_lines": 49,
        "view_angle_x": -0.037901818209860494,
        "view_angle_y": 55.7944615193459
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 193.34907700572495,
        "origin_x": -44.39455469122634,
        "origin_y": 28.77785319165288
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1221.366918234095,
        "origin_x": -28.83218243188881,
        "origin_y": 15.384993454304634
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 14.021925760303798,
        "frequency": 205.0329579167739
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 4.894132072933161,
        "frequency": 175.9069851318804
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.3995697020422014,
        "end_scale": 0.5106123694613176
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #4: exotic_1847_klein_bottle (spread: 1343.38)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "klein_bottle",
        "surface": "klein",
        "major_radius": 182.5320437737459,
        "minor_radius": 11.654457539692025,
        "v_lines": 49,
        "view_angle_x": -33.31517321494716,
        "view_angle_y": 41.299207031319824
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 18.96659188798968,
        "end_x": 65.21417747932264,
        "start_y": -88.0859842145964,
        "end_y": 42.197693590120764
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1326.7610123629142,
        "origin_x": -7.219691986413501,
        "origin_y": -5.353998491791245
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 40.06439670959699,
        "outer_radius": 75.94069750751568,
        "sweep_angle": 1168.5424724152522,
        "start_angle": 349.84814666185724
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #5: deep_275_circle_noise_damping_translation_arc (spread: 1342.86)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "circle",
        "radius": 143.14165609882457,
        "cycles": 4
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.337182691798358,
        "frequency": 276.39676942560106
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.12495233053470742,
        "duration": 79.18086421930587
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 42.71274239293538,
        "end_x": -61.89116694621397,
        "start_y": 72.38734485717478,
        "end_y": 56.42438868612473
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 191.68189677341783,
        "sweep_angle": 330.70631453413944,
        "start_angle": 155.27109196991907,
        "cycles": 2
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #6: deep_58_spiral_shape_translation_spiral_arc_arc_stretch (spread: 1342.66)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spiral_shape",
        "start_radius": 38.906201862496296,
        "end_radius": 90.34880297850947,
        "turns": 6.861251574216441
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 60.25184483030952,
        "end_x": -72.32029307931376,
        "start_y": -49.999357682198585,
        "end_y": 28.235807240889443
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 59.90866708819881,
        "outer_radius": 107.3489214854284,
        "sweep_angle": 2491.648537368265,
        "start_angle": 306.4197773105204
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 39.29127883551172,
        "sweep_angle": 190.99677057458845,
        "start_angle": 161.75491933457727,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.189024249463292,
        "scale_y": 0.6402251343636483,
        "end_scale_x": 4.120175628106402,
        "end_scale_y": 4.4462229138464355
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #7: deep_84_ribbon_spiral_arc_stretch_stretch_bend_bend (spread: 1342.48)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ribbon",
        "surface": "ribbon",
        "major_radius": 82.59038152663301,
        "width": 87.73572184030508,
        "twists": 0.8104421926345351,
        "v_lines": 74,
        "view_angle_x": 59.2180129491658,
        "view_angle_y": -31.900617943001173
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 61.97273331740938,
        "outer_radius": 223.30422943937043,
        "sweep_angle": 2422.323872507185,
        "start_angle": 85.28545251961943
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.931338691480604,
        "scale_y": 2.702005060471633,
        "end_scale_x": 1.520738818441306,
        "end_scale_y": 2.872246966905126
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 3.204767060711984,
        "scale_y": 2.250562795013809,
        "end_scale_x": 4.866993129649692,
        "end_scale_y": 4.7196147671931765
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 320.74770051279165,
        "sweep_angle": 249.92677554825545
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 181.05589542694773,
        "sweep_angle": 236.92306116042676
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #8: deep_80_star_shape_arc_translation_spiral_arc_translation_noise (spread: 1342.06)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 3,
        "outer_radius": 110.13433377584056,
        "inner_radius": 30.596724501806115,
        "cycles": 6,
        "rotation": -34.05001933137697
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 178.76678680632725,
        "sweep_angle": 492.3881348756115,
        "start_angle": 338.6288245485241,
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -56.17427981293122,
        "end_x": -73.28624356063918,
        "start_y": -69.36288706216416,
        "end_y": 49.54696743017132
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 47.42610538881022,
        "outer_radius": 170.79597188793224,
        "sweep_angle": 1546.486753735865,
        "start_angle": 193.5063675695523
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 52.37192399422142,
        "end_x": 36.068383983879585,
        "start_y": 19.162893106244567,
        "end_y": 57.47413796465145
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.679065336146257,
        "frequency": 212.6110069209824
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #9: deep_243_figure8_rotation_noise_scale_rotation_rotation (spread: 1341.80)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "figure8",
        "surface": "figure8",
        "major_radius": 155.58530945338566,
        "minor_radius": 10.095455424687156,
        "v_lines": 19,
        "view_angle_x": -13.814487850575652,
        "view_angle_y": 22.890076636886107
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 917.4860475828295,
        "origin_x": 25.288801096222826,
        "origin_y": 19.805498381030176
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 17.469266343393347,
        "frequency": 66.10819594837048
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.9752290724090307,
        "end_scale": 1.0735145608611871
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1526.114780883856,
        "origin_x": 41.000411417076705,
        "origin_y": -13.600947791354436
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 399.5966569963426,
        "origin_x": -13.44091410536106,
        "origin_y": 11.913345039542264
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #10: deep_256_klein_bottle_noise_arc_translation_scale_bend (spread: 1341.76)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "klein_bottle",
        "surface": "klein",
        "major_radius": 102.23148686242118,
        "minor_radius": 58.37354924812763,
        "v_lines": 27,
        "view_angle_x": 38.04464439326932,
        "view_angle_y": 46.7671662458018
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 23.025891602920648,
        "frequency": 105.90331324041715
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 26.61469356138891,
        "sweep_angle": 603.1816882991495,
        "start_angle": 80.04882519198365,
        "cycles": 2
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -38.514335266732914,
        "end_x": -58.03179870513344,
        "start_y": 96.22191351444266,
        "end_y": -15.038985474678682
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.5098853033093905,
        "end_scale": 2.3466076933170794
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 45.73126809783181,
        "sweep_angle": 104.39399348666493
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #11: deep_69_spirograph_gear_bend_noise_damping_bend_rotation (spread: 1341.70)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 48,
        "rolling_teeth": 18,
        "tooth_pitch": 0.6136545082283549,
        "hole_position": 0.9055991072067962,
        "inside": "false",
        "cycles": 4
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 258.7001177402343,
        "sweep_angle": 50.8972700211872
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 9.04531387564737,
        "frequency": 287.21180013654947
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.04050729704409674,
        "duration": 123.02890402003167
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 140.05053242900465,
        "sweep_angle": 80.3513875986886
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 531.044447172428,
        "origin_x": -8.437825378588492,
        "origin_y": -3.5557842224664995
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #12: deep_72_rack_arc_scale_spiral_arc_translation_spiral_arc (spread: 1341.66)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rack",
        "straight_teeth": 61,
        "end_teeth": 33,
        "gear_teeth": 12,
        "tooth_pitch": 1.5014540525368916,
        "hole_position": 0.7702816438810294,
        "laps": 2,
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 36.91230244085362,
        "sweep_angle": 407.68098334761896,
        "start_angle": 275.18548129460623,
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.6473911548608811,
        "end_scale": 0.38037630947173195
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 81.54075055428513,
        "outer_radius": 169.18525154622122,
        "sweep_angle": 2726.150388727546,
        "start_angle": 271.78746202540583
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 20.492590232376017,
        "end_x": -19.722583144787095,
        "start_y": -91.94901876851418,
        "end_y": -92.21720675075595
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 82.35692696747908,
        "outer_radius": 200.64348772410324,
        "sweep_angle": 735.330474732641,
        "start_angle": 321.5274091480826
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #13: deep_250_ellipse_noise_noise_spiral_arc_rotation (spread: 1341.66)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ellipse",
        "radius_x": 41.42161591383865,
        "radius_y": 26.284589303178034,
        "cycles": 15,
        "rotation": 243.74281973958608
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 12.135496580871017,
        "frequency": 149.68728127880806
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 28.33036384100768,
        "frequency": 272.99185031426015
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 45.780219758414724,
        "outer_radius": 197.49406105624007,
        "sweep_angle": 1437.6540047784708,
        "start_angle": 139.0005425678135
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 884.1745200181556,
        "origin_x": -14.864496657188731,
        "origin_y": 47.75236282168032
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #14: deep_1_lissajous_scale_scale_rotation_bend_rotation (spread: 1341.56)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 1,
        "freq_y": 12,
        "amplitude_x": 55.7538113879855,
        "amplitude_y": 49.017395959346956,
        "phase": 265.1296370990445,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.8943297836124073,
        "end_scale": 0.19216977049717243
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.8903225319697292,
        "end_scale": 1.565530335499751
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1655.8737255987303,
        "origin_x": 21.601961292240347,
        "origin_y": 20.13249735902359
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 111.56303015505777,
        "sweep_angle": 436.593321874377
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2207.072554292051,
        "origin_x": -34.03406836231099,
        "origin_y": -7.738560184649742
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #15: deep_297_lissajous_scale_rotation_noise_arc (spread: 1341.22)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 12,
        "freq_y": 1,
        "amplitude_x": 129.40584732955136,
        "amplitude_y": 53.768339540873754,
        "phase": 182.6997757525027,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.5115895919836684,
        "end_scale": 1.7600623126096295
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1354.2805779409036,
        "origin_x": 48.29505625076392,
        "origin_y": 30.538756210921747
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 25.412625223910013,
        "frequency": 73.98217982314121
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 85.44316383743393,
        "sweep_angle": 584.417235579341,
        "start_angle": 257.3476085528408,
        "cycles": 2
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #16: deep_199_ribbon_rotation_arc_arc_arc (spread: 1340.98)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ribbon",
        "surface": "ribbon",
        "major_radius": 81.78129703231306,
        "width": 59.178179257317844,
        "twists": 4.626953318138562,
        "v_lines": 80,
        "view_angle_x": -2.0368403586369865,
        "view_angle_y": 27.590830021174654
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1140.7326090081317,
        "origin_x": 40.60402860010292,
        "origin_y": 2.6799090530589282
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 59.17351882029556,
        "sweep_angle": 268.9285308602341,
        "start_angle": 284.10785802267196,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 32.209607190944155,
        "sweep_angle": 502.4974592436938,
        "start_angle": 3.00030308943394,
        "cycles": 4
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 172.4857762156358,
        "sweep_angle": 665.1073316176477,
        "start_angle": 129.678891235155,
        "cycles": 1
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #17: exotic_1963_spirograph_rail (spread: 1340.72)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_rail",
        "rail_length": 211.2231395158513,
        "gear_teeth": 24,
        "tooth_pitch": 1.0261697273214392,
        "hole_position": 0.520686558357706,
        "passes": 8
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.08829672110786585,
        "duration": 118.07251666911577
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.042691480325780365,
        "duration": 58.92175527446795
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 232.05437062133424,
        "sweep_angle": 488.18960179367355,
        "start_angle": 233.2716133748272,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 68.98913345080771,
        "sweep_angle": 424.0241261241813,
        "start_angle": 287.0145110180692,
        "cycles": 3
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #18: deep_195_line_translation_bend_spiral_arc_rotation (spread: 1339.62)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "line",
        "length": 117.4204579468213,
        "cycles": 27,
        "rotation": 156.34958289524772
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 49.53573145386454,
        "end_x": 69.89563346252089,
        "start_y": 85.73063315664885,
        "end_y": 26.777420606342872
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 50.02734104372452,
        "sweep_angle": 391.82451254439167
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 58.59367564948022,
        "outer_radius": 114.02227890792143,
        "sweep_angle": 1626.0520583270265,
        "start_angle": 79.48698293530266
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1969.4423262112155,
        "origin_x": 49.73673030203781,
        "origin_y": 47.10402447403686
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #19: deep_117_spirograph_gear_scale_bend_bend_arc_spiral_arc (spread: 1339.20)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 72,
        "rolling_teeth": 30,
        "tooth_pitch": 0.7325665958952206,
        "hole_position": 1.213401843269317,
        "inside": "false",
        "cycles": 6
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.8680806939159178,
        "end_scale": 1.5657405151962498
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 57.68727920205467,
        "sweep_angle": 421.7963025195537
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 275.1042534169611,
        "sweep_angle": 120.18871764371168
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 80.0279159524303,
        "sweep_angle": 288.4556167081477,
        "start_angle": 288.2940559198183,
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 50.748206708401646,
        "outer_radius": 120.46211523691483,
        "sweep_angle": 2737.757808795838,
        "start_angle": 49.000264710018854
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Deep #20: deep_335_guilloche_bend_rotation_rotation_scale (spread: 1338.94)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "guilloche",
        "inner": 49.77130286471195,
        "outer": 277.87574491979905,
        "nodes": 98.82753555266012,
        "div": 29,
        "n0": 11.246923290397268,
        "h0": 36.358650250654286,
        "n1": 13.635114362680534,
        "h1": 10.685183936779353
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 222.9446131661958,
        "sweep_angle": 156.64637673816833
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 270.28109615242613,
        "origin_x": -0.8357710614912861,
        "origin_y": 45.36611899172175
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1859.8838163742055,
        "origin_x": -35.8467989129763,
        "origin_y": -29.577998723416776
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.7689247265465762,
        "end_scale": 1.6916565910767056
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

## Best Group Combinations

### Group #1: symgroup_1825 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "lissajous",
            "freq_x": 12,
            "freq_y": 9,
            "amplitude_x": 82.70763494045104,
            "amplitude_y": 113.13951638514973,
            "phase": 235.04820143512669,
            "cycles": 0
          }
        ],
        [
          {
            "type": "ellipse",
            "radius_x": 49.583898699755224,
            "radius_y": 24.392863784689563,
            "cycles": 2,
            "rotation": 236.841837382467
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1315.706311039927,
        "origin_x": 19.863199585931383,
        "origin_y": 18.771354162235838
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### Group #2: symgroup_1846 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "line",
            "length": 39.72301520569319,
            "cycles": 20,
            "rotation": 190.0128583135332
          }
        ],
        [
          {
            "type": "sphere",
            "surface": "sphere",
            "major_radius": 198.76760055749932,
            "v_lines": 42
          }
        ],
        [
          {
            "type": "rack",
            "straight_teeth": 44,
            "end_teeth": 15,
            "gear_teeth": 42,
            "tooth_pitch": 1.0218382403124433,
            "hole_position": 0.9787395976198745,
            "laps": 5,
            "cycles": 5
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.121662464414774,
        "end_scale": 1.5252144491896982
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### Group #3: symgroup_1853 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "rack",
            "straight_teeth": 89,
            "end_teeth": 32,
            "gear_teeth": 31,
            "tooth_pitch": 1.0921563580503733,
            "hole_position": 0.8567025430381199,
            "laps": 2,
            "cycles": 2
          }
        ],
        [
          {
            "type": "spirograph_gear",
            "fixed_teeth": 96,
            "rolling_teeth": 45,
            "tooth_pitch": 0.5840660618933562,
            "hole_position": 0.48274311552929716,
            "inside": "false",
            "cycles": 8
          }
        ],
        [
          {
            "type": "spirograph_rail",
            "rail_length": 139.5127384072676,
            "gear_teeth": 55,
            "tooth_pitch": 1.487112542551073,
            "hole_position": 0.8103339840588573,
            "passes": 1
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 2.8511395232224954,
        "end_scale": 2.2128101661776665
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Group #4: symgroup_1869 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "guilloche",
            "inner": 50.47796358691221,
            "outer": 253.86560044846047,
            "nodes": 153.20688692425585,
            "div": 53,
            "n0": 16.47214207510811,
            "h0": 16.61471352284355,
            "n1": 9.371561341413937,
            "h1": 2.0356501888806964
          }
        ],
        [
          {
            "type": "rack",
            "straight_teeth": 29,
            "end_teeth": 14,
            "gear_teeth": 42,
            "tooth_pitch": 2.7846749766255003,
            "hole_position": 0.5322690254185445,
            "laps": 5,
            "cycles": 4
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 26.321974077271513,
        "frequency": 17.638516068775232
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### Group #5: symgroup_1909 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "spiral_shape",
            "start_radius": 5.387618945823847,
            "end_radius": 126.09747327283056,
            "turns": 8.623146831990894
          }
        ],
        [
          {
            "type": "rose",
            "k_num": 12,
            "k_den": 3,
            "radius": 24.238741410879598,
            "cycles": 0
          }
        ],
        [
          {
            "type": "ribbon",
            "surface": "ribbon",
            "major_radius": 69.94271528304947,
            "width": 95.19328205322579,
            "twists": 3.7552716505740102,
            "v_lines": 42,
            "view_angle_x": -19.080971384797472,
            "view_angle_y": 6.126739103570358
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 574.6905493185291,
        "origin_x": 1.2221984052581547,
        "origin_y": -19.636006395092853
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Group #6: symgroup_1932 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "ellipse",
            "radius_x": 66.01703464428115,
            "radius_y": 97.3980337562791,
            "cycles": 20,
            "rotation": 128.55959785505442
          }
        ],
        [
          {
            "type": "ribbon",
            "surface": "ribbon",
            "major_radius": 57.06644816527998,
            "width": 79.89890088846067,
            "twists": 4.287529514624605,
            "v_lines": 62,
            "view_angle_x": 40.71142852907897,
            "view_angle_y": 23.11471487758959
          }
        ],
        [
          {
            "type": "spirograph_rail",
            "rail_length": 105.09301369491604,
            "gear_teeth": 55,
            "tooth_pitch": 1.6297528810213253,
            "hole_position": 1.0287129192318032,
            "passes": 6
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2087.7123817439683,
        "origin_x": -39.77892889266484,
        "origin_y": -35.77805253637916
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Group #7: symgroup_1936 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "line",
            "length": 42.16697541125016,
            "cycles": 1,
            "rotation": 205.68311072499543
          }
        ],
        [
          {
            "type": "spirograph_gear",
            "fixed_teeth": 60,
            "rolling_teeth": 48,
            "tooth_pitch": 0.7245367969673046,
            "hole_position": 0.9341039443919152,
            "inside": "false",
            "cycles": 4
          }
        ],
        [
          {
            "type": "harmonograph",
            "freq1": 2.05,
            "freq2": 3.23,
            "amp1": 102.86844887429979,
            "amp2": 58.65798372919883,
            "phase1": 152.50701923832148,
            "phase2": 9.164031470054287,
            "decay1": 0.027139211673349192,
            "decay2": 0.03589950021218463,
            "freq3": 3.5,
            "amp3": 25.379865552864093,
            "phase3": 241.00229770729234,
            "decay3": 0.014091696095674029,
            "duration": 119.57651523963898,
            "cycles": 1
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 64.46483751887459,
        "outer_radius": 160.68127964169827,
        "sweep_angle": 2500.992589421696,
        "start_angle": 222.6425170569629
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Group #8: symgroup_1941 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "klein_bottle",
            "surface": "klein",
            "major_radius": 103.77872612374496,
            "minor_radius": 70.66106249268408,
            "v_lines": 44,
            "view_angle_x": 11.070812963881636,
            "view_angle_y": -49.797318360737876
          }
        ],
        [
          {
            "type": "ribbon",
            "surface": "ribbon",
            "major_radius": 160.32067888254574,
            "width": 90.15394712691074,
            "twists": 3.408092414878813,
            "v_lines": 10,
            "view_angle_x": -46.44021878138609,
            "view_angle_y": 1.9038490252797473
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.6239624295109234,
        "end_scale": 0.7683884194313204
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Group #9: symgroup_1959 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "torus",
            "surface": "torus",
            "major_radius": 140.28656418499622,
            "minor_radius": 30.782631754434245,
            "v_lines": 55,
            "view_angle_x": 47.92531960770572,
            "view_angle_y": 54.26016555044765
          }
        ],
        [
          {
            "type": "spirograph_gear",
            "fixed_teeth": 84,
            "rolling_teeth": 40,
            "tooth_pitch": 1.3458174062018577,
            "hole_position": 0.5904995538215527,
            "inside": "false",
            "cycles": 3
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -11.80635964988592,
        "end_x": 97.63393100724593,
        "start_y": -48.87249106617473,
        "end_y": -15.172187310613069
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Group #10: symgroup_1965 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "star_shape",
            "points": 3,
            "outer_radius": 121.12461046420036,
            "inner_radius": 10.884579743037216,
            "cycles": 17,
            "rotation": -177.9463813036672
          }
        ],
        [
          {
            "type": "spirograph_rail",
            "rail_length": 290.8538282645492,
            "gear_teeth": 43,
            "tooth_pitch": 1.4469279454807826,
            "hole_position": 1.1247932053072691,
            "passes": 5
          }
        ],
        [
          {
            "type": "rack",
            "straight_teeth": 23,
            "end_teeth": 16,
            "gear_teeth": 48,
            "tooth_pitch": 2.7574818734535436,
            "hole_position": 0.879326138687158,
            "laps": 2,
            "cycles": 3
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 208.4643889686485,
        "sweep_angle": 475.5372039421214
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### Group #11: group3_481_rose_klein_bottle_harmonograph (spread: 1343.90)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "rose",
            "k_num": 7,
            "k_den": 6,
            "radius": 80.91536925688982,
            "cycles": 0
          }
        ],
        [
          {
            "type": "klein_bottle",
            "surface": "klein",
            "major_radius": 97.43219048942404,
            "minor_radius": 75.31141522107633,
            "v_lines": 77,
            "view_angle_x": 28.238114680128348,
            "view_angle_y": 45.10998848256614
          }
        ],
        [
          {
            "type": "harmonograph",
            "freq1": 1.89,
            "freq2": 2.28,
            "amp1": 133.4699122930739,
            "amp2": 36.330324707784015,
            "phase1": 306.93633312270725,
            "phase2": 112.78579723360052,
            "decay1": 0.045090187846383585,
            "decay2": 0.010150353514993306,
            "freq3": 1.31,
            "amp3": 41.30118556884068,
            "phase3": 302.6442648751163,
            "decay3": 0.018147003137779116,
            "duration": 111.83210446234794,
            "cycles": 1
          },
          {
            "type": "damping",
            "decay_rate": 0.07388766317889103,
            "duration": 108.5044503549525
          },
          {
            "type": "arc",
            "radius": 89.74531012285412,
            "sweep_angle": 595.4716356395868,
            "start_angle": 57.53246578793331,
            "cycles": 2
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 73.82297319883787,
        "sweep_angle": 658.0597284929405
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #12: unconventional_1362_spirograph_rail_harmonograph (spread: 1343.86)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "spirograph_rail",
            "rail_length": 221.3078333917184,
            "gear_teeth": 15,
            "tooth_pitch": 0.9550800085433737,
            "hole_position": 0.4681945886466669,
            "passes": 8
          },
          {
            "type": "spiral_arc",
            "inner_radius": 71.20496410653475,
            "outer_radius": 173.0988085935748,
            "sweep_angle": 2588.970228031121,
            "start_angle": 187.58471292848358
          }
        ],
        [
          {
            "type": "harmonograph",
            "freq1": 2.96,
            "freq2": 4.23,
            "amp1": 71.43731232456679,
            "amp2": 107.71164284275372,
            "phase1": 258.3207754866902,
            "phase2": 256.1869988722515,
            "decay1": 0.03333198907746883,
            "decay2": 0.010060932065995044,
            "freq3": 1.96,
            "amp3": 76.15484249177808,
            "phase3": 143.86052859096912,
            "decay3": 0.034363295472827945,
            "duration": 75.19109152600561,
            "cycles": 1
          },
          {
            "type": "spiral_arc",
            "inner_radius": 42.27164802584353,
            "outer_radius": 151.84797246390863,
            "sweep_angle": 2105.2730287555983,
            "start_angle": 131.3300402530006
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 59.951816410225234,
        "sweep_angle": 320.74391898559225
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #13: surfcombo_1947 (spread: 1343.74)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "figure8",
            "surface": "figure8",
            "major_radius": 174.21956983399338,
            "minor_radius": 18.95084588333217,
            "v_lines": 41,
            "view_angle_x": 46.636275104059635,
            "view_angle_y": -20.076557060634542
          }
        ],
        [
          {
            "type": "spirograph_gear",
            "fixed_teeth": 60,
            "rolling_teeth": 24,
            "tooth_pitch": 1.1771573658340924,
            "hole_position": 1.21641733323273,
            "inside": "false",
            "cycles": 6
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1735.8227749162247,
        "origin_x": 31.98502254740886,
        "origin_y": -41.73803490262471
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #14: unconventional_1345_sphere_spirograph_gear (spread: 1343.52)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "sphere",
            "surface": "sphere",
            "major_radius": 172.16209654135656,
            "v_lines": 67
          }
        ],
        [
          {
            "type": "spirograph_gear",
            "fixed_teeth": 96,
            "rolling_teeth": 21,
            "tooth_pitch": 0.5810507113381322,
            "hole_position": 0.267819644600633,
            "inside": "true",
            "cycles": 5
          },
          {
            "type": "stretch",
            "scale_x": 1.4354633948417872,
            "scale_y": 0.26643429905075705,
            "end_scale_x": 4.242504816830311,
            "end_scale_y": 1.0139835326680278
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 27.562011085320794,
        "frequency": 24.98026428318656
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 62.093371548796185,
        "outer_radius": 120.9350950370617,
        "sweep_angle": 2135.669369511675,
        "start_angle": 303.50048032358785
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #15: branchtx_793 (spread: 1343.30)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "spiral_shape",
            "start_radius": 16.574882856325978,
            "end_radius": 64.75503662922276,
            "turns": 11.274836436146185
          },
          {
            "type": "damping",
            "decay_rate": 0.006863038230268973,
            "duration": 113.61260500965835
          }
        ],
        [
          {
            "type": "sphere",
            "surface": "sphere",
            "major_radius": 94.35625032892179,
            "v_lines": 55
          },
          {
            "type": "scale",
            "start_scale": 2.783991094803471,
            "end_scale": 2.0432320275078957
          }
        ]
      ]
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #16: group3_416_rack_line_guilloche (spread: 1343.14)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "rack",
            "straight_teeth": 20,
            "end_teeth": 24,
            "gear_teeth": 14,
            "tooth_pitch": 1.317789289294317,
            "hole_position": 0.7070601726721015,
            "laps": 3,
            "cycles": 4
          },
          {
            "type": "scale",
            "start_scale": 2.2083864640998203,
            "end_scale": 1.0129487826495638
          },
          {
            "type": "rotation",
            "total_degrees": 1299.123571814777,
            "origin_x": 43.23680006347871,
            "origin_y": 29.41973993278802
          }
        ],
        [
          {
            "type": "line",
            "length": 73.31162956059492,
            "cycles": 18,
            "rotation": 238.00695375761845
          }
        ],
        [
          {
            "type": "guilloche",
            "inner": 51.96878491188367,
            "outer": 238.31271075886818,
            "nodes": 220.58640902435292,
            "div": 31,
            "n0": 13.793604990228173,
            "h0": 11.346155824769296,
            "n1": 3.877229021531612,
            "h1": 32.74088522268153
          },
          {
            "type": "arc",
            "radius": 50.3121435319765,
            "sweep_angle": 489.9068164214066,
            "start_angle": 31.93621503040039,
            "cycles": 5
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1301.7494001065115,
        "origin_x": -0.930884809987873,
        "origin_y": 11.121718740870776
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #17: branchtx_630 (spread: 1343.00)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "star_shape",
            "points": 12,
            "outer_radius": 52.81249334837925,
            "inner_radius": 33.721685582298306,
            "cycles": 20,
            "rotation": -117.24972009276823
          },
          {
            "type": "spiral_arc",
            "inner_radius": 86.75776878469681,
            "outer_radius": 234.26005013678287,
            "sweep_angle": 2447.3299087129003,
            "start_angle": 281.4164279354721
          },
          {
            "type": "translation",
            "start_x": 56.371740034280435,
            "end_x": -54.89963124811255,
            "start_y": -54.6725654255944,
            "end_y": -14.635704327959417
          }
        ],
        [
          {
            "type": "mobius",
            "surface": "mobius",
            "major_radius": 102.50121053903499,
            "width": 13.128258006712933,
            "v_lines": 60,
            "view_angle_x": -49.00343575412214,
            "view_angle_y": -54.12540833542312
          },
          {
            "type": "rotation",
            "total_degrees": 1516.9473126750497,
            "origin_x": -11.09100385968813,
            "origin_y": -0.21657959527359338
          },
          {
            "type": "scale",
            "start_scale": 2.364126351962233,
            "end_scale": 2.4400847685288287
          }
        ]
      ]
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #18: branchtx_752 (spread: 1342.88)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "polygon",
            "sides": 5,
            "radius": 127.06098716112203,
            "cycles": 25,
            "rotation": 314.0615874316297
          },
          {
            "type": "translation",
            "start_x": -74.48820303114047,
            "end_x": 49.06031224493938,
            "start_y": 95.07193355333447,
            "end_y": -48.548017601388274
          },
          {
            "type": "bend",
            "radius": 67.52882978604771,
            "sweep_angle": 99.58256869237452
          }
        ],
        [
          {
            "type": "ribbon",
            "surface": "ribbon",
            "major_radius": 137.8585745065161,
            "width": 94.11043285762376,
            "twists": 3.435170981516679,
            "v_lines": 19,
            "view_angle_x": 19.26394689115041,
            "view_angle_y": 49.22754058628922
          },
          {
            "type": "arc",
            "radius": 149.34852253303447,
            "sweep_angle": 303.8435699315846,
            "start_angle": 90.53201888398905,
            "cycles": 1
          },
          {
            "type": "scale",
            "start_scale": 0.7926217433039187,
            "end_scale": 1.4062470694416642
          }
        ],
        [
          {
            "type": "circle",
            "radius": 37.871187018234124,
            "cycles": 7
          },
          {
            "type": "noise",
            "amplitude": 21.244370896405698,
            "frequency": 94.7348065452189
          },
          {
            "type": "damping",
            "decay_rate": 0.04852482583396601,
            "duration": 125.73952514328448
          },
          {
            "type": "stretch",
            "scale_x": 1.8368381642469762,
            "scale_y": 3.6326356814299277,
            "end_scale_x": 3.5411997851739585,
            "end_scale_y": 0.5082271163670328
          }
        ]
      ]
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #19: group3_578_guilloche_star_shape_rose (spread: 1342.84)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "guilloche",
            "inner": 124.6970804109506,
            "outer": 137.94690499627438,
            "nodes": 173.39862831562846,
            "div": 83,
            "n0": 7.559536743431263,
            "h0": 31.38953690296309,
            "n1": 12.085718612630687,
            "h1": 33.11625214417616
          }
        ],
        [
          {
            "type": "star_shape",
            "points": 10,
            "outer_radius": 44.23803997803837,
            "inner_radius": 20.15040647604766,
            "cycles": 14,
            "rotation": 156.6607860419585
          },
          {
            "type": "spiral_arc",
            "inner_radius": 58.56753940136846,
            "outer_radius": 154.42022662746035,
            "sweep_angle": 2281.6817713419387,
            "start_angle": 46.92009744289918
          },
          {
            "type": "rotation",
            "total_degrees": 813.6067712815129,
            "origin_x": -42.5050989627076,
            "origin_y": 24.264540358275966
          }
        ],
        [
          {
            "type": "rose",
            "k_num": 1,
            "k_den": 3,
            "radius": 148.71299998939645,
            "cycles": 0
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 1.2769209657496075,
        "end_scale": 0.5696662015467915
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 11.505680523599821,
        "end_x": -44.41384515120244,
        "start_y": -66.72963261743368,
        "end_y": 23.884955140230886
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Group #20: unconventional_1393_sphere_ellipse (spread: 1342.60)
```json
{
  "steps": [
    {
      "kind": "group",
      "branches": [
        [
          {
            "type": "sphere",
            "surface": "sphere",
            "major_radius": 64.39741131379932,
            "v_lines": 34
          }
        ],
        [
          {
            "type": "ellipse",
            "radius_x": 138.9309000341974,
            "radius_y": 122.53094119910797,
            "cycles": 5,
            "rotation": 64.38711598966599
          }
        ]
      ]
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 40.76357280861912,
        "sweep_angle": 590.336908616249,
        "start_angle": 346.6842918340291,
        "cycles": 2
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

## Best Symmetry Combos

### Symmetry #1: symmetry_1402_mobius_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "mobius",
        "surface": "mobius",
        "major_radius": 91.11823107618815,
        "width": 85.33771871502577,
        "v_lines": 49,
        "view_angle_x": -51.315536239649994,
        "view_angle_y": 30.01565069198061
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 86.33751191386045,
        "sweep_angle": 647.5945151351888
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 16.835729544927833,
        "outer_radius": 189.2166355731958,
        "sweep_angle": 1957.3142248736226,
        "start_angle": 184.12204110914126
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Symmetry #2: symmetry_1403_harmonograph_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 1.66,
        "freq2": 3.58,
        "amp1": 122.89648659340025,
        "amp2": 119.69485316612673,
        "phase1": 266.3183024342117,
        "phase2": 284.53742818272343,
        "decay1": 0.009132805789375698,
        "decay2": 0.019473301578689435,
        "freq3": 0.85,
        "amp3": 61.8839012020363,
        "phase3": 6.331492881262473,
        "decay3": 0.0051951935299476785,
        "duration": 53.566201292898384,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 24.964683381534932,
        "frequency": 189.15657081645674
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### Symmetry #3: symmetry_1415_sphere_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 81.60588983566018,
        "v_lines": 29
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 20.512231676663834,
        "frequency": 177.76093259021053
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Symmetry #4: symmetry_1417_rack_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rack",
        "straight_teeth": 26,
        "end_teeth": 37,
        "gear_teeth": 36,
        "tooth_pitch": 1.9015967639101499,
        "hole_position": 1.1471482899704541,
        "laps": 1,
        "cycles": 2
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -19.923431471168456,
        "end_x": 4.647950931634796,
        "start_y": -8.013349301965661,
        "end_y": -70.10606637354965
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 2.4781487645995504,
        "frequency": 104.79939424999702
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### Symmetry #5: symmetry_1419_spirograph_rail_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_rail",
        "rail_length": 60.44167116641742,
        "gear_teeth": 51,
        "tooth_pitch": 1.213408311969517,
        "hole_position": 0.5457259102777094,
        "passes": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 182.1076914591159,
        "sweep_angle": 109.02297108311237,
        "start_angle": 30.27140357662131,
        "cycles": 5
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### Symmetry #6: symmetry_1420_klein_bottle_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "klein_bottle",
        "surface": "klein",
        "major_radius": 175.36512693741312,
        "minor_radius": 31.320626004567757,
        "v_lines": 52,
        "view_angle_x": -27.31984848304333,
        "view_angle_y": -1.2667034253133522
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 858.5318494049797,
        "origin_x": 8.846367115351804,
        "origin_y": 11.595858663209654
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 199.76375995266056,
        "sweep_angle": 76.81797933710146
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### Symmetry #7: symmetry_1422_polygon_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "polygon",
        "sides": 9,
        "radius": 90.38652030760039,
        "cycles": 28,
        "rotation": 262.54841185361585
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 26.024515770387936,
        "frequency": 10.952670399358036
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### Symmetry #8: symmetry_1425_rose_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rose",
        "k_num": 10,
        "k_den": 2,
        "radius": 41.61202788676695,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 15.512289895321647,
        "frequency": 273.97988182540547
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.4396222917122374,
        "scale_y": 4.785360503450763,
        "end_scale_x": 3.1976989464468617,
        "end_scale_y": 2.1408060321509716
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 9.120001539197988,
        "frequency": 217.11759906432104
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12
  }
}
```

### Symmetry #9: symmetry_1427_sphere_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 175.19137850640476,
        "v_lines": 42
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 20.52130446656738,
        "sweep_angle": 127.23919600395905,
        "start_angle": 264.3245698349349,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.05859077721456537,
        "duration": 16.319001174417167
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### Symmetry #10: symmetry_1428_lissajous_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 1,
        "freq_y": 12,
        "amplitude_x": 74.96513605568792,
        "amplitude_y": 145.96887097370052,
        "phase": 14.526080787419314,
        "cycles": 4
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 223.9002074600472,
        "sweep_angle": 141.31669813216345
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### Symmetry #11: symmetry_1430_torus_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 111.17981817320322,
        "minor_radius": 67.68068374241028,
        "v_lines": 51,
        "view_angle_x": 59.014537879102775,
        "view_angle_y": -6.557346821340303
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.1262657186109004,
        "duration": 108.31449774632146
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 90.94992826405911,
        "end_x": -3.137008980235123,
        "start_y": -86.61464019081204,
        "end_y": -88.0323561437315
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 26.87628073731583,
        "outer_radius": 156.66104513614047,
        "sweep_angle": 2113.562035560947,
        "start_angle": 127.65824312807162
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8,
    "mirror": "true"
  }
}
```

### Symmetry #12: symmetry_1432_polygon_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "polygon",
        "sides": 4,
        "radius": 73.17113897703629,
        "cycles": 13,
        "rotation": 304.82007129425546
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 2.505424729934132,
        "scale_y": 4.998373079321305,
        "end_scale_x": 4.954940646496398,
        "end_scale_y": 4.430463079734345
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.019874954437214064,
        "duration": 70.19642658396593
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

### Symmetry #13: symmetry_1443_lissajous_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 4,
        "freq_y": 5,
        "amplitude_x": 74.19399350306577,
        "amplitude_y": 31.59335487762422,
        "phase": 99.8033979979719,
        "cycles": 3
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.704840410944673,
        "scale_y": 4.061754664752801,
        "end_scale_x": 1.8098542063806442,
        "end_scale_y": 0.9256082706120439
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.8120307748384294,
        "scale_y": 3.440709654958201
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### Symmetry #14: symmetry_1445_star_shape_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 10,
        "outer_radius": 122.16649245404652,
        "inner_radius": 57.16209058919729,
        "cycles": 18,
        "rotation": 59.76946529113704
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 220.67077771341272,
        "sweep_angle": 366.3981358730233
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### Symmetry #15: symmetry_1450_lissajous_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "lissajous",
        "freq_x": 7,
        "freq_y": 7,
        "amplitude_x": 66.07496934999469,
        "amplitude_y": 130.580706610387,
        "phase": 330.84618646222845,
        "cycles": 5
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 886.2926160106507,
        "origin_x": 7.469946610645714,
        "origin_y": -15.463640653070321
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### Symmetry #16: symmetry_1452_rose_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rose",
        "k_num": 5,
        "k_den": 8,
        "radius": 70.12125710478058,
        "cycles": 0
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 66.53280325429253,
        "sweep_angle": 180.12343668904802
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4,
    "mirror": "true"
  }
}
```

### Symmetry #17: symmetry_1453_rack_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "rack",
        "straight_teeth": 56,
        "end_teeth": 41,
        "gear_teeth": 26,
        "tooth_pitch": 1.301487221272439,
        "hole_position": 0.5968607792151721,
        "laps": 5,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 15.321745344102624,
        "end_x": -37.54158633274991,
        "start_y": 92.87272399088258,
        "end_y": 3.6156344700571452
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 34.416572876379135,
        "outer_radius": 203.06499722861167,
        "sweep_angle": 1063.7191116646386,
        "start_angle": 50.6729355686784
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.07966893566331339,
        "duration": 59.40183743122062
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Symmetry #18: symmetry_1456_sphere_fold8 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "sphere",
        "surface": "sphere",
        "major_radius": 160.9294901870228,
        "v_lines": 54
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "damping",
        "decay_rate": 0.12607900985589945,
        "duration": 124.96673736554276
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 539.187769481447,
        "origin_x": 46.19001655535746,
        "origin_y": 42.83125908814556
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.491281706592627,
        "scale_y": 0.28519000129451155,
        "end_scale_x": 2.586240878605808,
        "end_scale_y": 3.4541307916579185
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 8
  }
}
```

### Symmetry #19: symmetry_1458_star_shape_fold4 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 8,
        "outer_radius": 110.03351945896186,
        "inner_radius": 20.26651241072664,
        "cycles": 10,
        "rotation": 70.74622995268581
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -62.74414815041345,
        "end_x": -52.33332554108501,
        "start_y": 40.04432577445547,
        "end_y": 65.39660770980726
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 4
  }
}
```

### Symmetry #20: symmetry_1459_torus_fold12 (spread: 1344.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "torus",
        "surface": "torus",
        "major_radius": 194.94981780871032,
        "minor_radius": 69.97215427546425,
        "v_lines": 16,
        "view_angle_x": 46.61227353622078,
        "view_angle_y": -9.35654761815271
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 128.25968549308314,
        "sweep_angle": 496.9167705617271,
        "start_angle": 48.86761330378131,
        "cycles": 1
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 0.5145772642421886,
        "end_scale": 2.630199859130376
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 20.35346527993657,
        "sweep_angle": 235.19052714747954,
        "start_angle": 90.11620468559755,
        "cycles": 4
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  },
  "symmetry": {
    "n_fold": 12,
    "mirror": "true"
  }
}
```

## Best Drift Patterns

### Drift #1: drift_1786_gear (spread: 1343.84)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 105,
        "rolling_teeth": 21,
        "tooth_pitch": 2.072457525010665,
        "hole_position": 0.5267792363500181,
        "inside": "false",
        "cycles": 8,
        "end_hole_position": 0.1349982295485664,
        "end_tooth_pitch": 1.990684911994841
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.770033622042124,
        "scale_y": 3.20295740448268,
        "end_scale_x": 3.573068414826676,
        "end_scale_y": 1.2613205084719956
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 28.67241995248542,
        "frequency": 147.9853629150711
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 145.58919450515629,
        "sweep_angle": 347.14366255092153
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #2: drift_1774_harmonograph (spread: 1343.76)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 3.22,
        "freq2": 6.96,
        "amp1": 148.25905526945513,
        "amp2": 86.90348456711882,
        "phase1": 13.729231186812466,
        "phase2": 17.36791971819107,
        "decay1": 0.01967276188034823,
        "decay2": 0.021502931212716254,
        "freq3": 5.62,
        "amp3": 43.68974200743725,
        "phase3": 326.8393871421089,
        "decay3": 0.02641817351119001,
        "duration": 109.69911616794973,
        "cycles": 1,
        "end_amp1": 37.96845758190716,
        "end_amp2": 53.45824033604779,
        "end_amp3": 81.50759128989088
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.38890394186841315,
        "scale_y": 2.403832036052027,
        "end_scale_x": 2.042418532046801,
        "end_scale_y": 3.2968202970391354
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2116.6978753522308,
        "origin_x": 15.530233155958967,
        "origin_y": -4.38998188007379
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 79.06562779220604,
        "outer_radius": 155.20767088387277,
        "sweep_angle": 1967.0488118539477,
        "start_angle": 244.0824403932857
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 58.541713257741236,
        "outer_radius": 151.5036690529718,
        "sweep_angle": 2265.9912565271834,
        "start_angle": 161.94989363345346
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #3: drift_1735_circle (spread: 1342.98)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "circle",
        "radius": 72.9515050113041,
        "end_radius": 16.61353263709864,
        "cycles": 13
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.505908241338581,
        "scale_y": 2.639625979082134,
        "end_scale_x": 1.3408162135782187,
        "end_scale_y": 3.807614535003475
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 2.8675836274692443,
        "scale_y": 3.952393108742462,
        "end_scale_x": 2.4429843856772937,
        "end_scale_y": 1.4590535411530094
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 42.57418657226066,
        "sweep_angle": 678.1482767310215
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.996589063980696,
        "frequency": 230.4097721983943
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #4: drift_1718_star_shape (spread: 1341.78)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 9,
        "outer_radius": 88.57711079172472,
        "inner_radius": 7.40897238320674,
        "cycles": 5,
        "rotation": -25.0111363304747,
        "end_outer_radius": 58.586912928087145,
        "end_inner_radius": 12.338332367205847,
        "end_rotation": -39.121691207734756
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.832423907412278,
        "scale_y": 3.951559079329665,
        "end_scale_x": 1.2459951336949389,
        "end_scale_y": 2.64256260652007
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 55.978411991111116,
        "outer_radius": 200.81664873634094,
        "sweep_angle": 2170.771750476247,
        "start_angle": 104.56334188478912
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "arc",
        "radius": 167.85155987074538,
        "sweep_angle": 126.95224286272169,
        "start_angle": 180.72162447868513,
        "cycles": 5
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #5: drift_1768_circle (spread: 1340.94)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "circle",
        "radius": 54.010567875427675,
        "end_radius": 35.215402853830895,
        "cycles": 21
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.3627952076434726,
        "scale_y": 2.3393494910633175,
        "end_scale_x": 2.823838796165397,
        "end_scale_y": 0.5633873006340983
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.248860992505277,
        "frequency": 111.60291754598143
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 9.126106991799631,
        "frequency": 227.9822999914998
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2412.892888322292,
        "origin_x": 25.368476131806403,
        "origin_y": -15.85274646497772
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #6: drift_1759_harmonograph (spread: 1340.52)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 4.05,
        "freq2": 7.25,
        "amp1": 123.32785097909141,
        "amp2": 56.99974840356171,
        "phase1": 106.89951879418425,
        "phase2": 346.96183550332177,
        "decay1": 0.04014304326789232,
        "decay2": 0.04085628958668836,
        "freq3": 7.11,
        "amp3": 84.98394335544454,
        "phase3": 103.41510621567609,
        "decay3": 0.006597801711014362,
        "duration": 88.74802806866893,
        "cycles": 1,
        "end_amp1": 74.64940435413871,
        "end_amp2": 18.227433665538065,
        "end_amp3": 81.13124890493168
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.3507407134000218,
        "scale_y": 0.5660325420128457,
        "end_scale_x": 2.264837781922883,
        "end_scale_y": 1.2232710958861832
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 5.323841901218464,
        "frequency": 7.699776854748276
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2293.699776312464,
        "origin_x": 8.92211806990175,
        "origin_y": 32.281870408936825
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #7: drift_1766_harmonograph (spread: 1340.48)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 2.72,
        "freq2": 6.22,
        "amp1": 45.32549281154561,
        "amp2": 31.97079123969857,
        "phase1": 115.35014816748416,
        "phase2": 242.19407294743797,
        "decay1": 0.00305907003002503,
        "decay2": 0.04949116340462459,
        "freq3": 4.12,
        "amp3": 93.13442435427721,
        "phase3": 75.85357128596146,
        "decay3": 0.028749548776045686,
        "duration": 114.06792188613143,
        "cycles": 1,
        "end_amp1": 18.13130268821421,
        "end_amp2": 90.26948128070049,
        "end_amp3": 74.47650124460802
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.27244388629850674,
        "scale_y": 4.28946664365303,
        "end_scale_x": 1.1876089610779463,
        "end_scale_y": 1.304797125204424
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 89.11865679351382,
        "end_x": 49.201848540835414,
        "start_y": -68.18829643736537,
        "end_y": -22.326463249045432
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2583.1617852524028,
        "origin_x": 18.135660413134985,
        "origin_y": 26.897242448476845
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 73.61735851434821,
        "outer_radius": 263.3068232163487,
        "sweep_angle": 2186.5614463507054,
        "start_angle": 137.72664468604665
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #8: drift_1787_harmonograph (spread: 1340.48)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "harmonograph",
        "freq1": 2.02,
        "freq2": 3.85,
        "amp1": 59.9670214524358,
        "amp2": 51.45605426085332,
        "phase1": 156.85477328841813,
        "phase2": 178.34463859259301,
        "decay1": 0.03865124852764348,
        "decay2": 0.009825382139588707,
        "freq3": 2.6,
        "amp3": 74.06582741175629,
        "phase3": 229.39400799744996,
        "decay3": 0.04368450447221463,
        "duration": 41.479305347911506,
        "cycles": 1,
        "end_amp1": 53.54065061801923,
        "end_amp2": 31.555616697515518,
        "end_amp3": 123.91637893781754
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.056674447904362,
        "scale_y": 2.7971944166452056,
        "end_scale_x": 3.528810366669474,
        "end_scale_y": 2.7544301018066255
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -38.156716364795294,
        "end_x": -2.559434735897753,
        "start_y": 40.03343705791585,
        "end_y": -29.430740607674096
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 69.45397793309522,
        "sweep_angle": 210.8129036285537
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #9: drift_1743_star_shape (spread: 1339.00)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 8,
        "outer_radius": 106.87464690172736,
        "inner_radius": 43.824377493633584,
        "cycles": 20,
        "rotation": 20.639438963264013,
        "end_outer_radius": 157.56997773901165,
        "end_inner_radius": 6.791247366752874,
        "end_rotation": -50.49584419922738
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.6005319979591248,
        "scale_y": 3.5505824355918656,
        "end_scale_x": 3.584533839197989,
        "end_scale_y": 1.7972645256408362
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 35.09122319011399,
        "end_x": -4.874530820045877,
        "start_y": 66.8603671085715,
        "end_y": -25.694082056752208
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 2.7467221112825686,
        "end_scale": 1.5708840756851465
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 29.92856242387623,
        "outer_radius": 141.84344394378047,
        "sweep_angle": 1573.7828967010844,
        "start_angle": 178.5482004293093
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #10: drift_1778_gear (spread: 1337.12)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 105,
        "rolling_teeth": 48,
        "tooth_pitch": 0.5517449956868782,
        "hole_position": 0.5350029645286234,
        "inside": "true",
        "cycles": 1,
        "end_hole_position": 0.5773693142673925,
        "end_tooth_pitch": 1.1601105566310108
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.1788727442804365,
        "scale_y": 2.4292420598003504,
        "end_scale_x": 0.6959651909676279,
        "end_scale_y": 1.7972755410609367
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1665.4203004459741,
        "origin_x": 39.998368244433706,
        "origin_y": 46.45541532644003
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #11: drift_1761_guilloche (spread: 1336.06)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "guilloche",
        "inner": 104.71499432178733,
        "outer": 127.1296145744712,
        "nodes": 123.28497363075363,
        "div": 79,
        "n0": 15.112479382383768,
        "h0": 8.696564624971021,
        "n1": 5.588667171432103,
        "h1": 10.32189665980364,
        "end_inner": 91.01304725016918,
        "end_outer": 170.9943101841539,
        "end_nodes": 134.84017914780196
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.541630512047583,
        "scale_y": 0.2956316266183537,
        "end_scale_x": 1.7568314318632823,
        "end_scale_y": 1.699361374308947
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.444321021149707,
        "scale_y": 4.237917035747737,
        "end_scale_x": 3.90238343586919,
        "end_scale_y": 0.45463718407241094
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 134.09651804098314,
        "sweep_angle": 39.58396619205129
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #12: drift_1771_circle (spread: 1334.12)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "circle",
        "radius": 94.89999880839694,
        "end_radius": 10.058280206553366,
        "cycles": 7
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.068196763679666,
        "scale_y": 3.834992570728958,
        "end_scale_x": 2.8201810798829072,
        "end_scale_y": 2.7011468258980917
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 258.8024557234568,
        "sweep_angle": 464.8368230785841
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.487393251665468,
        "scale_y": 0.5962604395913491,
        "end_scale_x": 4.913251008712285,
        "end_scale_y": 2.192522549472591
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 131.59709683704307,
        "sweep_angle": 75.73421779124223
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #13: drift_1703_star_shape (spread: 1333.90)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 10,
        "outer_radius": 124.99215475568619,
        "inner_radius": 53.72164185184837,
        "cycles": 12,
        "rotation": 159.53050313430288,
        "end_outer_radius": 46.52487939799768,
        "end_inner_radius": 3.4995443731101834,
        "end_rotation": -108.97984237124983
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.9941720611693272,
        "scale_y": 0.2591156156176414,
        "end_scale_x": 1.5064605203687846,
        "end_scale_y": 2.2358465542190276
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 5.535385907340499,
        "frequency": 268.2331675016788
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1417.6377345144347,
        "origin_x": 17.873931334207896,
        "origin_y": -34.07640045926587
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #14: drift_1736_ellipse (spread: 1333.48)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ellipse",
        "radius_x": 127.6573322133593,
        "radius_y": 25.55598203359201,
        "cycles": 9,
        "rotation": 70.252830745556,
        "end_radius_x": 25.927086679395273,
        "end_radius_y": 24.515332820247743,
        "end_rotation": 162.5123108023672
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 3.8629476243866994,
        "scale_y": 3.029467573337626,
        "end_scale_x": 3.054376216857356,
        "end_scale_y": 0.3255807230655598
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 1903.3152862600443,
        "origin_x": -49.671476501054165,
        "origin_y": 39.80995389982196
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 23.71987926053889,
        "frequency": 72.80777757442986
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #15: drift_1740_star_shape (spread: 1332.94)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 6,
        "outer_radius": 102.20847903023899,
        "inner_radius": 34.702573925938054,
        "cycles": 9,
        "rotation": -99.61469487073731,
        "end_outer_radius": 141.09326362078227,
        "end_inner_radius": 7.455472445757965,
        "end_rotation": 20.216696868790166
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.834600757124821,
        "scale_y": 4.005367595571388,
        "end_scale_x": 1.3134111365309744,
        "end_scale_y": 2.417039583541276
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "spiral_arc",
        "inner_radius": 32.05777402578416,
        "outer_radius": 193.63652129601417,
        "sweep_angle": 1846.9520811869832,
        "start_angle": 262.48360852533654
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #16: drift_1789_circle (spread: 1329.56)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "circle",
        "radius": 20.449474031526353,
        "end_radius": 92.69010404836833,
        "cycles": 19
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 1.5525635935572748,
        "scale_y": 2.5397762383194644,
        "end_scale_x": 0.30736924060410137,
        "end_scale_y": 1.0115067177008428
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.9995568358722324,
        "scale_y": 3.249024309327276,
        "end_scale_x": 1.454838830046079,
        "end_scale_y": 0.6650853373416141
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 150.54335568594882,
        "sweep_angle": 546.7064212548506
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 521.2032271009143,
        "origin_x": 6.504506800402041,
        "origin_y": -3.5416480744019907
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #17: drift_1714_ellipse (spread: 1329.16)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "ellipse",
        "radius_x": 96.26545003756534,
        "radius_y": 128.2530803190005,
        "cycles": 22,
        "rotation": 23.196809002614742,
        "end_radius_x": 77.48275233406575,
        "end_radius_y": 118.3296260899492,
        "end_rotation": 56.196383164738144
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 3.3312454230071844,
        "scale_y": 0.560775645327416,
        "end_scale_x": 3.4471153035241007,
        "end_scale_y": 2.714892986291327
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 2.5478053816500013,
        "end_scale": 1.004034666822605
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "scale",
        "start_scale": 2.6370617536669467,
        "end_scale": 2.291145297914902
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 257.96835812464957,
        "sweep_angle": 86.83202324108203
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #18: drift_1782_guilloche (spread: 1328.98)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "guilloche",
        "inner": 66.9817401693932,
        "outer": 340.415299709583,
        "nodes": 159.98753245646688,
        "div": 47,
        "n0": 14.047264732493268,
        "h0": 25.528770129986448,
        "n1": 5.368820483773757,
        "h1": 32.369713420668404,
        "end_inner": 67.39171389421288,
        "end_outer": 319.5364297376714,
        "end_nodes": 149.3421601295749
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 4.635532024744596,
        "scale_y": 4.942731428744034,
        "end_scale_x": 3.164969413459611,
        "end_scale_y": 1.9073121196417593
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 3.0691372824231733,
        "frequency": 217.29366135000612
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 177.11394734547082,
        "sweep_angle": 486.53120556141573
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": -94.65757463815747,
        "end_x": 86.02455642176847,
        "start_y": 7.029312935449312,
        "end_y": -29.728172806431957
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #19: drift_1742_gear (spread: 1327.04)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "spirograph_gear",
        "fixed_teeth": 48,
        "rolling_teeth": 30,
        "tooth_pitch": 1.2371349714235076,
        "hole_position": 0.31571266495492667,
        "inside": "true",
        "cycles": 1,
        "end_hole_position": 1.2846605231926551,
        "end_tooth_pitch": 0.8441744122256312
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 2.215176718050017,
        "scale_y": 1.5678473668753727,
        "end_scale_x": 1.092047222854426,
        "end_scale_y": 1.9600933493285777
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "noise",
        "amplitude": 13.058990901170294,
        "frequency": 25.716103624522262
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "translation",
        "start_x": 60.59686362912407,
        "end_x": -74.01320368384965,
        "start_y": -9.579565436852079,
        "end_y": 93.77237619046511
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 2052.7574286660656,
        "origin_x": 47.422805993316146,
        "origin_y": -31.176489881261695
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```

### Drift #20: drift_1733_star_shape (spread: 1325.60)
```json
{
  "steps": [
    {
      "kind": "single",
      "params": {
        "type": "star_shape",
        "points": 8,
        "outer_radius": 67.44430135581673,
        "inner_radius": 20.431377406156887,
        "cycles": 11,
        "rotation": 155.4264790239646,
        "end_outer_radius": 146.9602441005339,
        "end_inner_radius": 35.152050219872976,
        "end_rotation": -70.08518693787472
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "stretch",
        "scale_x": 0.5082130546059795,
        "scale_y": 0.6690221468844365,
        "end_scale_x": 2.275030313500902,
        "end_scale_y": 2.4920778248582534
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "bend",
        "radius": 115.61585586640923,
        "sweep_angle": 469.5907499719068
      }
    },
    {
      "kind": "single",
      "params": {
        "type": "rotation",
        "total_degrees": 128.48582552202387,
        "origin_x": 36.81770238810992,
        "origin_y": 2.2683105528434453
      }
    }
  ],
  "sampling": {
    "initial_samples": 20000,
    "output_samples": 3000
  },
  "output": {
    "stroke_width": 0.12
  }
}
```


## Lowest Scoring Patterns (to avoid)

- **stretch_1018_helix_ribbon**: spread=738.76
- **group3_370_circle_ellipse_rose**: spread=736.68
- **multi_stretch_1119_ellipse_2x**: spread=736.02
- **multi_stretch_1129_spirograph_rail_2x**: spread=734.44
- **deep_157_mobius_stretch_translation_bend_stretch**: spread=732.46
- **deep_338_line_rotation_damping_bend_damping**: spread=723.26
- **multi_stretch_1205_rack_2x**: spread=720.52
- **group3_559_line_circle_guilloche**: spread=720.28
- **deep_43_figure8_translation_translation_stretch_stretch**: spread=717.38
- **deep_236_spirograph_rail_scale_arc_translation_stretch**: spread=711.38
- **stretch_989_spirograph_rail**: spread=707.38
- **stretch_1065_spirograph_rail**: spread=703.38
- **multi_damping_1221_spirograph_rail_3x**: spread=697.64
- **stretch_991_spirograph_rail**: spread=690.46
- **multi_stretch_1247_spirograph_gear_2x**: spread=687.26
- **deep_207_spirograph_rail_stretch_stretch_damping_stretch**: spread=672.46
- **multi_noise_1157_line_3x**: spread=672.00
- **multi_stretch_1160_line_3x**: spread=672.00
- **multi_stretch_1212_line_2x**: spread=672.00
- **multi_stretch_1228_line_3x**: spread=672.00

## Failed Patterns (to avoid)


Total failures: 0

## Summary: Generator + Transform Coverage

### Average spread by generator:

| Generator | Count | Avg Spread | Max Spread | Min Spread |
|-----------|-------|-----------|------------|------------|
| mobius | 95 | 1216.8 | 1344.0 | 732.5 |
| harmonograph | 77 | 1208.7 | 1344.0 | 746.8 |
| sphere | 104 | 1239.8 | 1344.0 | 818.2 |
| rack | 93 | 1188.0 | 1344.0 | 720.5 |
| spirograph_rail | 107 | 1135.9 | 1344.0 | 672.5 |
| klein_bottle | 107 | 1240.2 | 1344.0 | 742.8 |
| polygon | 88 | 1230.2 | 1344.0 | 768.4 |
| rose | 73 | 1197.8 | 1344.0 | 741.2 |
| lissajous | 77 | 1203.3 | 1344.0 | 830.6 |
| torus | 100 | 1226.9 | 1344.0 | 771.4 |
| star_shape | 117 | 1219.4 | 1344.0 | 750.1 |
| circle | 110 | 1208.7 | 1344.0 | 736.7 |
| helix_ribbon | 86 | 1162.8 | 1344.0 | 738.8 |
| spirograph_gear | 82 | 1187.1 | 1344.0 | 687.3 |
| ellipse | 116 | 1181.4 | 1344.0 | 736.0 |
| figure8 | 82 | 1184.8 | 1344.0 | 717.4 |
| guilloche | 255 | 1243.1 | 1344.0 | 772.9 |
| ribbon | 74 | 1216.4 | 1344.0 | 767.3 |
| spiral_shape | 69 | 1220.1 | 1344.0 | 786.5 |
| line | 88 | 1160.5 | 1344.0 | 672.0 |

### Category performance:

| Category | Count | Avg Spread | Max Spread |
|----------|-------|-----------|------------|
| symmetry | 200 | 1329.9 | 1344.0 |
| symgroup | 32 | 1330.8 | 1344.0 |
| group3 | 250 | 1209.6 | 1343.9 |
| unconventional | 150 | 1188.1 | 1343.9 |
| drift | 100 | 1176.4 | 1343.8 |
| deep | 350 | 1178.0 | 1343.8 |
| surfcombo | 31 | 1239.0 | 1343.7 |
| highcycle | 100 | 1209.1 | 1343.6 |
| exotic | 30 | 1185.8 | 1343.4 |
| multi | 150 | 1166.2 | 1343.3 |
| branchtx | 200 | 1198.1 | 1343.3 |
| guilloche | 150 | 1257.8 | 1343.1 |
| stretch | 150 | 1132.0 | 1343.0 |
| liss | 21 | 1182.8 | 1338.1 |
| guill | 34 | 1209.9 | 1336.7 |
| group4 | 24 | 1170.8 | 1324.1 |
| deepgroup | 28 | 1168.3 | 1321.0 |
