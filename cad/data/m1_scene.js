window.SCENE_MANIFEST = {
  "schema_version": "1.0",
  "provenance": {
    "scientific_freeze": "round11.4a-freeze",
    "commit_sha": "8a6b557",
    "fixture_id": "RepairPop_F1_StaggerDeficit_00",
    "family": "Family_1_Stagger_Deficit",
    "evidence_tier": "native_engine_verified"
  },
  "clock": {
    "ticrate_hz": 35,
    "dt_s": 0.028571,
    "total_tics": 78,
    "total_duration_s": 2.2286
  },
  "units": {
    "coordinates": "meters (origin at port entrance, +x right, +y up)",
    "angles": "degrees (0 = +x, counterclockwise)",
    "time": "tics (35 Hz) and seconds"
  },
  "source_parameters": {
    "v_move_mps": 4.5,
    "omega_slew_deg_per_s": 360.0,
    "acquisition_latency_s": 0.15,
    "service_duration_s": 0.1,
    "initial_reticle_deg": 0.0
  },
  "geometry": {
    "boundary": [
      [
        0.0,
        -3.0
      ],
      [
        10.0,
        -3.0
      ],
      [
        10.0,
        3.0
      ],
      [
        0.0,
        3.0
      ],
      [
        0.0,
        -3.0
      ]
    ],
    "obstacles": [
      {
        "obstacle_id": 0,
        "vertices": [
          [
            0.2,
            0.25
          ],
          [
            0.55,
            0.25
          ],
          [
            0.55,
            1.8
          ],
          [
            0.2,
            1.8
          ],
          [
            0.2,
            0.25
          ]
        ]
      }
    ],
    "route": {
      "id": "main",
      "waypoints": [
        [
          0.0,
          0.0
        ],
        [
          10.0,
          0.0
        ]
      ],
      "total_length_m": 10.0,
      "v_move_mps": 4.5
    },
    "threats": [
      {
        "id": "F1_T1_L00",
        "polygon": [
          [
            2.5,
            -1.8
          ],
          [
            3.0,
            -1.8
          ],
          [
            3.0,
            -1.3
          ],
          [
            2.5,
            -1.3
          ],
          [
            2.5,
            -1.8
          ]
        ],
        "anchor": [
          2.75,
          -1.55
        ],
        "due_window_s": 0.62,
        "service_duration_s": 0.1
      },
      {
        "id": "F1_T2_R00",
        "polygon": [
          [
            2.2,
            2.1
          ],
          [
            2.7,
            2.1
          ],
          [
            2.7,
            2.6
          ],
          [
            2.2,
            2.6
          ],
          [
            2.2,
            2.1
          ]
        ],
        "anchor": [
          2.45,
          2.35
        ],
        "due_window_s": 0.62,
        "service_duration_s": 0.1
      }
    ],
    "ports": [
      {
        "id": "PORT_IN",
        "segment": [
          [
            0.0,
            -1.0
          ],
          [
            0.0,
            1.0
          ]
        ]
      },
      {
        "id": "PORT_OUT",
        "segment": [
          [
            10.0,
            -1.0
          ],
          [
            10.0,
            1.0
          ]
        ]
      }
    ]
  },
  "broken_scenario": {
    "tactical_margin_tics": -6,
    "tactical_margin_ms": -171.4,
    "l_star_tics": 6,
    "verdict": "unserviceable",
    "engine_survived": false,
    "death_tic": 25,
    "threat_jobs": [
      {
        "id": "F1_T1_L00",
        "reveal_tic": 0,
        "reveal_s": 0.0,
        "due_window_tics": 22,
        "due_window_s": 0.6286,
        "deadline_tic": 22,
        "deadline_s": 0.6286,
        "angle_deg": -29.41,
        "service_duration_tics": 4,
        "completion_tic": 13,
        "completion_s": 0.3714,
        "lateness_tics": -9
      },
      {
        "id": "F1_T2_R00",
        "reveal_tic": 3,
        "reveal_s": 0.0857,
        "due_window_tics": 22,
        "due_window_s": 0.6286,
        "deadline_tic": 25,
        "deadline_s": 0.7143,
        "angle_deg": 48.7,
        "service_duration_tics": 4,
        "completion_tic": 31,
        "completion_s": 0.8857,
        "lateness_tics": 6
      }
    ],
    "diagnostic": {
      "has_bottleneck": true,
      "critical_threat_id": "F1_T2_R00",
      "controlling_occluder_obstacle_id": 0,
      "controlling_occluder_segment": [
        [
          0.2,
          0.25
        ],
        [
          0.55,
          0.25
        ]
      ],
      "lateness_deficit_tics": 8,
      "lateness_deficit_ms": 228.6,
      "explanation": "Threat 'F1_T2_R00' unoccludes too early along obstacle #0. Player requires +8 tics (+228.6ms) of additional delay to service prior threats without deadline breach."
    },
    "events": [
      {
        "tic": 0,
        "time_s": 0.0,
        "type": "REVEAL",
        "threat_id": "F1_T1_L00",
        "description": "Threat F1_T1_L00 becomes actionable / revealed at tic 0 (0.00s)"
      },
      {
        "tic": 3,
        "time_s": 0.0857,
        "type": "REVEAL",
        "threat_id": "F1_T2_R00",
        "description": "Threat F1_T2_R00 becomes actionable / revealed at tic 3 (0.09s)"
      },
      {
        "tic": 8,
        "time_s": 0.2286,
        "type": "SERVICE_START",
        "threat_id": "F1_T1_L00",
        "description": "Commenced fire / servicing threat F1_T1_L00 at tic 8"
      },
      {
        "tic": 12,
        "time_s": 0.3429,
        "type": "SERVICE_COMPLETE",
        "threat_id": "F1_T1_L00",
        "description": "Threat F1_T1_L00 neutralized at tic 12 (0.34s)"
      },
      {
        "tic": 22,
        "time_s": 0.6286,
        "type": "DEADLINE",
        "threat_id": "F1_T1_L00",
        "description": "Threat F1_T1_L00 lethal deadline D_F1_T1_L00 at tic 22 (0.63s)"
      },
      {
        "tic": 25,
        "time_s": 0.7143,
        "type": "DEADLINE",
        "threat_id": "F1_T2_R00",
        "description": "Threat F1_T2_R00 lethal deadline D_F1_T2_R00 at tic 25 (0.71s)"
      },
      {
        "tic": 25,
        "time_s": 0.7143,
        "type": "BREACH",
        "threat_id": "F1_T2_R00",
        "description": "Lethal deadline breached by threat F1_T2_R00 at tic 25!"
      },
      {
        "tic": 25,
        "time_s": 0.7143,
        "type": "DEATH",
        "threat_id": "F1_T2_R00",
        "description": "Player defeated at tic 25 (0.71s) due to deadline breach."
      }
    ],
    "telemetry_frames": [
      {
        "tic": 0,
        "time_s": 0.0,
        "player_pos": [
          0.0,
          0.0
        ],
        "route_dist_m": 0.0,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 0.0,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 1,
        "time_s": 0.0286,
        "player_pos": [
          0.1286,
          0.0
        ],
        "route_dist_m": 0.1286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 0.0,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 2,
        "time_s": 0.0571,
        "player_pos": [
          0.2571,
          0.0
        ],
        "route_dist_m": 0.2571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 3,
        "time_s": 0.0857,
        "player_pos": [
          0.3857,
          0.0
        ],
        "route_dist_m": 0.3857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 4,
        "time_s": 0.1143,
        "player_pos": [
          0.5143,
          0.0
        ],
        "route_dist_m": 0.5143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 5,
        "time_s": 0.1429,
        "player_pos": [
          0.6429,
          0.0
        ],
        "route_dist_m": 0.6429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 6,
        "time_s": 0.1714,
        "player_pos": [
          0.7714,
          0.0
        ],
        "route_dist_m": 0.7714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 7,
        "time_s": 0.2,
        "player_pos": [
          0.9,
          0.0
        ],
        "route_dist_m": 0.9,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 8,
        "time_s": 0.2286,
        "player_pos": [
          1.0286,
          0.0
        ],
        "route_dist_m": 1.0286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 9,
        "time_s": 0.2571,
        "player_pos": [
          1.1571,
          0.0
        ],
        "route_dist_m": 1.1571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 10,
        "time_s": 0.2857,
        "player_pos": [
          1.2857,
          0.0
        ],
        "route_dist_m": 1.2857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 11,
        "time_s": 0.3143,
        "player_pos": [
          1.4143,
          0.0
        ],
        "route_dist_m": 1.4143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 12,
        "time_s": 0.3429,
        "player_pos": [
          1.5429,
          0.0
        ],
        "route_dist_m": 1.5429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "IDLE",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 13,
        "time_s": 0.3714,
        "player_pos": [
          1.6714,
          0.0
        ],
        "route_dist_m": 1.6714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 14,
        "time_s": 0.4,
        "player_pos": [
          1.8,
          0.0
        ],
        "route_dist_m": 1.8,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 15,
        "time_s": 0.4286,
        "player_pos": [
          1.9286,
          0.0
        ],
        "route_dist_m": 1.9286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 16,
        "time_s": 0.4571,
        "player_pos": [
          2.0571,
          0.0
        ],
        "route_dist_m": 2.0571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 17,
        "time_s": 0.4857,
        "player_pos": [
          2.1857,
          0.0
        ],
        "route_dist_m": 2.1857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 18,
        "time_s": 0.5143,
        "player_pos": [
          2.3143,
          0.0
        ],
        "route_dist_m": 2.3143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 19,
        "time_s": 0.5429,
        "player_pos": [
          2.4429,
          0.0
        ],
        "route_dist_m": 2.4429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 20,
        "time_s": 0.5714,
        "player_pos": [
          2.5714,
          0.0
        ],
        "route_dist_m": 2.5714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 21,
        "time_s": 0.6,
        "player_pos": [
          2.7,
          0.0
        ],
        "route_dist_m": 2.7,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 22,
        "time_s": 0.6286,
        "player_pos": [
          2.8286,
          0.0
        ],
        "route_dist_m": 2.8286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 23,
        "time_s": 0.6571,
        "player_pos": [
          2.9571,
          0.0
        ],
        "route_dist_m": 2.9571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 24,
        "time_s": 0.6857,
        "player_pos": [
          3.0857,
          0.0
        ],
        "route_dist_m": 3.0857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 25,
        "time_s": 0.7143,
        "player_pos": [
          3.2143,
          0.0
        ],
        "route_dist_m": 3.2143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 26,
        "time_s": 0.7429,
        "player_pos": [
          3.3429,
          0.0
        ],
        "route_dist_m": 3.3429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 27,
        "time_s": 0.7714,
        "player_pos": [
          3.4714,
          0.0
        ],
        "route_dist_m": 3.4714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 28,
        "time_s": 0.8,
        "player_pos": [
          3.6,
          0.0
        ],
        "route_dist_m": 3.6,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 29,
        "time_s": 0.8286,
        "player_pos": [
          3.7286,
          0.0
        ],
        "route_dist_m": 3.7286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 30,
        "time_s": 0.8571,
        "player_pos": [
          3.8571,
          0.0
        ],
        "route_dist_m": 3.8571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 31,
        "time_s": 0.8857,
        "player_pos": [
          3.9857,
          0.0
        ],
        "route_dist_m": 3.9857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 32,
        "time_s": 0.9143,
        "player_pos": [
          4.1143,
          0.0
        ],
        "route_dist_m": 4.1143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 33,
        "time_s": 0.9429,
        "player_pos": [
          4.2429,
          0.0
        ],
        "route_dist_m": 4.2429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 34,
        "time_s": 0.9714,
        "player_pos": [
          4.3714,
          0.0
        ],
        "route_dist_m": 4.3714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 35,
        "time_s": 1.0,
        "player_pos": [
          4.5,
          0.0
        ],
        "route_dist_m": 4.5,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 36,
        "time_s": 1.0286,
        "player_pos": [
          4.6286,
          0.0
        ],
        "route_dist_m": 4.6286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 37,
        "time_s": 1.0571,
        "player_pos": [
          4.7571,
          0.0
        ],
        "route_dist_m": 4.7571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 38,
        "time_s": 1.0857,
        "player_pos": [
          4.8857,
          0.0
        ],
        "route_dist_m": 4.8857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 39,
        "time_s": 1.1143,
        "player_pos": [
          5.0143,
          0.0
        ],
        "route_dist_m": 5.0143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 40,
        "time_s": 1.1429,
        "player_pos": [
          5.1429,
          0.0
        ],
        "route_dist_m": 5.1429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 41,
        "time_s": 1.1714,
        "player_pos": [
          5.2714,
          0.0
        ],
        "route_dist_m": 5.2714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 42,
        "time_s": 1.2,
        "player_pos": [
          5.4,
          0.0
        ],
        "route_dist_m": 5.4,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 43,
        "time_s": 1.2286,
        "player_pos": [
          5.5286,
          0.0
        ],
        "route_dist_m": 5.5286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 44,
        "time_s": 1.2571,
        "player_pos": [
          5.6571,
          0.0
        ],
        "route_dist_m": 5.6571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 45,
        "time_s": 1.2857,
        "player_pos": [
          5.7857,
          0.0
        ],
        "route_dist_m": 5.7857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 46,
        "time_s": 1.3143,
        "player_pos": [
          5.9143,
          0.0
        ],
        "route_dist_m": 5.9143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 47,
        "time_s": 1.3429,
        "player_pos": [
          6.0429,
          0.0
        ],
        "route_dist_m": 6.0429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 48,
        "time_s": 1.3714,
        "player_pos": [
          6.1714,
          0.0
        ],
        "route_dist_m": 6.1714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 49,
        "time_s": 1.4,
        "player_pos": [
          6.3,
          0.0
        ],
        "route_dist_m": 6.3,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 50,
        "time_s": 1.4286,
        "player_pos": [
          6.4286,
          0.0
        ],
        "route_dist_m": 6.4286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 51,
        "time_s": 1.4571,
        "player_pos": [
          6.5571,
          0.0
        ],
        "route_dist_m": 6.5571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 52,
        "time_s": 1.4857,
        "player_pos": [
          6.6857,
          0.0
        ],
        "route_dist_m": 6.6857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 53,
        "time_s": 1.5143,
        "player_pos": [
          6.8143,
          0.0
        ],
        "route_dist_m": 6.8143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 54,
        "time_s": 1.5429,
        "player_pos": [
          6.9429,
          0.0
        ],
        "route_dist_m": 6.9429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 55,
        "time_s": 1.5714,
        "player_pos": [
          7.0714,
          0.0
        ],
        "route_dist_m": 7.0714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 56,
        "time_s": 1.6,
        "player_pos": [
          7.2,
          0.0
        ],
        "route_dist_m": 7.2,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 57,
        "time_s": 1.6286,
        "player_pos": [
          7.3286,
          0.0
        ],
        "route_dist_m": 7.3286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 58,
        "time_s": 1.6571,
        "player_pos": [
          7.4571,
          0.0
        ],
        "route_dist_m": 7.4571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 59,
        "time_s": 1.6857,
        "player_pos": [
          7.5857,
          0.0
        ],
        "route_dist_m": 7.5857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 60,
        "time_s": 1.7143,
        "player_pos": [
          7.7143,
          0.0
        ],
        "route_dist_m": 7.7143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 61,
        "time_s": 1.7429,
        "player_pos": [
          7.8429,
          0.0
        ],
        "route_dist_m": 7.8429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 62,
        "time_s": 1.7714,
        "player_pos": [
          7.9714,
          0.0
        ],
        "route_dist_m": 7.9714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 63,
        "time_s": 1.8,
        "player_pos": [
          8.1,
          0.0
        ],
        "route_dist_m": 8.1,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 64,
        "time_s": 1.8286,
        "player_pos": [
          8.2286,
          0.0
        ],
        "route_dist_m": 8.2286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 65,
        "time_s": 1.8571,
        "player_pos": [
          8.3571,
          0.0
        ],
        "route_dist_m": 8.3571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 66,
        "time_s": 1.8857,
        "player_pos": [
          8.4857,
          0.0
        ],
        "route_dist_m": 8.4857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 67,
        "time_s": 1.9143,
        "player_pos": [
          8.6143,
          0.0
        ],
        "route_dist_m": 8.6143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 68,
        "time_s": 1.9429,
        "player_pos": [
          8.7429,
          0.0
        ],
        "route_dist_m": 8.7429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 69,
        "time_s": 1.9714,
        "player_pos": [
          8.8714,
          0.0
        ],
        "route_dist_m": 8.8714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 70,
        "time_s": 2.0,
        "player_pos": [
          9.0,
          0.0
        ],
        "route_dist_m": 9.0,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 71,
        "time_s": 2.0286,
        "player_pos": [
          9.1286,
          0.0
        ],
        "route_dist_m": 9.1286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 72,
        "time_s": 2.0571,
        "player_pos": [
          9.2571,
          0.0
        ],
        "route_dist_m": 9.2571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 73,
        "time_s": 2.0857,
        "player_pos": [
          9.3857,
          0.0
        ],
        "route_dist_m": 9.3857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 74,
        "time_s": 2.1143,
        "player_pos": [
          9.5143,
          0.0
        ],
        "route_dist_m": 9.5143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 75,
        "time_s": 2.1429,
        "player_pos": [
          9.6429,
          0.0
        ],
        "route_dist_m": 9.6429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 76,
        "time_s": 2.1714,
        "player_pos": [
          9.7714,
          0.0
        ],
        "route_dist_m": 9.7714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 77,
        "time_s": 2.2,
        "player_pos": [
          9.9,
          0.0
        ],
        "route_dist_m": 9.9,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 78,
        "time_s": 2.2286,
        "player_pos": [
          10.0,
          0.0
        ],
        "route_dist_m": 10.0,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 48.7,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "DEAD",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      }
    ]
  },
  "repair": {
    "operator": "obstacle_translation",
    "obstacle_id": 0,
    "displacement_m": 1.1,
    "direction": [
      1.0,
      0.0
    ],
    "edit_distance_m": 1.1,
    "description": "Shift obstacle #0 by 1.10m along vector (+1.00, +0.00) -> Margin M = 2 tics.",
    "preservation_validated": true
  },
  "repaired_scenario": {
    "tactical_margin_tics": 2,
    "tactical_margin_ms": 57.1,
    "l_star_tics": -2,
    "verdict": "serviceable",
    "engine_survived": true,
    "death_tic": null,
    "threat_jobs": [
      {
        "id": "F1_T1_L00",
        "reveal_tic": 0,
        "reveal_s": 0.0,
        "due_window_tics": 22,
        "due_window_s": 0.6286,
        "deadline_tic": 22,
        "deadline_s": 0.6286,
        "angle_deg": -29.41,
        "service_duration_tics": 4,
        "completion_tic": 13,
        "completion_s": 0.3714,
        "lateness_tics": -9
      },
      {
        "id": "F1_T2_R00",
        "reveal_tic": 13,
        "reveal_s": 0.3714,
        "due_window_tics": 22,
        "due_window_s": 0.6286,
        "deadline_tic": 35,
        "deadline_s": 1.0,
        "angle_deg": 71.67,
        "service_duration_tics": 4,
        "completion_tic": 33,
        "completion_s": 0.9429,
        "lateness_tics": -2
      }
    ],
    "diagnostic": {
      "has_bottleneck": false,
      "critical_threat_id": null,
      "controlling_occluder_obstacle_id": null,
      "controlling_occluder_segment": null,
      "lateness_deficit_tics": 0,
      "lateness_deficit_ms": 0.0,
      "explanation": "Obstacle #0 translated by 1.10m along (+1.10, +0.00). Second threat reveal is cleanly delayed, achieving Tactical Margin M = +2 tics."
    },
    "events": [
      {
        "tic": 0,
        "time_s": 0.0,
        "type": "REVEAL",
        "threat_id": "F1_T1_L00",
        "description": "Threat F1_T1_L00 becomes actionable / revealed at tic 0 (0.00s)"
      },
      {
        "tic": 8,
        "time_s": 0.2286,
        "type": "SERVICE_START",
        "threat_id": "F1_T1_L00",
        "description": "Commenced fire / servicing threat F1_T1_L00 at tic 8"
      },
      {
        "tic": 12,
        "time_s": 0.3429,
        "type": "SERVICE_COMPLETE",
        "threat_id": "F1_T1_L00",
        "description": "Threat F1_T1_L00 neutralized at tic 12 (0.34s)"
      },
      {
        "tic": 13,
        "time_s": 0.3714,
        "type": "REVEAL",
        "threat_id": "F1_T2_R00",
        "description": "Threat F1_T2_R00 becomes actionable / revealed at tic 13 (0.37s)"
      },
      {
        "tic": 22,
        "time_s": 0.6286,
        "type": "DEADLINE",
        "threat_id": "F1_T1_L00",
        "description": "Threat F1_T1_L00 lethal deadline D_F1_T1_L00 at tic 22 (0.63s)"
      },
      {
        "tic": 28,
        "time_s": 0.8,
        "type": "SERVICE_START",
        "threat_id": "F1_T2_R00",
        "description": "Commenced fire / servicing threat F1_T2_R00 at tic 28"
      },
      {
        "tic": 32,
        "time_s": 0.9143,
        "type": "SERVICE_COMPLETE",
        "threat_id": "F1_T2_R00",
        "description": "Threat F1_T2_R00 neutralized at tic 32 (0.91s)"
      },
      {
        "tic": 35,
        "time_s": 1.0,
        "type": "DEADLINE",
        "threat_id": "F1_T2_R00",
        "description": "Threat F1_T2_R00 lethal deadline D_F1_T2_R00 at tic 35 (1.00s)"
      }
    ],
    "telemetry_frames": [
      {
        "tic": 0,
        "time_s": 0.0,
        "player_pos": [
          0.0,
          0.0
        ],
        "route_dist_m": 0.0,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 0.0,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 1,
        "time_s": 0.0286,
        "player_pos": [
          0.1286,
          0.0
        ],
        "route_dist_m": 0.1286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 0.0,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 2,
        "time_s": 0.0571,
        "player_pos": [
          0.2571,
          0.0
        ],
        "route_dist_m": 0.2571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 3,
        "time_s": 0.0857,
        "player_pos": [
          0.3857,
          0.0
        ],
        "route_dist_m": 0.3857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 4,
        "time_s": 0.1143,
        "player_pos": [
          0.5143,
          0.0
        ],
        "route_dist_m": 0.5143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 5,
        "time_s": 0.1429,
        "player_pos": [
          0.6429,
          0.0
        ],
        "route_dist_m": 0.6429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 6,
        "time_s": 0.1714,
        "player_pos": [
          0.7714,
          0.0
        ],
        "route_dist_m": 0.7714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 7,
        "time_s": 0.2,
        "player_pos": [
          0.9,
          0.0
        ],
        "route_dist_m": 0.9,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 8,
        "time_s": 0.2286,
        "player_pos": [
          1.0286,
          0.0
        ],
        "route_dist_m": 1.0286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 9,
        "time_s": 0.2571,
        "player_pos": [
          1.1571,
          0.0
        ],
        "route_dist_m": 1.1571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 10,
        "time_s": 0.2857,
        "player_pos": [
          1.2857,
          0.0
        ],
        "route_dist_m": 1.2857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 11,
        "time_s": 0.3143,
        "player_pos": [
          1.4143,
          0.0
        ],
        "route_dist_m": 1.4143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": "F1_T1_L00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 12,
        "time_s": 0.3429,
        "player_pos": [
          1.5429,
          0.0
        ],
        "route_dist_m": 1.5429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00"
        ],
        "active_target_id": null,
        "controller_state": "IDLE",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": false
          }
        ]
      },
      {
        "tic": 13,
        "time_s": 0.3714,
        "player_pos": [
          1.6714,
          0.0
        ],
        "route_dist_m": 1.6714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 14,
        "time_s": 0.4,
        "player_pos": [
          1.8,
          0.0
        ],
        "route_dist_m": 1.8,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 15,
        "time_s": 0.4286,
        "player_pos": [
          1.9286,
          0.0
        ],
        "route_dist_m": 1.9286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 16,
        "time_s": 0.4571,
        "player_pos": [
          2.0571,
          0.0
        ],
        "route_dist_m": 2.0571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 17,
        "time_s": 0.4857,
        "player_pos": [
          2.1857,
          0.0
        ],
        "route_dist_m": 2.1857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 18,
        "time_s": 0.5143,
        "player_pos": [
          2.3143,
          0.0
        ],
        "route_dist_m": 2.3143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 19,
        "time_s": 0.5429,
        "player_pos": [
          2.4429,
          0.0
        ],
        "route_dist_m": 2.4429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 20,
        "time_s": 0.5714,
        "player_pos": [
          2.5714,
          0.0
        ],
        "route_dist_m": 2.5714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 21,
        "time_s": 0.6,
        "player_pos": [
          2.7,
          0.0
        ],
        "route_dist_m": 2.7,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": -29.41,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SLEWING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 22,
        "time_s": 0.6286,
        "player_pos": [
          2.8286,
          0.0
        ],
        "route_dist_m": 2.8286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 23,
        "time_s": 0.6571,
        "player_pos": [
          2.9571,
          0.0
        ],
        "route_dist_m": 2.9571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 24,
        "time_s": 0.6857,
        "player_pos": [
          3.0857,
          0.0
        ],
        "route_dist_m": 3.0857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 25,
        "time_s": 0.7143,
        "player_pos": [
          3.2143,
          0.0
        ],
        "route_dist_m": 3.2143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 26,
        "time_s": 0.7429,
        "player_pos": [
          3.3429,
          0.0
        ],
        "route_dist_m": 3.3429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 27,
        "time_s": 0.7714,
        "player_pos": [
          3.4714,
          0.0
        ],
        "route_dist_m": 3.4714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "ACQUIRING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 28,
        "time_s": 0.8,
        "player_pos": [
          3.6,
          0.0
        ],
        "route_dist_m": 3.6,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 29,
        "time_s": 0.8286,
        "player_pos": [
          3.7286,
          0.0
        ],
        "route_dist_m": 3.7286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 30,
        "time_s": 0.8571,
        "player_pos": [
          3.8571,
          0.0
        ],
        "route_dist_m": 3.8571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 31,
        "time_s": 0.8857,
        "player_pos": [
          3.9857,
          0.0
        ],
        "route_dist_m": 3.9857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": "F1_T2_R00",
        "controller_state": "SERVICING",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 32,
        "time_s": 0.9143,
        "player_pos": [
          4.1143,
          0.0
        ],
        "route_dist_m": 4.1143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 33,
        "time_s": 0.9429,
        "player_pos": [
          4.2429,
          0.0
        ],
        "route_dist_m": 4.2429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 34,
        "time_s": 0.9714,
        "player_pos": [
          4.3714,
          0.0
        ],
        "route_dist_m": 4.3714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 35,
        "time_s": 1.0,
        "player_pos": [
          4.5,
          0.0
        ],
        "route_dist_m": 4.5,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 36,
        "time_s": 1.0286,
        "player_pos": [
          4.6286,
          0.0
        ],
        "route_dist_m": 4.6286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 37,
        "time_s": 1.0571,
        "player_pos": [
          4.7571,
          0.0
        ],
        "route_dist_m": 4.7571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 38,
        "time_s": 1.0857,
        "player_pos": [
          4.8857,
          0.0
        ],
        "route_dist_m": 4.8857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 39,
        "time_s": 1.1143,
        "player_pos": [
          5.0143,
          0.0
        ],
        "route_dist_m": 5.0143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 40,
        "time_s": 1.1429,
        "player_pos": [
          5.1429,
          0.0
        ],
        "route_dist_m": 5.1429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 41,
        "time_s": 1.1714,
        "player_pos": [
          5.2714,
          0.0
        ],
        "route_dist_m": 5.2714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 42,
        "time_s": 1.2,
        "player_pos": [
          5.4,
          0.0
        ],
        "route_dist_m": 5.4,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 43,
        "time_s": 1.2286,
        "player_pos": [
          5.5286,
          0.0
        ],
        "route_dist_m": 5.5286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 44,
        "time_s": 1.2571,
        "player_pos": [
          5.6571,
          0.0
        ],
        "route_dist_m": 5.6571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 45,
        "time_s": 1.2857,
        "player_pos": [
          5.7857,
          0.0
        ],
        "route_dist_m": 5.7857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 46,
        "time_s": 1.3143,
        "player_pos": [
          5.9143,
          0.0
        ],
        "route_dist_m": 5.9143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 47,
        "time_s": 1.3429,
        "player_pos": [
          6.0429,
          0.0
        ],
        "route_dist_m": 6.0429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 48,
        "time_s": 1.3714,
        "player_pos": [
          6.1714,
          0.0
        ],
        "route_dist_m": 6.1714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 49,
        "time_s": 1.4,
        "player_pos": [
          6.3,
          0.0
        ],
        "route_dist_m": 6.3,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 50,
        "time_s": 1.4286,
        "player_pos": [
          6.4286,
          0.0
        ],
        "route_dist_m": 6.4286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 51,
        "time_s": 1.4571,
        "player_pos": [
          6.5571,
          0.0
        ],
        "route_dist_m": 6.5571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 52,
        "time_s": 1.4857,
        "player_pos": [
          6.6857,
          0.0
        ],
        "route_dist_m": 6.6857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 53,
        "time_s": 1.5143,
        "player_pos": [
          6.8143,
          0.0
        ],
        "route_dist_m": 6.8143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 54,
        "time_s": 1.5429,
        "player_pos": [
          6.9429,
          0.0
        ],
        "route_dist_m": 6.9429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 55,
        "time_s": 1.5714,
        "player_pos": [
          7.0714,
          0.0
        ],
        "route_dist_m": 7.0714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 56,
        "time_s": 1.6,
        "player_pos": [
          7.2,
          0.0
        ],
        "route_dist_m": 7.2,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 57,
        "time_s": 1.6286,
        "player_pos": [
          7.3286,
          0.0
        ],
        "route_dist_m": 7.3286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 58,
        "time_s": 1.6571,
        "player_pos": [
          7.4571,
          0.0
        ],
        "route_dist_m": 7.4571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 59,
        "time_s": 1.6857,
        "player_pos": [
          7.5857,
          0.0
        ],
        "route_dist_m": 7.5857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 60,
        "time_s": 1.7143,
        "player_pos": [
          7.7143,
          0.0
        ],
        "route_dist_m": 7.7143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 61,
        "time_s": 1.7429,
        "player_pos": [
          7.8429,
          0.0
        ],
        "route_dist_m": 7.8429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 62,
        "time_s": 1.7714,
        "player_pos": [
          7.9714,
          0.0
        ],
        "route_dist_m": 7.9714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 63,
        "time_s": 1.8,
        "player_pos": [
          8.1,
          0.0
        ],
        "route_dist_m": 8.1,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 64,
        "time_s": 1.8286,
        "player_pos": [
          8.2286,
          0.0
        ],
        "route_dist_m": 8.2286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 65,
        "time_s": 1.8571,
        "player_pos": [
          8.3571,
          0.0
        ],
        "route_dist_m": 8.3571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 66,
        "time_s": 1.8857,
        "player_pos": [
          8.4857,
          0.0
        ],
        "route_dist_m": 8.4857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 67,
        "time_s": 1.9143,
        "player_pos": [
          8.6143,
          0.0
        ],
        "route_dist_m": 8.6143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 68,
        "time_s": 1.9429,
        "player_pos": [
          8.7429,
          0.0
        ],
        "route_dist_m": 8.7429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 69,
        "time_s": 1.9714,
        "player_pos": [
          8.8714,
          0.0
        ],
        "route_dist_m": 8.8714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 70,
        "time_s": 2.0,
        "player_pos": [
          9.0,
          0.0
        ],
        "route_dist_m": 9.0,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 71,
        "time_s": 2.0286,
        "player_pos": [
          9.1286,
          0.0
        ],
        "route_dist_m": 9.1286,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 72,
        "time_s": 2.0571,
        "player_pos": [
          9.2571,
          0.0
        ],
        "route_dist_m": 9.2571,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 73,
        "time_s": 2.0857,
        "player_pos": [
          9.3857,
          0.0
        ],
        "route_dist_m": 9.3857,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 74,
        "time_s": 2.1143,
        "player_pos": [
          9.5143,
          0.0
        ],
        "route_dist_m": 9.5143,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 75,
        "time_s": 2.1429,
        "player_pos": [
          9.6429,
          0.0
        ],
        "route_dist_m": 9.6429,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 76,
        "time_s": 2.1714,
        "player_pos": [
          9.7714,
          0.0
        ],
        "route_dist_m": 9.7714,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 77,
        "time_s": 2.2,
        "player_pos": [
          9.9,
          0.0
        ],
        "route_dist_m": 9.9,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      },
      {
        "tic": 78,
        "time_s": 2.2286,
        "player_pos": [
          10.0,
          0.0
        ],
        "route_dist_m": 10.0,
        "forward_heading_deg": 0.0,
        "reticle_heading_deg": 71.67,
        "visible_threat_ids": [
          "F1_T1_L00",
          "F1_T2_R00"
        ],
        "active_target_id": null,
        "controller_state": "CLEARED",
        "los_rays": [
          {
            "threat_id": "F1_T1_L00",
            "target_pos": [
              2.75,
              -1.55
            ],
            "is_visible": true
          },
          {
            "threat_id": "F1_T2_R00",
            "target_pos": [
              2.45,
              2.35
            ],
            "is_visible": true
          }
        ]
      }
    ]
  },
  "external_engine_bridge": {
    "broken_engine_survived": false,
    "repaired_engine_survived": true,
    "delta_export_tics": 0,
    "delta_execution_tics": 0,
    "delta_total_tics": 0,
    "transfer_efficiency": 1.0
  }
};
