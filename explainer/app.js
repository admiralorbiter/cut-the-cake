// =============================================================================
// Tactical Clearability Interactive Visual Explainer (Canonical Discrete Solver)
// =============================================================================

const CANONICAL_DATA = {
  "params": {
    "ticrate_hz": 35,
    "tic_duration_ms": 28.5714,
    "max_aim_deg_per_tic": 10.2857,
    "acquisition_tics": 6,
    "acquisition_ms": 171.4,
    "service_tics": 4,
    "service_ms": 114.3
  },
  "stimuli": [
    {
      "id": "STIM_01_K0_ImpossibleAmbush",
      "name": "STIM 01 K0 ImpossibleAmbush",
      "classification": "Structurally Overloaded",
      "m_reveal_tics": -3,
      "m_preaim_tics": -3,
      "delta_m_knowledge_tics": 0,
      "l_star_source_tics": null,
      "l_star_source_ms": null,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 71.6,
          "reveal_tic": 0,
          "deadline_tic": 14,
          "due_window_tics": 14,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": 33.2,
          "reveal_tic": 18,
          "deadline_tic": 32,
          "due_window_tics": 14,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              2.0,
              -0.2
            ],
            [
              2.3,
              -0.2
            ],
            [
              2.3,
              2.0
            ],
            [
              2.0,
              2.0
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_02_K0_GenerousCorridor",
      "name": "STIM 02 K0 GenerousCorridor",
      "classification": "Blind-Clearable",
      "m_reveal_tics": 13,
      "m_preaim_tics": 13,
      "delta_m_knowledge_tics": 0,
      "l_star_source_tics": 0,
      "l_star_source_ms": 0.0,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 13,
          "tactical_margin_ms": 371.4,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 71.6,
          "reveal_tic": 0,
          "deadline_tic": 30,
          "due_window_tics": 30,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": 31.6,
          "reveal_tic": 17,
          "deadline_tic": 47,
          "due_window_tics": 30,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              1.8,
              -0.2
            ],
            [
              2.1,
              -0.2
            ],
            [
              2.1,
              1.8
            ],
            [
              1.8,
              1.8
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_03_K0_LethalCrossfire",
      "name": "STIM 03 K0 LethalCrossfire",
      "classification": "Structurally Overloaded",
      "m_reveal_tics": -28,
      "m_preaim_tics": -20,
      "delta_m_knowledge_tics": 8,
      "l_star_source_tics": null,
      "l_star_source_ms": null,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -28,
          "tactical_margin_ms": -800.0,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -27,
          "tactical_margin_ms": -771.4,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -26,
          "tactical_margin_ms": -742.9,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -25,
          "tactical_margin_ms": -714.3,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": -24,
          "tactical_margin_ms": -685.7,
          "is_feasible": false
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": -23,
          "tactical_margin_ms": -657.1,
          "is_feasible": false
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": -22,
          "tactical_margin_ms": -628.6,
          "is_feasible": false
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": -21,
          "tactical_margin_ms": -600.0,
          "is_feasible": false
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": -20,
          "tactical_margin_ms": -571.4,
          "is_feasible": false
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": -20,
          "tactical_margin_ms": -571.4,
          "is_feasible": false
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": -20,
          "tactical_margin_ms": -571.4,
          "is_feasible": false
        }
      ],
      "threats": [
        {
          "id": "T1_L",
          "angle_deg": 78.5,
          "reveal_tic": 17,
          "deadline_tic": 33,
          "due_window_tics": 16,
          "service_duration_tics": 4
        },
        {
          "id": "T2_R",
          "angle_deg": -78.5,
          "reveal_tic": 17,
          "deadline_tic": 33,
          "due_window_tics": 16,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              2.0,
              0.6
            ],
            [
              2.3,
              0.6
            ],
            [
              2.3,
              2.5
            ],
            [
              2.0,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              2.0,
              -2.5
            ],
            [
              2.3,
              -2.5
            ],
            [
              2.3,
              -0.6
            ],
            [
              2.0,
              -0.6
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_04_K0_NarrowCrossfire",
      "name": "STIM 04 K0 NarrowCrossfire",
      "classification": "Structurally Overloaded",
      "m_reveal_tics": -7,
      "m_preaim_tics": -7,
      "delta_m_knowledge_tics": 0,
      "l_star_source_tics": null,
      "l_star_source_ms": null,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": -7,
          "tactical_margin_ms": -200.0,
          "is_feasible": false
        }
      ],
      "threats": [
        {
          "id": "T1_L",
          "angle_deg": 9.0,
          "reveal_tic": 0,
          "deadline_tic": 16,
          "due_window_tics": 16,
          "service_duration_tics": 4
        },
        {
          "id": "T2_R",
          "angle_deg": -9.0,
          "reveal_tic": 0,
          "deadline_tic": 16,
          "due_window_tics": 16,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              2.0,
              0.6
            ],
            [
              2.3,
              0.6
            ],
            [
              2.3,
              2.5
            ],
            [
              2.0,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              2.0,
              -2.5
            ],
            [
              2.3,
              -2.5
            ],
            [
              2.3,
              -0.6
            ],
            [
              2.0,
              -0.6
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_05_K2_CornerBoundary",
      "name": "STIM 05 K2 CornerBoundary",
      "classification": "Blind-Clearable",
      "m_reveal_tics": 3,
      "m_preaim_tics": 3,
      "delta_m_knowledge_tics": 0,
      "l_star_source_tics": 0,
      "l_star_source_ms": 0.0,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 71.6,
          "reveal_tic": 0,
          "deadline_tic": 20,
          "due_window_tics": 20,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": 28.7,
          "reveal_tic": 15,
          "deadline_tic": 35,
          "due_window_tics": 20,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              1.5,
              -0.2
            ],
            [
              1.8,
              -0.2
            ],
            [
              1.8,
              1.8
            ],
            [
              1.5,
              1.8
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_06_K3_ModestPivot",
      "name": "STIM 06 K3 ModestPivot",
      "classification": "Knowledge-Rescuable",
      "m_reveal_tics": -5,
      "m_preaim_tics": 2,
      "delta_m_knowledge_tics": 7,
      "l_star_source_tics": 5,
      "l_star_source_ms": 142.9,
      "l_star_engine_model_tics": 4,
      "l_star_engine_model_ms": 114.3,
      "l_star_survival_tics": 4,
      "l_star_survival_ms": 114.3,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -5,
          "tactical_margin_ms": -142.9,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -4,
          "tactical_margin_ms": -114.3,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -2,
          "tactical_margin_ms": -57.1,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": -1,
          "tactical_margin_ms": -28.6,
          "is_feasible": false
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 0,
          "tactical_margin_ms": 0.0,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 64.1,
          "reveal_tic": 13,
          "deadline_tic": 37,
          "due_window_tics": 24,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": -61.5,
          "reveal_tic": 24,
          "deadline_tic": 48,
          "due_window_tics": 24,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              1.5,
              0.4
            ],
            [
              1.8,
              0.4
            ],
            [
              1.8,
              2.5
            ],
            [
              1.5,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              3.0,
              -2.5
            ],
            [
              3.3,
              -2.5
            ],
            [
              3.3,
              -0.4
            ],
            [
              3.0,
              -0.4
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_07_K4_FeasibleEnhancement",
      "name": "STIM 07 K4 FeasibleEnhancement",
      "classification": "Knowledge-Rescuable",
      "m_reveal_tics": -4,
      "m_preaim_tics": 3,
      "delta_m_knowledge_tics": 7,
      "l_star_source_tics": 4,
      "l_star_source_ms": 114.3,
      "l_star_engine_model_tics": 3,
      "l_star_engine_model_ms": 85.7,
      "l_star_survival_tics": 3,
      "l_star_survival_ms": 85.7,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -4,
          "tactical_margin_ms": -114.3,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -2,
          "tactical_margin_ms": -57.1,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -1,
          "tactical_margin_ms": -28.6,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": 0,
          "tactical_margin_ms": 0.0,
          "is_feasible": true
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 64.1,
          "reveal_tic": 13,
          "deadline_tic": 34,
          "due_window_tics": 21,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": -61.9,
          "reveal_tic": 28,
          "deadline_tic": 49,
          "due_window_tics": 21,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              1.5,
              0.4
            ],
            [
              1.8,
              0.4
            ],
            [
              1.8,
              2.5
            ],
            [
              1.5,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              3.5,
              -2.5
            ],
            [
              3.8,
              -2.5
            ],
            [
              3.8,
              -0.4
            ],
            [
              3.5,
              -0.4
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_08_K5_SweepArcPivot",
      "name": "STIM 08 K5 SweepArcPivot",
      "classification": "Blind-Clearable",
      "m_reveal_tics": 2,
      "m_preaim_tics": 10,
      "delta_m_knowledge_tics": 8,
      "l_star_source_tics": 0,
      "l_star_source_ms": 0.0,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": 4,
          "tactical_margin_ms": 114.3,
          "is_feasible": true
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": 5,
          "tactical_margin_ms": 142.9,
          "is_feasible": true
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": 6,
          "tactical_margin_ms": 171.4,
          "is_feasible": true
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 7,
          "tactical_margin_ms": 200.0,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 8,
          "tactical_margin_ms": 228.6,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 9,
          "tactical_margin_ms": 257.1,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 10,
          "tactical_margin_ms": 285.7,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 10,
          "tactical_margin_ms": 285.7,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 10,
          "tactical_margin_ms": 285.7,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 74.1,
          "reveal_tic": 14,
          "deadline_tic": 34,
          "due_window_tics": 20,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": 75.7,
          "reveal_tic": 26,
          "deadline_tic": 46,
          "due_window_tics": 20,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              1.5,
              0.2
            ],
            [
              1.8,
              0.2
            ],
            [
              1.8,
              2.5
            ],
            [
              1.5,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              3.0,
              0.2
            ],
            [
              3.3,
              0.2
            ],
            [
              3.3,
              2.5
            ],
            [
              3.0,
              2.5
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_09_K6_AperturePivot",
      "name": "STIM 09 K6 AperturePivot",
      "classification": "Knowledge-Rescuable",
      "m_reveal_tics": -4,
      "m_preaim_tics": 2,
      "delta_m_knowledge_tics": 6,
      "l_star_source_tics": 4,
      "l_star_source_ms": 114.3,
      "l_star_engine_model_tics": 3,
      "l_star_engine_model_ms": 85.7,
      "l_star_survival_tics": 5,
      "l_star_survival_ms": 142.9,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -4,
          "tactical_margin_ms": -114.3,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -2,
          "tactical_margin_ms": -57.1,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -1,
          "tactical_margin_ms": -28.6,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": 0,
          "tactical_margin_ms": 0.0,
          "is_feasible": true
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "F3_T1",
          "angle_deg": 57.8,
          "reveal_tic": 15,
          "deadline_tic": 47,
          "due_window_tics": 32,
          "service_duration_tics": 4
        },
        {
          "id": "F3_T2",
          "angle_deg": -53.5,
          "reveal_tic": 26,
          "deadline_tic": 58,
          "due_window_tics": 32,
          "service_duration_tics": 4
        },
        {
          "id": "F3_T3",
          "angle_deg": 53.8,
          "reveal_tic": 37,
          "deadline_tic": 69,
          "due_window_tics": 32,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              1.8,
              0.2
            ],
            [
              2.0,
              0.2
            ],
            [
              2.0,
              2.5
            ],
            [
              1.8,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              3.2,
              -2.5
            ],
            [
              3.4,
              -2.5
            ],
            [
              3.4,
              -0.2
            ],
            [
              3.2,
              -0.2
            ]
          ]
        },
        {
          "pts": [
            [
              4.6,
              0.2
            ],
            [
              4.8,
              0.2
            ],
            [
              4.8,
              2.5
            ],
            [
              4.6,
              2.5
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_10_K6_AlternatingFlankPivot",
      "name": "STIM 10 K6 AlternatingFlankPivot",
      "classification": "Blind-Clearable",
      "m_reveal_tics": 1,
      "m_preaim_tics": 7,
      "delta_m_knowledge_tics": 6,
      "l_star_source_tics": 0,
      "l_star_source_ms": 0.0,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": 2,
          "tactical_margin_ms": 57.1,
          "is_feasible": true
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": 3,
          "tactical_margin_ms": 85.7,
          "is_feasible": true
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": 4,
          "tactical_margin_ms": 114.3,
          "is_feasible": true
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": 5,
          "tactical_margin_ms": 142.9,
          "is_feasible": true
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": 6,
          "tactical_margin_ms": 171.4,
          "is_feasible": true
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 7,
          "tactical_margin_ms": 200.0,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 7,
          "tactical_margin_ms": 200.0,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 7,
          "tactical_margin_ms": 200.0,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 7,
          "tactical_margin_ms": 200.0,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 7,
          "tactical_margin_ms": 200.0,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "F4_T1_L",
          "angle_deg": 59.8,
          "reveal_tic": 17,
          "deadline_tic": 47,
          "due_window_tics": 30,
          "service_duration_tics": 4
        },
        {
          "id": "F4_T2_R",
          "angle_deg": -61.6,
          "reveal_tic": 33,
          "deadline_tic": 63,
          "due_window_tics": 30,
          "service_duration_tics": 4
        },
        {
          "id": "F4_T3_L",
          "angle_deg": 63.4,
          "reveal_tic": 49,
          "deadline_tic": 79,
          "due_window_tics": 30,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              2.0,
              0.2
            ],
            [
              2.3,
              0.2
            ],
            [
              2.3,
              2.2
            ],
            [
              2.0,
              2.2
            ]
          ]
        },
        {
          "pts": [
            [
              4.0,
              -2.2
            ],
            [
              4.3,
              -2.2
            ],
            [
              4.3,
              -0.2
            ],
            [
              4.0,
              -0.2
            ]
          ]
        },
        {
          "pts": [
            [
              6.0,
              0.2
            ],
            [
              6.3,
              0.2
            ],
            [
              6.3,
              2.2
            ],
            [
              6.0,
              2.2
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_11_K7_ZigzagPivot",
      "name": "STIM 11 K7 ZigzagPivot",
      "classification": "Knowledge-Rescuable",
      "m_reveal_tics": -6,
      "m_preaim_tics": 1,
      "delta_m_knowledge_tics": 7,
      "l_star_source_tics": 6,
      "l_star_source_ms": 171.4,
      "l_star_engine_model_tics": 4,
      "l_star_engine_model_ms": 114.3,
      "l_star_survival_tics": 5,
      "l_star_survival_ms": 142.9,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -6,
          "tactical_margin_ms": -171.4,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -5,
          "tactical_margin_ms": -142.9,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -4,
          "tactical_margin_ms": -114.3,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -3,
          "tactical_margin_ms": -85.7,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": -2,
          "tactical_margin_ms": -57.1,
          "is_feasible": false
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": -1,
          "tactical_margin_ms": -28.6,
          "is_feasible": false
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": 0,
          "tactical_margin_ms": 0.0,
          "is_feasible": true
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": 1,
          "tactical_margin_ms": 28.6,
          "is_feasible": true
        }
      ],
      "threats": [
        {
          "id": "T1",
          "angle_deg": 66.3,
          "reveal_tic": 17,
          "deadline_tic": 52,
          "due_window_tics": 35,
          "service_duration_tics": 4
        },
        {
          "id": "T2",
          "angle_deg": -67.8,
          "reveal_tic": 29,
          "deadline_tic": 64,
          "due_window_tics": 35,
          "service_duration_tics": 4
        },
        {
          "id": "T3",
          "angle_deg": 69.3,
          "reveal_tic": 41,
          "deadline_tic": 76,
          "due_window_tics": 35,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              2.0,
              0.3
            ],
            [
              2.3,
              0.3
            ],
            [
              2.3,
              2.5
            ],
            [
              2.0,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              3.5,
              -2.5
            ],
            [
              3.8,
              -2.5
            ],
            [
              3.8,
              -0.3
            ],
            [
              3.5,
              -0.3
            ]
          ]
        },
        {
          "pts": [
            [
              5.0,
              0.3
            ],
            [
              5.3,
              0.3
            ],
            [
              5.3,
              2.5
            ],
            [
              5.0,
              2.5
            ]
          ]
        }
      ]
    },
    {
      "id": "STIM_12_K8_SevereKnowledgeGain",
      "name": "STIM 12 K8 SevereKnowledgeGain",
      "classification": "Structurally Overloaded",
      "m_reveal_tics": -10,
      "m_preaim_tics": -10,
      "delta_m_knowledge_tics": 0,
      "l_star_source_tics": null,
      "l_star_source_ms": null,
      "l_star_engine_model_tics": null,
      "l_star_engine_model_ms": null,
      "l_star_survival_tics": null,
      "l_star_survival_ms": null,
      "curve": [
        {
          "lead_tics": 0,
          "lead_ms": 0.0,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 1,
          "lead_ms": 28.6,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 2,
          "lead_ms": 57.1,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 3,
          "lead_ms": 85.7,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 4,
          "lead_ms": 114.3,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 5,
          "lead_ms": 142.9,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 6,
          "lead_ms": 171.4,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 7,
          "lead_ms": 200.0,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 8,
          "lead_ms": 228.6,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 9,
          "lead_ms": 257.1,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        },
        {
          "lead_tics": 10,
          "lead_ms": 285.7,
          "tactical_margin_tics": -10,
          "tactical_margin_ms": -285.7,
          "is_feasible": false
        }
      ],
      "threats": [
        {
          "id": "T1_L",
          "angle_deg": 9.0,
          "reveal_tic": 0,
          "deadline_tic": 13,
          "due_window_tics": 13,
          "service_duration_tics": 4
        },
        {
          "id": "T2_R",
          "angle_deg": -9.0,
          "reveal_tic": 0,
          "deadline_tic": 13,
          "due_window_tics": 13,
          "service_duration_tics": 4
        }
      ],
      "obstacles": [
        {
          "pts": [
            [
              2.0,
              0.6
            ],
            [
              2.3,
              0.6
            ],
            [
              2.3,
              2.5
            ],
            [
              2.0,
              2.5
            ]
          ]
        },
        {
          "pts": [
            [
              2.0,
              -2.5
            ],
            [
              2.3,
              -2.5
            ],
            [
              2.3,
              -0.6
            ],
            [
              2.0,
              -0.6
            ]
          ]
        }
      ]
    }
  ]
};
const ATLAS_FIXTURES = {
  "meta": {
    "version": "v2.0-provenance-grounded",
    "description": "Tactical Readability Atlas grounded in compiler fixtures, canonical stimuli, and design archetypes.",
    "ticrate_hz": 35,
    "tic_duration_ms": 28.571428571428573
  },
  "f05": {
    "direct_center": {
      "is_feasible": false,
      "tactical_margin_tics": -13,
      "tactical_margin_ms": -371.4,
      "k_static": 2,
      "threats": [
        {
          "id": "F05_T1",
          "angle": -20.6,
          "reveal_tic": 0,
          "deadline_tic": 11
        },
        {
          "id": "F05_T2",
          "angle": 7.1,
          "reveal_tic": 0,
          "deadline_tic": 11
        }
      ]
    },
    "upper_flank": {
      "is_feasible": true,
      "tactical_margin_tics": 0,
      "tactical_margin_ms": 0.0,
      "k_static": 0,
      "threats": []
    }
  },
  "f06": {
    "0.70": {
      "wall_x_m": 0.7,
      "is_feasible": false,
      "status": "VALID_INFEASIBLE",
      "reveal_gap_ms": 211.1,
      "reveal_gap_tics": 7,
      "tactical_margin_tics": -2,
      "tactical_margin_ms": -57.1,
      "l_star_ms": 114,
      "r1_tic": 0,
      "r2_tic": 7
    },
    "0.75": {
      "wall_x_m": 0.75,
      "is_feasible": false,
      "status": "VALID_INFEASIBLE",
      "reveal_gap_ms": 222.2,
      "reveal_gap_tics": 8,
      "tactical_margin_tics": -2,
      "tactical_margin_ms": -57.1,
      "l_star_ms": 114,
      "r1_tic": 0,
      "r2_tic": 8
    },
    "0.80": {
      "wall_x_m": 0.8,
      "is_feasible": false,
      "status": "VALID_INFEASIBLE",
      "reveal_gap_ms": 233.3,
      "reveal_gap_tics": 8,
      "tactical_margin_tics": -2,
      "tactical_margin_ms": -57.1,
      "l_star_ms": 114,
      "r1_tic": 0,
      "r2_tic": 8
    },
    "0.85": {
      "wall_x_m": 0.85,
      "is_feasible": false,
      "status": "VALID_INFEASIBLE",
      "reveal_gap_ms": 244.4,
      "reveal_gap_tics": 9,
      "tactical_margin_tics": -1,
      "tactical_margin_ms": -28.6,
      "l_star_ms": 57,
      "r1_tic": 0,
      "r2_tic": 9
    },
    "0.90": {
      "wall_x_m": 0.9,
      "is_feasible": true,
      "status": "VALID_FEASIBLE",
      "reveal_gap_ms": 255.6,
      "reveal_gap_tics": 9,
      "tactical_margin_tics": 1,
      "tactical_margin_ms": 28.6,
      "l_star_ms": 0,
      "r1_tic": 0,
      "r2_tic": 9
    },
    "0.95": {
      "wall_x_m": 0.95,
      "is_feasible": true,
      "status": "VALID_FEASIBLE",
      "reveal_gap_ms": 266.7,
      "reveal_gap_tics": 9,
      "tactical_margin_tics": 1,
      "tactical_margin_ms": 28.6,
      "l_star_ms": 0,
      "r1_tic": 0,
      "r2_tic": 9
    },
    "1.00": {
      "wall_x_m": 1.0,
      "is_feasible": true,
      "status": "VALID_FEASIBLE",
      "reveal_gap_ms": 277.8,
      "reveal_gap_tics": 10,
      "tactical_margin_tics": 1,
      "tactical_margin_ms": 28.6,
      "l_star_ms": 0,
      "r1_tic": 0,
      "r2_tic": 10
    }
  }
};

const TIC_MS = CANONICAL_DATA.params.tic_duration_ms; // 28.5714 ms
const TICRATE_HZ = CANONICAL_DATA.params.ticrate_hz;  // 35 Hz
const MAX_AIM_DEG_PER_TIC = CANONICAL_DATA.params.max_aim_deg_per_tic; // 10.2857 deg/tic
const ACQUISITION_TICS = CANONICAL_DATA.params.acquisition_tics;       // 6 tics (171.4 ms)
const SERVICE_TICS = CANONICAL_DATA.params.service_tics;               // 4 tics (114.3 ms)

const STIMULI_MAP = {};
CANONICAL_DATA.stimuli.forEach(s => {
  STIMULI_MAP[s.id] = s;
  const shortId = s.id.split("_").slice(0, 2).join("_");
  STIMULI_MAP[shortId] = s;
});

// =============================================================================
// SCHEMATIC TWO ROOMS DATA
// =============================================================================

const TWO_ROOMS_DATA = {
  roomA: {
    id: "roomA",
    title: "Room A: Low Count, Unserviceable",
    kStatic: 2,
    marginTics: -1,
    marginMs: -28.6,
    isClearable: false,
    threats: [
      { id: "T1", name: "Left Flank", x: 380, y: 55, angle: 65, revealDist: 3.0, deadlineS: 0.85 },
      { id: "T2", name: "Right Flank", x: 380, y: 195, angle: -85, revealDist: 3.0, deadlineS: 0.85 }
    ],
    obstacles: [
      { x: 180, y: 0, w: 35, h: 80, label: "TOP DOORJAMB", type: "concrete" },
      { x: 180, y: 160, w: 35, h: 80, label: "BOTTOM DOORJAMB", type: "concrete" }
    ],
    route: [{x: 40, y: 120}, {x: 420, y: 120}]
  },
  roomB: {
    id: "roomB",
    title: "Room B: Higher Count, Serviceable",
    kStatic: 3,
    marginTics: +23,
    marginMs: +657.1,
    isClearable: true,
    threats: [
      { id: "T1", name: "Corner Pocket", x: 215, y: 50, angle: 35, revealDist: 1.0, deadlineS: 1.4 },
      { id: "T2", name: "Chicane Alley", x: 315, y: 135, angle: 0, revealDist: 2.8, deadlineS: 2.2 },
      { id: "T3", name: "Deep Pocket", x: 405, y: 190, angle: -35, revealDist: 4.4, deadlineS: 3.0 }
    ],
    obstacles: [
      { x: 120, y: 0, w: 30, h: 80, label: "BLAST WALL", type: "concrete" },
      { x: 215, y: 135, w: 35, h: 105, label: "CONCRETE BARRICADE", type: "barrier" },
      { x: 320, y: 0, w: 30, h: 80, label: "COVER CRATES", type: "crate" }
    ],
    route: [
      {x: 40, y: 120},
      {x: 175, y: 120},
      {x: 235, y: 98},
      {x: 295, y: 98},
      {x: 355, y: 120},
      {x: 420, y: 120}
    ]
  }
};

// =============================================================================
// EXACT INTEGER-TIC SCHEDULING ENGINE
// =============================================================================

function angleDiff(a, b) {
  let d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

function solveDiscreteScheduleWithLead(threats, leadTics) {
  const n = threats.length;
  let bestLStar = 999999;
  let bestSchedule = null;

  const perms = n === 2 ? [[0, 1], [1, 0]] : (n === 1 ? [[0]] : [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]]);

  for (const p of perms) {
    let curTime = 0;
    let curAim = 0.0;
    let maxL = -999999;
    const timeline = [];

    for (const idx of p) {
      const t = threats[idx];
      const a_j = Math.max(0, t.reveal_tic - leadTics);
      const diff = angleDiff(curAim, t.angle_deg);
      const rotTics = diff > 1e-4 ? Math.ceil(diff / MAX_AIM_DEG_PER_TIC) : 0;

      const rotStart = Math.max(curTime, a_j);
      const rotFinish = rotStart + rotTics;
      const acqStart = Math.max(t.reveal_tic, rotFinish);
      const srvStart = acqStart + ACQUISITION_TICS;
      const compT = srvStart + SERVICE_TICS;
      const deadline = t.reveal_tic + t.due_window_tics;
      const lateness = compT - deadline;

      timeline.push({
        id: t.id,
        rotStart,
        rotFinish,
        acqStart,
        srvStart,
        compT,
        deadline,
        lateness,
        angle: t.angle_deg
      });

      maxL = Math.max(maxL, lateness);
      curTime = compT;
      curAim = t.angle_deg;
    }

    if (maxL < bestLStar) {
      bestLStar = maxL;
      bestSchedule = timeline;
    }
  }

  const marginTics = -bestLStar;
  const marginMs = marginTics * TIC_MS;
  return { lStarTics: bestLStar, marginTics, marginMs, schedule: bestSchedule };
}

// =============================================================================
// COMPONENT 1: TWO ROOMS ANIMATION & RENDERING
// =============================================================================

let twoRoomsProgress = 0.0;
let twoRoomsAnimId = null;

function initTwoRooms() {
  document.getElementById("btn-tworooms-play").addEventListener("click", playTwoRoomsAnim);
  document.getElementById("btn-tworooms-reset").addEventListener("click", resetTwoRoomsAnim);
  renderTwoRooms(0.0);
}

function renderTwoRooms(progress) {
  renderRoomSVG("svg-roomA", TWO_ROOMS_DATA.roomA, progress);
  renderRoomSVG("svg-roomB", TWO_ROOMS_DATA.roomB, progress);
  renderRoomTimeline("timeline-roomA", TWO_ROOMS_DATA.roomA, progress);
  renderRoomTimeline("timeline-roomB", TWO_ROOMS_DATA.roomB, progress);

  document.getElementById("hud-roomA").textContent = `Traversed: ${(progress * 6.0).toFixed(1)}m | Outcome: ${progress >= 0.95 ? "KILLED 💀" : "CLEARING"}`;
  document.getElementById("hud-roomB").textContent = `Traversed: ${(progress * 6.0).toFixed(1)}m | Outcome: ${progress >= 0.95 ? "SURVIVED ✓" : "CLEARING"}`;
}

function getPolylinePoint(pts, progress) {
  if (!pts || pts.length === 0) return { x: 0, y: 0 };
  if (pts.length === 1) return { x: pts[0].x, y: pts[0].y };
  
  const lens = [];
  let total = 0.0;
  for (let i = 0; i < pts.length - 1; i++) {
    const dx = pts[i + 1].x - pts[i].x;
    const dy = pts[i + 1].y - pts[i].y;
    const d = Math.hypot(dx, dy);
    lens.push(d);
    total += d;
  }

  const targetD = progress * total;
  let accum = 0.0;
  for (let i = 0; i < pts.length - 1; i++) {
    if (accum + lens[i] >= targetD) {
      const rem = targetD - accum;
      const r = lens[i] > 0 ? rem / lens[i] : 0;
      return {
        x: pts[i].x + (pts[i + 1].x - pts[i].x) * r,
        y: pts[i].y + (pts[i + 1].y - pts[i].y) * r
      };
    }
    accum += lens[i];
  }
  return { x: pts[pts.length - 1].x, y: pts[pts.length - 1].y };
}

function renderRoomSVG(svgId, data, progress) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  svg.innerHTML = "";

  // 1. Defs: Shadows, Tactical Grids & Patterns
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <pattern id="tac-grid-${svgId}" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(88, 166, 255, 0.05)" stroke-width="1"/>
    </pattern>
    <pattern id="hatch-concrete" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="10" stroke="rgba(88, 166, 255, 0.25)" stroke-width="2.5" />
    </pattern>
    <pattern id="hatch-crate" width="8" height="8" patternUnits="userSpaceOnUse">
      <rect width="8" height="8" fill="#1b222d" stroke="rgba(210, 153, 34, 0.3)" stroke-width="1"/>
      <line x1="0" y1="0" x2="8" y2="8" stroke="rgba(210, 153, 34, 0.2)" stroke-width="1"/>
    </pattern>
    <filter id="wall-drop-shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="3" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.6"/>
    </filter>
  `;
  svg.appendChild(defs);

  // 2. Room Outer Perimeter Wall & Floor Grid
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", 8); bg.setAttribute("y", 8);
  bg.setAttribute("width", 444); bg.setAttribute("height", 234);
  bg.setAttribute("fill", "#0a0e14"); bg.setAttribute("stroke", "#30363d"); bg.setAttribute("stroke-width", "2");
  bg.setAttribute("rx", 6);
  svg.appendChild(bg);

  const grid = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  grid.setAttribute("x", 8); grid.setAttribute("y", 8);
  grid.setAttribute("width", 444); grid.setAttribute("height", 234);
  grid.setAttribute("fill", `url(#tac-grid-${svgId})`);
  svg.appendChild(grid);

  // 3. Walkable Tactical Corridor Zone
  if (data.id === "roomB") {
    const zone = document.createElementNS("http://www.w3.org/2000/svg", "path");
    zone.setAttribute("d", "M 15 80 L 150 80 L 215 75 L 320 75 L 445 75 L 445 175 L 350 175 L 250 145 L 150 170 L 15 170 Z");
    zone.setAttribute("fill", "rgba(88, 166, 255, 0.03)");
    zone.setAttribute("stroke", "rgba(88, 166, 255, 0.12)");
    zone.setAttribute("stroke-dasharray", "3,3");
    svg.appendChild(zone);
  }

  // 4. Solid Obstacles with 3D Bevel, Hatching & Tactical Labels
  data.obstacles.forEach(o => {
    // Drop shadow base
    const base = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    base.setAttribute("x", o.x); base.setAttribute("y", o.y);
    base.setAttribute("width", o.w); base.setAttribute("height", o.h);
    base.setAttribute("fill", o.type === "crate" ? "url(#hatch-crate)" : "#161b22");
    base.setAttribute("filter", "url(#wall-drop-shadow)");
    base.setAttribute("stroke", o.type === "crate" ? "#d29922" : "#58a6ff");
    base.setAttribute("stroke-width", "1.5");
    base.setAttribute("rx", 3);
    svg.appendChild(base);

    // Inner concrete hatch texture
    if (o.type !== "crate") {
      const hatch = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      hatch.setAttribute("x", o.x + 2); hatch.setAttribute("y", o.y + 2);
      hatch.setAttribute("width", o.w - 4); hatch.setAttribute("height", o.h - 4);
      hatch.setAttribute("fill", "url(#hatch-concrete)");
      hatch.setAttribute("opacity", "0.45");
      svg.appendChild(hatch);
    }

    // Top edge 3D bevel cap (light reflection)
    const topBevel = document.createElementNS("http://www.w3.org/2000/svg", "line");
    topBevel.setAttribute("x1", o.x); topBevel.setAttribute("y1", o.y + 2);
    topBevel.setAttribute("x2", o.x + o.w); topBevel.setAttribute("y2", o.y + 2);
    topBevel.setAttribute("stroke", o.type === "crate" ? "rgba(255, 215, 0, 0.6)" : "rgba(136, 192, 255, 0.8)");
    topBevel.setAttribute("stroke-width", "2");
    svg.appendChild(topBevel);

    // Tactical label
    if (o.label) {
      const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
      const isVert = o.h > o.w * 1.8;
      if (isVert) {
        lbl.setAttribute("x", o.x + o.w / 2);
        lbl.setAttribute("y", o.y + o.h / 2);
        lbl.setAttribute("transform", `rotate(-90 ${o.x + o.w/2} ${o.y + o.h/2})`);
      } else {
        lbl.setAttribute("x", o.x + o.w / 2);
        lbl.setAttribute("y", o.y + o.h / 2 + 3);
      }
      lbl.setAttribute("fill", o.type === "crate" ? "#d29922" : "rgba(200, 225, 255, 0.7)");
      lbl.setAttribute("font-size", "7.5px");
      lbl.setAttribute("font-weight", "800");
      lbl.setAttribute("letter-spacing", "0.5px");
      lbl.setAttribute("text-anchor", "middle");
      lbl.textContent = o.label;
      svg.appendChild(lbl);
    }
  });

  // 5. Traversal Path Polyline (Weaves safely around cover)
  if (data.route && data.route.length >= 2) {
    const ptsStr = data.route.map(p => `${p.x},${p.y}`).join(" ");
    const rLine = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    rLine.setAttribute("points", ptsStr);
    rLine.setAttribute("fill", "none");
    rLine.setAttribute("stroke", "rgba(88, 166, 255, 0.35)");
    rLine.setAttribute("stroke-dasharray", "4,4");
    rLine.setAttribute("stroke-width", "2");
    svg.appendChild(rLine);
  }

  // 6. Current Player Coordinates along the non-intersecting polyline
  const pos = getPolylinePoint(data.route, progress);
  const px = pos.x;
  const py = pos.y;

  let currentAimAngle = 0.0;
  let activeTarget = null;
  if (data.id === "roomA") {
    if (progress < 0.45) {
      currentAimAngle = 0.0;
    } else if (progress < 0.75) {
      currentAimAngle = 65.0;
      activeTarget = "T1";
    } else {
      currentAimAngle = -85.0;
      activeTarget = "T2";
    }
  } else {
    if (progress < 0.35) {
      currentAimAngle = 35.0;
      activeTarget = "T1";
    } else if (progress < 0.70) {
      currentAimAngle = 0.0;
      activeTarget = "T2";
    } else {
      currentAimAngle = -35.0;
      activeTarget = "T3";
    }
  }

  const rad = currentAimAngle * Math.PI / 180;
  const fovHalfAngle = 30 * Math.PI / 180;
  const fovDist = 115;

  // 7. Player Vision Field of View (FOV) Cone
  const fovP1x = px + Math.cos(rad - fovHalfAngle) * fovDist;
  const fovP1y = py - Math.sin(rad - fovHalfAngle) * fovDist;
  const fovP2x = px + Math.cos(rad + fovHalfAngle) * fovDist;
  const fovP2y = py - Math.sin(rad + fovHalfAngle) * fovDist;

  const fovCone = document.createElementNS("http://www.w3.org/2000/svg", "path");
  fovCone.setAttribute("d", `M ${px} ${py} L ${fovP1x} ${fovP1y} A ${fovDist} ${fovDist} 0 0 0 ${fovP2x} ${fovP2y} Z`);
  fovCone.setAttribute("fill", "rgba(88, 166, 255, 0.08)");
  fovCone.setAttribute("stroke", "rgba(88, 166, 255, 0.25)");
  fovCone.setAttribute("stroke-width", "1");
  svg.appendChild(fovCone);

  // 8. Obstacle Occlusion Grazing Lines
  data.obstacles.forEach(o => {
    if (o.y === 0) {
      const cornerX = o.x + o.w;
      const cornerY = o.h;
      const thresh = document.createElementNS("http://www.w3.org/2000/svg", "line");
      thresh.setAttribute("x1", cornerX); thresh.setAttribute("y1", cornerY);
      thresh.setAttribute("x2", cornerX + 100); thresh.setAttribute("y2", cornerY + 50);
      thresh.setAttribute("stroke", "rgba(255, 255, 255, 0.12)");
      thresh.setAttribute("stroke-dasharray", "3,3");
      svg.appendChild(thresh);
    }
  });

  // 9. Threats & Active Line-of-Sight Rays
  data.threats.forEach((t, idx) => {
    const isRevealed = progress >= (t.revealDist / 6.0);
    const isTargeted = activeTarget === t.id;

    if (isRevealed) {
      const ray = document.createElementNS("http://www.w3.org/2000/svg", "line");
      ray.setAttribute("x1", px); ray.setAttribute("y1", py);
      ray.setAttribute("x2", t.x); ray.setAttribute("y2", t.y);
      
      const isBreach = idx === 1 && !data.isClearable && progress >= 0.7;
      ray.setAttribute("stroke", isBreach ? "#f85149" : (isTargeted ? "#3fb950" : "rgba(88, 166, 255, 0.6)"));
      ray.setAttribute("stroke-width", isTargeted ? "2.5" : "1.5");
      if (!isTargeted) ray.setAttribute("stroke-dasharray", "4,2");
      svg.appendChild(ray);

      const midX = (px + t.x) / 2;
      const midY = (py + t.y) / 2;
      const rayTag = document.createElementNS("http://www.w3.org/2000/svg", "text");
      rayTag.setAttribute("x", midX); rayTag.setAttribute("y", midY - 4);
      rayTag.setAttribute("fill", isBreach ? "#f85149" : "#58a6ff");
      rayTag.setAttribute("font-size", "9px");
      rayTag.setAttribute("text-anchor", "middle");
      rayTag.textContent = isBreach ? "BREACH ✗" : "LOS ACTIVE";
      svg.appendChild(rayTag);
    }

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", t.x - 10); rect.setAttribute("y", t.y - 10);
    rect.setAttribute("width", 20); rect.setAttribute("height", 20);
    rect.setAttribute("fill", isRevealed ? (idx === 1 && !data.isClearable && progress >= 0.7 ? "#f85149" : (isTargeted ? "#3fb950" : "#d29922")) : "#21262d");
    rect.setAttribute("stroke", isRevealed ? "#fff" : "#484f58");
    rect.setAttribute("stroke-width", isTargeted ? "2" : "1");
    rect.setAttribute("rx", 4);
    svg.appendChild(rect);

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", t.x); txt.setAttribute("y", t.y + 4);
    txt.setAttribute("fill", "#fff"); txt.setAttribute("font-size", "10px"); txt.setAttribute("font-weight", "bold");
    txt.setAttribute("text-anchor", "middle");
    txt.textContent = t.id;
    svg.appendChild(txt);

    if (isRevealed && isTargeted) {
      const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      ring.setAttribute("cx", t.x); ring.setAttribute("cy", t.y);
      ring.setAttribute("r", 15);
      ring.setAttribute("fill", "none");
      ring.setAttribute("stroke", "#3fb950");
      ring.setAttribute("stroke-width", "1.5");
      ring.setAttribute("stroke-dasharray", "3,3");
      svg.appendChild(ring);
    }
  });

  // 10. Reticle Slew Arc in Room A (Angular Flip)
  if (data.id === "roomA" && progress >= 0.65) {
    const arc = document.createElementNS("http://www.w3.org/2000/svg", "path");
    arc.setAttribute("d", `M ${px + 30} ${py - 15} A 35 35 0 0 1 ${px + 25} ${py + 25}`);
    arc.setAttribute("fill", "none");
    arc.setAttribute("stroke", "#d29922");
    arc.setAttribute("stroke-width", "2");
    svg.appendChild(arc);

    const arcLbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    arcLbl.setAttribute("x", px + 45); arcLbl.setAttribute("y", py + 8);
    arcLbl.setAttribute("fill", "#d29922"); arcLbl.setAttribute("font-size", "10px"); arcLbl.setAttribute("font-weight", "bold");
    arcLbl.textContent = "Δθ = 150°";
    svg.appendChild(arcLbl);
  }

  // 11. Reticle Aim Laser Beam
  const aimDist = 65;
  const aimLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
  aimLine.setAttribute("x1", px); aimLine.setAttribute("y1", py);
  aimLine.setAttribute("x2", px + Math.cos(rad) * aimDist);
  aimLine.setAttribute("y2", py - Math.sin(rad) * aimDist);
  aimLine.setAttribute("stroke", "#58a6ff"); aimLine.setAttribute("stroke-width", "2.5");
  aimLine.setAttribute("stroke-linecap", "round");
  svg.appendChild(aimLine);

  const retDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  retDot.setAttribute("cx", px + Math.cos(rad) * aimDist);
  retDot.setAttribute("cy", py - Math.sin(rad) * aimDist);
  retDot.setAttribute("r", 3);
  retDot.setAttribute("fill", "#58a6ff");
  retDot.setAttribute("stroke", "#fff");
  svg.appendChild(retDot);

  // 12. Player Body Circle with Drop Shadow
  const pCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  pCircle.setAttribute("cx", px); pCircle.setAttribute("cy", py);
  pCircle.setAttribute("r", 8); pCircle.setAttribute("fill", "#58a6ff"); pCircle.setAttribute("stroke", "#fff"); pCircle.setAttribute("stroke-width", "2.5");
  pCircle.setAttribute("filter", "url(#wall-drop-shadow)");
  svg.appendChild(pCircle);
}

function renderRoomTimeline(containerId, data, progress) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  data.threats.forEach((t, idx) => {
    const row = document.createElement("div");
    row.className = "t-row";
    
    const isMissed = !data.isClearable && idx === 1;
    const leftPct = (t.revealDist / 6.0) * 80;

    row.innerHTML = `
      <div class="t-lbl">${t.id} (${t.name})</div>
      <div class="t-track">
        <div class="t-block t-block-rot" style="left: ${leftPct}%; width: 8%;"></div>
        <div class="t-block t-block-acq" style="left: ${leftPct + 8}%; width: 6%;"></div>
        <div class="t-block t-block-srv" style="left: ${leftPct + 14}%; width: 20%;"></div>
        <div class="t-bar-deadline" style="left: ${leftPct + (isMissed ? 18 : 34)}%;" title="Deadline"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function playTwoRoomsAnim() {
  cancelAnimationFrame(twoRoomsAnimId);
  twoRoomsProgress = 0.0;
  const start = performance.now();
  const dur = 3000;

  function step(now) {
    const elapsed = now - start;
    twoRoomsProgress = Math.min(1.0, elapsed / dur);
    renderTwoRooms(twoRoomsProgress);
    if (twoRoomsProgress < 1.0) {
      twoRoomsAnimId = requestAnimationFrame(step);
    }
  }
  twoRoomsAnimId = requestAnimationFrame(step);
}

function resetTwoRoomsAnim() {
  cancelAnimationFrame(twoRoomsAnimId);
  twoRoomsProgress = 0.0;
  renderTwoRooms(0.0);
}

// =============================================================================
// COMPONENT 2: GEOMETRY -> SCHEDULE 4-PANEL PIPELINE
// =============================================================================

let pipeTime = 0.0;
let pipeAnimId = null;

function initPipeline() {
  const scrubber = document.getElementById("pipeline-time-scrubber");
  const playBtn = document.getElementById("btn-pipeline-play");

  scrubber.addEventListener("input", (e) => {
    pipeTime = parseFloat(e.target.value);
    renderPipeline(pipeTime);
  });

  playBtn.addEventListener("click", () => {
    cancelAnimationFrame(pipeAnimId);
    pipeTime = 0.0;
    const start = performance.now();
    const dur = 4000;

    function step(now) {
      const elapsed = now - start;
      pipeTime = (elapsed / dur) * 2.4;
      if (pipeTime > 2.4) pipeTime = 2.4;
      scrubber.value = pipeTime;
      renderPipeline(pipeTime);
      if (pipeTime < 2.4) {
        pipeAnimId = requestAnimationFrame(step);
      }
    }
    pipeAnimId = requestAnimationFrame(step);
  });

  renderPipeline(0.0);
}

function renderPipeline(t) {
  document.getElementById("pipe-time-display").textContent = t.toFixed(2) + "s";
  renderPipeGeo(t);
  renderPipeTimeline(t);
  renderPipeReticle(t);
}

function renderPipeGeo(t) {
  const svg = document.getElementById("svg-pipe-geo");
  if (!svg) return;
  svg.innerHTML = "";

  // 1. Defs: Shadows, Grids & Hatching
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <pattern id="pipe-grid" width="15" height="15" patternUnits="userSpaceOnUse">
      <path d="M 15 0 L 0 0 0 15" fill="none" stroke="rgba(88, 166, 255, 0.05)" stroke-width="1"/>
    </pattern>
    <pattern id="pipe-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(88, 166, 255, 0.25)" stroke-width="2" />
    </pattern>
    <filter id="pipe-shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="2" dy="3" stdDeviation="2" flood-color="#000" flood-opacity="0.6"/>
    </filter>
  `;
  svg.appendChild(defs);

  // 2. Outer Border & Grid
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", 5); bg.setAttribute("y", 5);
  bg.setAttribute("width", 230); bg.setAttribute("height", 170);
  bg.setAttribute("fill", "#0a0e14"); bg.setAttribute("stroke", "#30363d"); bg.setAttribute("rx", 4);
  svg.appendChild(bg);

  const grid = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  grid.setAttribute("x", 5); grid.setAttribute("y", 5);
  grid.setAttribute("width", 230); grid.setAttribute("height", 170);
  grid.setAttribute("fill", "url(#pipe-grid)");
  svg.appendChild(grid);

  // 3. Concrete Partition Obstacle (Casts occlusion on T1 and T2)
  const obsBase = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  obsBase.setAttribute("x", 95); obsBase.setAttribute("y", 5);
  obsBase.setAttribute("width", 22); obsBase.setAttribute("height", 85);
  obsBase.setAttribute("fill", "#161b22"); obsBase.setAttribute("stroke", "#58a6ff"); obsBase.setAttribute("stroke-width", "1.2");
  obsBase.setAttribute("filter", "url(#pipe-shadow)"); obsBase.setAttribute("rx", 2);
  svg.appendChild(obsBase);

  const obsHatch = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  obsHatch.setAttribute("x", 97); obsHatch.setAttribute("y", 7);
  obsHatch.setAttribute("width", 18); obsHatch.setAttribute("height", 81);
  obsHatch.setAttribute("fill", "url(#pipe-hatch)"); obsHatch.setAttribute("opacity", "0.4");
  svg.appendChild(obsHatch);

  const obsCap = document.createElementNS("http://www.w3.org/2000/svg", "line");
  obsCap.setAttribute("x1", 95); obsCap.setAttribute("y1", 7);
  obsCap.setAttribute("x2", 117); obsCap.setAttribute("y2", 7);
  obsCap.setAttribute("stroke", "rgba(136, 192, 255, 0.8)"); obsCap.setAttribute("stroke-width", "2");
  svg.appendChild(obsCap);

  const obsLbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
  obsLbl.setAttribute("x", 106); obsLbl.setAttribute("y", 45);
  obsLbl.setAttribute("transform", "rotate(-90 106 45)");
  obsLbl.setAttribute("fill", "rgba(200, 225, 255, 0.7)"); obsLbl.setAttribute("font-size", "7px"); obsLbl.setAttribute("font-weight", "bold");
  obsLbl.setAttribute("text-anchor", "middle"); obsLbl.textContent = "WALL";
  svg.appendChild(obsLbl);

  // Grazing Ray threshold
  const thresh = document.createElementNS("http://www.w3.org/2000/svg", "line");
  thresh.setAttribute("x1", 117); thresh.setAttribute("y1", 90);
  thresh.setAttribute("x2", 200); thresh.setAttribute("y2", 130);
  thresh.setAttribute("stroke", "rgba(255, 255, 255, 0.15)"); thresh.setAttribute("stroke-dasharray", "2,2");
  svg.appendChild(thresh);

  // 4. Traversal Route
  const route = document.createElementNS("http://www.w3.org/2000/svg", "line");
  route.setAttribute("x1", 20); route.setAttribute("y1", 135);
  route.setAttribute("x2", 220); route.setAttribute("y2", 135);
  route.setAttribute("stroke", "rgba(88, 166, 255, 0.35)"); route.setAttribute("stroke-dasharray", "3,3");
  svg.appendChild(route);

  const px = 20 + (t / 2.4) * 200;
  const py = 135;

  // Threat T1 (Upper Pocket: 175, 45, Angle +65 deg)
  const t1 = { x: 175, y: 40, id: "T1", name: "T1 (+65°)", r: 0.6 };
  // Threat T2 (Lower Right: 195, 120, Angle -55 deg)
  const t2 = { x: 195, y: 110, id: "T2", name: "T2 (-55°)", r: 1.1 };

  const isT1Revealed = t >= t1.r;
  const isT2Revealed = t >= t2.r;
  const activeT = (t >= 0.6 && t < 1.3) ? "T1" : (t >= 1.3 ? "T2" : null);

  let curAimDeg = 0.0;
  if (t >= 0.6 && t < 1.3) curAimDeg = 65.0;
  else if (t >= 1.3) curAimDeg = -55.0;

  const rad = curAimDeg * Math.PI / 180;
  const fovHalf = 28 * Math.PI / 180;
  const fovD = 80;

  // FOV Cone
  const fovP1x = px + Math.cos(rad - fovHalf) * fovD;
  const fovP1y = py - Math.sin(rad - fovHalf) * fovD;
  const fovP2x = px + Math.cos(rad + fovHalf) * fovD;
  const fovP2y = py - Math.sin(rad + fovHalf) * fovD;

  const fovCone = document.createElementNS("http://www.w3.org/2000/svg", "path");
  fovCone.setAttribute("d", `M ${px} ${py} L ${fovP1x} ${fovP1y} A ${fovD} ${fovD} 0 0 0 ${fovP2x} ${fovP2y} Z`);
  fovCone.setAttribute("fill", "rgba(88, 166, 255, 0.08)");
  fovCone.setAttribute("stroke", "rgba(88, 166, 255, 0.2)");
  svg.appendChild(fovCone);

  // 5. Draw Threat 1 with explicit [T1] Box and Ray
  if (isT1Revealed) {
    const ray1 = document.createElementNS("http://www.w3.org/2000/svg", "line");
    ray1.setAttribute("x1", px); ray1.setAttribute("y1", py);
    ray1.setAttribute("x2", t1.x); ray1.setAttribute("y2", t1.y);
    ray1.setAttribute("stroke", activeT === "T1" ? "#3fb950" : "rgba(88, 166, 255, 0.5)");
    ray1.setAttribute("stroke-width", activeT === "T1" ? "2" : "1");
    if (activeT !== "T1") ray1.setAttribute("stroke-dasharray", "3,2");
    svg.appendChild(ray1);
  }

  const box1 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  box1.setAttribute("x", t1.x - 9); box1.setAttribute("y", t1.y - 9);
  box1.setAttribute("width", 18); box1.setAttribute("height", 18);
  box1.setAttribute("fill", isT1Revealed ? (activeT === "T1" ? "#3fb950" : "#d29922") : "#21262d");
  box1.setAttribute("stroke", isT1Revealed ? "#fff" : "#484f58");
  box1.setAttribute("stroke-width", activeT === "T1" ? "2" : "1");
  box1.setAttribute("rx", 3);
  svg.appendChild(box1);

  const txt1 = document.createElementNS("http://www.w3.org/2000/svg", "text");
  txt1.setAttribute("x", t1.x); txt1.setAttribute("y", t1.y + 4);
  txt1.setAttribute("fill", "#fff"); txt1.setAttribute("font-size", "9px"); txt1.setAttribute("font-weight", "bold");
  txt1.setAttribute("text-anchor", "middle"); txt1.textContent = "T1";
  svg.appendChild(txt1);

  const lbl1 = document.createElementNS("http://www.w3.org/2000/svg", "text");
  lbl1.setAttribute("x", t1.x + 12); lbl1.setAttribute("y", t1.y + 3);
  lbl1.setAttribute("fill", isT1Revealed ? "#58a6ff" : "#8b949e"); lbl1.setAttribute("font-size", "8px"); lbl1.setAttribute("font-weight", "bold");
  lbl1.textContent = isT1Revealed ? "T1 (+65°)" : "T1 (r₁=0.6s)";
  svg.appendChild(lbl1);

  // 6. Draw Threat 2 with explicit [T2] Box and Ray
  if (isT2Revealed) {
    const ray2 = document.createElementNS("http://www.w3.org/2000/svg", "line");
    ray2.setAttribute("x1", px); ray2.setAttribute("y1", py);
    ray2.setAttribute("x2", t2.x); ray2.setAttribute("y2", t2.y);
    ray2.setAttribute("stroke", activeT === "T2" ? "#3fb950" : "rgba(88, 166, 255, 0.5)");
    ray2.setAttribute("stroke-width", activeT === "T2" ? "2" : "1");
    if (activeT !== "T2") ray2.setAttribute("stroke-dasharray", "3,2");
    svg.appendChild(ray2);
  }

  const box2 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  box2.setAttribute("x", t2.x - 9); box2.setAttribute("y", t2.y - 9);
  box2.setAttribute("width", 18); box2.setAttribute("height", 18);
  box2.setAttribute("fill", isT2Revealed ? (activeT === "T2" ? "#3fb950" : "#d29922") : "#21262d");
  box2.setAttribute("stroke", isT2Revealed ? "#fff" : "#484f58");
  box2.setAttribute("stroke-width", activeT === "T2" ? "2" : "1");
  box2.setAttribute("rx", 3);
  svg.appendChild(box2);

  const txt2 = document.createElementNS("http://www.w3.org/2000/svg", "text");
  txt2.setAttribute("x", t2.x); txt2.setAttribute("y", t2.y + 4);
  txt2.setAttribute("fill", "#fff"); txt2.setAttribute("font-size", "9px"); txt2.setAttribute("font-weight", "bold");
  txt2.setAttribute("text-anchor", "middle"); txt2.textContent = "T2";
  svg.appendChild(txt2);

  const lbl2 = document.createElementNS("http://www.w3.org/2000/svg", "text");
  lbl2.setAttribute("x", t2.x + 12); lbl2.setAttribute("y", t2.y + 3);
  lbl2.setAttribute("fill", isT2Revealed ? "#58a6ff" : "#8b949e"); lbl2.setAttribute("font-size", "8px"); lbl2.setAttribute("font-weight", "bold");
  lbl2.textContent = isT2Revealed ? "T2 (-55°)" : "T2 (r₂=1.1s)";
  svg.appendChild(lbl2);

  // 7. Reticle Laser Beam & Player Dot
  const aimL = 50;
  const beam = document.createElementNS("http://www.w3.org/2000/svg", "line");
  beam.setAttribute("x1", px); beam.setAttribute("y1", py);
  beam.setAttribute("x2", px + Math.cos(rad) * aimL);
  beam.setAttribute("y2", py - Math.sin(rad) * aimL);
  beam.setAttribute("stroke", "#58a6ff"); beam.setAttribute("stroke-width", "2");
  svg.appendChild(beam);

  const pl = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  pl.setAttribute("cx", px); pl.setAttribute("cy", py); pl.setAttribute("r", 6);
  pl.setAttribute("fill", "#58a6ff"); pl.setAttribute("stroke", "#fff"); pl.setAttribute("stroke-width", "2");
  svg.appendChild(pl);
}

function renderPipeTimeline(t) {
  const svg = document.getElementById("svg-pipe-timeline");
  if (!svg) return;
  svg.innerHTML = "";

  const r1 = 0.6, d1 = 1.6;
  const r2 = 1.1, d2 = 2.1;

  drawPipeTimelineRow(svg, 45, "T1 (+65°)", r1, d1, t, 0.6, 1.2);
  drawPipeTimelineRow(svg, 105, "T2 (-55°)", r2, d2, t, 1.3, 1.9);

  const cursorX = 45 + (t / 2.4) * 165;
  const cursor = document.createElementNS("http://www.w3.org/2000/svg", "line");
  cursor.setAttribute("x1", cursorX); cursor.setAttribute("y1", 10);
  cursor.setAttribute("x2", cursorX); cursor.setAttribute("y2", 155);
  cursor.setAttribute("stroke", "#fff"); cursor.setAttribute("stroke-width", "1.5"); cursor.setAttribute("stroke-dasharray", "2,2");
  svg.appendChild(cursor);

  const curTag = document.createElementNS("http://www.w3.org/2000/svg", "text");
  curTag.setAttribute("x", cursorX); curTag.setAttribute("y", 165);
  curTag.setAttribute("fill", "#58a6ff"); curTag.setAttribute("font-size", "9px"); curTag.setAttribute("font-weight", "bold");
  curTag.setAttribute("text-anchor", "middle"); curTag.textContent = `${t.toFixed(2)}s`;
  svg.appendChild(curTag);
}

function drawPipeTimelineRow(svg, y, label, r, d, t, srvStart, srvEnd) {
  const xStart = 45 + (r / 2.4) * 165;
  const xDead = 45 + (d / 2.4) * 165;

  const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
  txt.setAttribute("x", 8); txt.setAttribute("y", y + 4);
  txt.setAttribute("fill", t >= r ? "#58a6ff" : "#8b949e"); txt.setAttribute("font-size", "9px"); txt.setAttribute("font-weight", "bold");
  txt.textContent = label;
  svg.appendChild(txt);

  // Background track
  const track = document.createElementNS("http://www.w3.org/2000/svg", "line");
  track.setAttribute("x1", 45); track.setAttribute("y1", y);
  track.setAttribute("x2", 210); track.setAttribute("y2", y);
  track.setAttribute("stroke", "#21262d"); track.setAttribute("stroke-width", "6"); track.setAttribute("stroke-linecap", "round");
  svg.appendChild(track);

  if (t >= r) {
    // Window bar
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", xStart); line.setAttribute("y1", y);
    line.setAttribute("x2", xDead); line.setAttribute("y2", y);
    line.setAttribute("stroke", "#30363d"); line.setAttribute("stroke-width", "8"); line.setAttribute("stroke-linecap", "round");
    svg.appendChild(line);

    // Active service bar if running
    if (t >= srvStart) {
      const xSrvStart = 45 + (srvStart / 2.4) * 165;
      const xSrvCur = Math.min(xDead, 45 + (Math.min(t, srvEnd) / 2.4) * 165);
      const srvBar = document.createElementNS("http://www.w3.org/2000/svg", "line");
      srvBar.setAttribute("x1", xSrvStart); srvBar.setAttribute("y1", y);
      srvBar.setAttribute("x2", xSrvCur); srvBar.setAttribute("y2", y);
      srvBar.setAttribute("stroke", "#3fb950"); srvBar.setAttribute("stroke-width", "6");
      svg.appendChild(srvBar);
    }

    const relDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    relDot.setAttribute("cx", xStart); relDot.setAttribute("cy", y); relDot.setAttribute("r", 4);
    relDot.setAttribute("fill", "#58a6ff"); relDot.setAttribute("stroke", "#fff");
    svg.appendChild(relDot);

    const deadLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    deadLine.setAttribute("x1", xDead); deadLine.setAttribute("y1", y - 6);
    deadLine.setAttribute("x2", xDead); deadLine.setAttribute("y2", y + 6);
    deadLine.setAttribute("stroke", "#f85149"); deadLine.setAttribute("stroke-width", "3");
    svg.appendChild(deadLine);
  }
}

function renderPipeReticle(t) {
  const svg = document.getElementById("svg-pipe-reticle");
  if (!svg) return;
  svg.innerHTML = "";

  const cx = 120, cy = 85, r = 48;
  const dial = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  dial.setAttribute("cx", cx); dial.setAttribute("cy", cy); dial.setAttribute("r", r);
  dial.setAttribute("fill", "#0a0e14"); dial.setAttribute("stroke", "#30363d"); dial.setAttribute("stroke-width", "1.5");
  svg.appendChild(dial);

  // Center crosshair pips
  const chH = document.createElementNS("http://www.w3.org/2000/svg", "line");
  chH.setAttribute("x1", cx - 6); chH.setAttribute("y1", cy);
  chH.setAttribute("x2", cx + 6); chH.setAttribute("y2", cy);
  chH.setAttribute("stroke", "rgba(88, 166, 255, 0.3)");
  svg.appendChild(chH);

  const chV = document.createElementNS("http://www.w3.org/2000/svg", "line");
  chV.setAttribute("x1", cx); chV.setAttribute("y1", cy - 6);
  chV.setAttribute("x2", cx); chV.setAttribute("y2", cy + 6);
  chV.setAttribute("stroke", "rgba(88, 166, 255, 0.3)");
  svg.appendChild(chV);

  // Target Pins with explicit labels
  const pins = [
    { ang: 65, lbl: "T1 (+65°)", isTargeted: t >= 0.6 && t < 1.3 },
    { ang: -55, lbl: "T2 (-55°)", isTargeted: t >= 1.3 }
  ];

  pins.forEach(p => {
    const rad = p.ang * Math.PI / 180;
    const px = cx + Math.cos(rad) * (r - 8);
    const py = cy - Math.sin(rad) * (r - 8);

    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("cx", px); dot.setAttribute("cy", py); dot.setAttribute("r", p.isTargeted ? 4 : 3);
    dot.setAttribute("fill", p.isTargeted ? "#3fb950" : "#d29922");
    dot.setAttribute("stroke", "#fff");
    svg.appendChild(dot);

    const lblX = cx + Math.cos(rad) * (r + 14);
    const lblY = cy - Math.sin(rad) * (r + 14);
    const pinLbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    pinLbl.setAttribute("x", lblX); pinLbl.setAttribute("y", lblY + 3);
    pinLbl.setAttribute("fill", p.isTargeted ? "#3fb950" : "#8b949e");
    pinLbl.setAttribute("font-size", "8.5px"); pinLbl.setAttribute("font-weight", "bold");
    pinLbl.setAttribute("text-anchor", Math.cos(rad) > 0 ? "start" : "end");
    pinLbl.textContent = p.lbl;
    svg.appendChild(pinLbl);
  });

  let currentAng = 0.0;
  if (t >= 0.6 && t < 1.3) currentAng = 65.0;
  else if (t >= 1.3) currentAng = -55.0;

  const needleRad = currentAng * Math.PI / 180;
  const needle = document.createElementNS("http://www.w3.org/2000/svg", "line");
  needle.setAttribute("x1", cx); needle.setAttribute("y1", cy);
  needle.setAttribute("x2", cx + Math.cos(needleRad) * (r - 4));
  needle.setAttribute("y2", cy - Math.sin(needleRad) * (r - 4));
  needle.setAttribute("stroke", "#58a6ff"); needle.setAttribute("stroke-width", "2.5"); needle.setAttribute("stroke-linecap", "round");
  svg.appendChild(needle);
}

// =============================================================================
// COMPONENT 3: MAP KNOWLEDGE SLIDER, TRAVERSAL ANIMATION & STEP-FUNCTION GRAPH
// =============================================================================

let curStimulusKey = "STIM_06";
let curLeadTics = 0;
let knowledgeAnimProgress = 0.0;
let knowledgeAnimId = null;
let isKnowledgePlaying = false;

function initKnowledgeSlider() {
  const select = document.getElementById("select-knowledge-stimulus");
  const slider = document.getElementById("slider-advance-lead");
  const snapBtn = document.getElementById("btn-snap-critical");
  const playBtn = document.getElementById("btn-play-knowledge-anim");

  select.addEventListener("change", () => {
    curStimulusKey = select.value;
    stopKnowledgeAnim();
    updateKnowledgeStimulusUI();
  });

  slider.addEventListener("input", (e) => {
    curLeadTics = parseInt(e.target.value, 10);
    stopKnowledgeAnim();
    updateKnowledgeProbe();
  });

  snapBtn.addEventListener("click", () => {
    const stim = STIMULI_MAP[curStimulusKey];
    curLeadTics = stim.l_star_source_tics || 0;
    slider.value = curLeadTics;
    stopKnowledgeAnim();
    updateKnowledgeProbe();
  });

  if (playBtn) {
    playBtn.addEventListener("click", () => {
      if (isKnowledgePlaying) {
        stopKnowledgeAnim();
      } else {
        playKnowledgeAnim();
      }
    });
  }

  // Smooth scroll links across page to prevent Chromium file:/// frame security warnings
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
      e.preventDefault();
      const targetId = this.getAttribute("href").substring(1);
      const targetElem = document.getElementById(targetId);
      if (targetElem) {
        targetElem.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  updateKnowledgeStimulusUI();
}

function updateKnowledgeStimulusUI() {
  const stim = STIMULI_MAP[curStimulusKey];
  const lStarMs = stim.l_star_source_ms !== null ? stim.l_star_source_ms.toFixed(0) : "N/A";
  document.getElementById("slider-lstar-marker").textContent = `Critical Lead ℓ* = ${lStarMs} ms (${stim.l_star_source_tics} tics)`;
  document.getElementById("slider-advance-lead").value = curLeadTics;
  updateKnowledgeProbe();
}

function updateKnowledgeProbe() {
  const stim = STIMULI_MAP[curStimulusKey];
  const res = solveDiscreteScheduleWithLead(stim.threats, curLeadTics);
  const curLeadMs = curLeadTics * TIC_MS;

  document.getElementById("lead-value-tag").textContent = `${curLeadTics} tics (${curLeadMs.toFixed(1)} ms)`;
  document.getElementById("gauge-margin-text").textContent = `${res.marginTics > 0 ? "+" : ""}${res.marginTics} tics (${res.marginMs > 0 ? "+" : ""}${res.marginMs.toFixed(1)} ms)`;

  const bar = document.getElementById("gauge-active-fill");
  const pct = Math.min(50, (Math.abs(res.marginTics) / 10.0) * 50);
  if (res.marginTics >= 0) {
    bar.className = "gauge-fill-bar positive";
    bar.style.width = `${pct}%`;
  } else {
    bar.className = "gauge-fill-bar negative";
    bar.style.width = `${pct}%`;
  }

  const banner = document.getElementById("epistemic-banner-box");
  const icon = document.getElementById("banner-icon-glyph");
  const title = document.getElementById("banner-title-text");
  const desc = document.getElementById("banner-desc-text");

  const lStarTics = stim.l_star_source_tics;
  const lStarMs = stim.l_star_source_ms !== null ? stim.l_star_source_ms.toFixed(0) : "N/A";

  if (res.marginTics >= 0) {
    banner.className = "epistemic-banner rescued";
    icon.textContent = "🛡️";
    title.textContent = `PRE-AIM RESCUED (ℓ ≥ ℓ* = ${lStarTics} tics / ${lStarMs} ms)`;
    desc.textContent = `Prior spatial knowledge allows anticipatory reticle alignment before aperture reveal (a_j < r_j). The encounter clears safely with a +${res.marginTics} tic reserve!`;
  } else {
    banner.className = "epistemic-banner";
    icon.textContent = "💀";
    title.textContent = `INSUFFICIENT WARNING (ℓ < ℓ* = ${lStarTics} tics / ${lStarMs} ms)`;
    desc.textContent = `Reticle cannot pre-align early enough. Non-anticipatory slew creates an unavoidable deadline breach (L* = +${Math.abs(res.marginTics)} tics).`;
  }

  renderKnowledgeMapSVG(stim, res, knowledgeAnimProgress);
  renderKnowledgeTimeline(res);
  renderMarginCurveSVG(stim, curLeadTics);
}

function playKnowledgeAnim() {
  cancelAnimationFrame(knowledgeAnimId);
  isKnowledgePlaying = true;
  const playBtn = document.getElementById("btn-play-knowledge-anim");
  if (playBtn) playBtn.textContent = "⏸ Pause Traversal";

  const stim = STIMULI_MAP[curStimulusKey];
  const res = solveDiscreteScheduleWithLead(stim.threats, curLeadTics);
  const start = performance.now() - (knowledgeAnimProgress * 3200);
  const dur = 3200;

  function step(now) {
    const elapsed = now - start;
    knowledgeAnimProgress = Math.min(1.0, elapsed / dur);
    renderKnowledgeMapSVG(stim, res, knowledgeAnimProgress);

    if (knowledgeAnimProgress < 1.0 && isKnowledgePlaying) {
      knowledgeAnimId = requestAnimationFrame(step);
    } else {
      isKnowledgePlaying = false;
      if (playBtn) playBtn.textContent = "↺ Replay Traversal";
    }
  }
  knowledgeAnimId = requestAnimationFrame(step);
}

function stopKnowledgeAnim() {
  cancelAnimationFrame(knowledgeAnimId);
  isKnowledgePlaying = false;
  knowledgeAnimProgress = 0.0;
  const playBtn = document.getElementById("btn-play-knowledge-anim");
  if (playBtn) playBtn.textContent = "▶ Animate Traversal";
}

function renderKnowledgeMapSVG(stim, res, progress) {
  const svg = document.getElementById("svg-knowledge-map");
  if (!svg) return;
  svg.innerHTML = "";

  const isRescued = res.marginTics >= 0;

  // Background
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", 15); bg.setAttribute("y", 15);
  bg.setAttribute("width", 430); bg.setAttribute("height", 250);
  bg.setAttribute("fill", "#0d1117"); bg.setAttribute("stroke", "#30363d"); bg.setAttribute("stroke-width", "2");
  bg.setAttribute("rx", 6);
  svg.appendChild(bg);

  // Obstacle Baffles
  const obsDefs = [
    { x: 170, y: 0, w: 25, h: 95 },
    { x: 280, y: 185, w: 25, h: 95 }
  ];
  obsDefs.forEach(o => {
    const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    r.setAttribute("x", o.x); r.setAttribute("y", o.y);
    r.setAttribute("width", o.w); r.setAttribute("height", o.h);
    r.setAttribute("fill", "#21262d"); r.setAttribute("stroke", "#484f58"); r.setAttribute("stroke-width", "1.5");
    r.setAttribute("rx", 3);
    svg.appendChild(r);
  });

  // Traversal path line
  const path = document.createElementNS("http://www.w3.org/2000/svg", "line");
  path.setAttribute("x1", 30); path.setAttribute("y1", 140);
  path.setAttribute("x2", 430); path.setAttribute("y2", 140);
  path.setAttribute("stroke", "rgba(88, 166, 255, 0.4)"); path.setAttribute("stroke-dasharray", "4,4"); path.setAttribute("stroke-width", "2");
  svg.appendChild(path);

  // Player position along traversal path
  const px = 40 + progress * 370;
  const py = 140;

  // Compute active reticle aim angle based on pre-aim lead vs blind reveal
  let curAimDeg = 0.0;
  let activeTargetId = null;
  const t1Angle = stim.threats[0] ? stim.threats[0].angle_deg : 45;
  const t2Angle = stim.threats[1] ? stim.threats[1].angle_deg : -65;

  if (isRescued) {
    // With adequate advance knowledge (ell >= ell*), reticle pre-aims T1 immediately
    if (progress < 0.50) {
      curAimDeg = t1Angle;
      activeTargetId = "T1";
    } else {
      curAimDeg = t2Angle;
      activeTargetId = "T2";
    }
  } else {
    // Blind / insufficient lead: looks forward until unocclusion, then slews late
    if (progress < 0.35) {
      curAimDeg = 0.0;
    } else if (progress < 0.70) {
      curAimDeg = t1Angle;
      activeTargetId = "T1";
    } else {
      curAimDeg = t2Angle;
      activeTargetId = "T2";
    }
  }

  // Update Reticle Dial Widget
  renderKnowledgeDial(curAimDeg);

  const rad = curAimDeg * Math.PI / 180;
  const fovHalfAngle = 30 * Math.PI / 180;
  const fovDist = 120;

  // 1. Draw Player Vision Field of View (FOV) Cone
  const fovP1x = px + Math.cos(rad - fovHalfAngle) * fovDist;
  const fovP1y = py - Math.sin(rad - fovHalfAngle) * fovDist;
  const fovP2x = px + Math.cos(rad + fovHalfAngle) * fovDist;
  const fovP2y = py - Math.sin(rad + fovHalfAngle) * fovDist;

  const fovCone = document.createElementNS("http://www.w3.org/2000/svg", "path");
  fovCone.setAttribute("d", `M ${px} ${py} L ${fovP1x} ${fovP1y} A ${fovDist} ${fovDist} 0 0 0 ${fovP2x} ${fovP2y} Z`);
  fovCone.setAttribute("fill", isRescued ? "rgba(63, 185, 80, 0.08)" : "rgba(88, 166, 255, 0.08)");
  fovCone.setAttribute("stroke", isRescued ? "rgba(63, 185, 80, 0.25)" : "rgba(88, 166, 255, 0.2)");
  fovCone.setAttribute("stroke-width", "1");
  svg.appendChild(fovCone);

  // 2. Obstacle Occlusion Grazing Lines
  obsDefs.forEach(o => {
    if (o.y === 0) {
      const cx = o.x + o.w;
      const cy = o.h;
      const gLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      gLine.setAttribute("x1", cx); gLine.setAttribute("y1", cy);
      gLine.setAttribute("x2", cx + 110); gLine.setAttribute("y2", cy + 55);
      gLine.setAttribute("stroke", "rgba(255, 255, 255, 0.12)");
      gLine.setAttribute("stroke-dasharray", "3,3");
      svg.appendChild(gLine);
    }
  });

  // 3. Threats & Active Unocclusion Rays
  const tPositions = [{x: 300, y: 65}, {x: 390, y: 215}];
  stim.threats.forEach((t, idx) => {
    const pos = tPositions[idx] || {x: 350, y: 100};
    const isRevealed = (idx === 0 && px >= 140) || (idx === 1 && px >= 250);
    const isTargeted = activeTargetId === t.id;
    const isBreach = !isRescued && idx === 1 && progress >= 0.75;

    if (isRevealed) {
      const ray = document.createElementNS("http://www.w3.org/2000/svg", "line");
      ray.setAttribute("x1", px); ray.setAttribute("y1", py);
      ray.setAttribute("x2", pos.x); ray.setAttribute("y2", pos.y);
      ray.setAttribute("stroke", isBreach ? "#f85149" : (isTargeted ? "#3fb950" : "rgba(88, 166, 255, 0.5)"));
      ray.setAttribute("stroke-width", isTargeted ? "2.5" : "1.5");
      if (!isTargeted) ray.setAttribute("stroke-dasharray", "4,2");
      svg.appendChild(ray);

      const midX = (px + pos.x) / 2;
      const midY = (py + pos.y) / 2;
      const rayTag = document.createElementNS("http://www.w3.org/2000/svg", "text");
      rayTag.setAttribute("x", midX); rayTag.setAttribute("y", midY - 4);
      rayTag.setAttribute("fill", isBreach ? "#f85149" : "#58a6ff");
      rayTag.setAttribute("font-size", "9px");
      rayTag.setAttribute("text-anchor", "middle");
      rayTag.textContent = isBreach ? "BREACH ✗" : (isRescued && idx === 0 && progress < 0.35 ? "PRE-AIM LOCK" : "LOS ACTIVE");
      svg.appendChild(rayTag);
    }

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", pos.x - 10); rect.setAttribute("y", pos.y - 10);
    rect.setAttribute("width", 20); rect.setAttribute("height", 20);
    rect.setAttribute("fill", isBreach ? "#f85149" : (isTargeted ? "#3fb950" : (isRevealed ? "#d29922" : "#21262d")));
    rect.setAttribute("stroke", isRevealed ? "#fff" : "#484f58");
    rect.setAttribute("stroke-width", isTargeted ? "2" : "1");
    rect.setAttribute("rx", 4);
    svg.appendChild(rect);

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", pos.x); txt.setAttribute("y", pos.y + 4);
    txt.setAttribute("fill", "#fff"); txt.setAttribute("font-size", "9.5px"); txt.setAttribute("font-weight", "bold");
    txt.setAttribute("text-anchor", "middle");
    txt.textContent = t.id;
    svg.appendChild(txt);

    if (isRevealed && isTargeted) {
      const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      ring.setAttribute("cx", pos.x); ring.setAttribute("cy", pos.y);
      ring.setAttribute("r", 15);
      ring.setAttribute("fill", "none");
      ring.setAttribute("stroke", isBreach ? "#f85149" : "#3fb950");
      ring.setAttribute("stroke-width", "1.5");
      ring.setAttribute("stroke-dasharray", "3,3");
      svg.appendChild(ring);
    }
  });

  // 4. Reticle Laser Beam
  const aimDist = 70;
  const beam = document.createElementNS("http://www.w3.org/2000/svg", "line");
  beam.setAttribute("x1", px); beam.setAttribute("y1", py);
  beam.setAttribute("x2", px + Math.cos(rad) * aimDist);
  beam.setAttribute("y2", py - Math.sin(rad) * aimDist);
  beam.setAttribute("stroke", isRescued ? "#3fb950" : (progress >= 0.75 ? "#f85149" : "#58a6ff"));
  beam.setAttribute("stroke-width", "2.5");
  beam.setAttribute("stroke-linecap", "round");
  svg.appendChild(beam);

  const retDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  retDot.setAttribute("cx", px + Math.cos(rad) * aimDist);
  retDot.setAttribute("cy", py - Math.sin(rad) * aimDist);
  retDot.setAttribute("r", 3);
  retDot.setAttribute("fill", isRescued ? "#3fb950" : "#58a6ff");
  retDot.setAttribute("stroke", "#fff");
  svg.appendChild(retDot);

  // 5. Player Body Circle
  const player = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  player.setAttribute("cx", px); player.setAttribute("cy", py);
  player.setAttribute("r", 8); player.setAttribute("fill", "#58a6ff"); player.setAttribute("stroke", "#fff"); player.setAttribute("stroke-width", "2.5");
  svg.appendChild(player);
}

function renderKnowledgeTimeline(res) {
  const container = document.getElementById("knowledge-timeline-rows");
  if (!container) return;
  container.innerHTML = "";

  const totalTics = 70;
  res.schedule.forEach(item => {
    const rotPct = (item.rotStart / totalTics) * 100;
    const rotWidth = Math.max(2, ((item.rotFinish - item.rotStart) / totalTics) * 100);
    const acqPct = (item.acqStart / totalTics) * 100;
    const acqWidth = (ACQUISITION_TICS / totalTics) * 100;
    const srvPct = (item.srvStart / totalTics) * 100;
    const srvWidth = (SERVICE_TICS / totalTics) * 100;
    const deadPct = (item.deadline / totalTics) * 100;

    const row = document.createElement("div");
    row.className = "t-row";
    row.innerHTML = `
      <div class="t-lbl">${item.id} (${item.angle > 0 ? "+" : ""}${item.angle.toFixed(0)}°)</div>
      <div class="t-track">
        <div class="t-block t-block-rot" style="left: ${rotPct}%; width: ${rotWidth}%;" title="Reticle Slew"></div>
        <div class="t-block t-block-acq" style="left: ${acqPct}%; width: ${acqWidth}%;" title="Perceptual Acquisition"></div>
        <div class="t-block t-block-srv" style="left: ${srvPct}%; width: ${srvWidth}%;" title="Weapon Service"></div>
        <div class="t-bar-deadline" style="left: ${deadPct}%;" title="Hostile Deadline"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderKnowledgeDial(angleDeg) {
  const svg = document.getElementById("svg-knowledge-dial");
  if (!svg) return;
  svg.innerHTML = "";

  const cx = 40, cy = 40, r = 32;
  const dial = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  dial.setAttribute("cx", cx); dial.setAttribute("cy", cy); dial.setAttribute("r", r);
  dial.setAttribute("fill", "#0d1117"); dial.setAttribute("stroke", "#30363d"); dial.setAttribute("stroke-width", "1.5");
  svg.appendChild(dial);

  const rad = angleDeg * Math.PI / 180;
  const needle = document.createElementNS("http://www.w3.org/2000/svg", "line");
  needle.setAttribute("x1", cx); needle.setAttribute("y1", cy);
  needle.setAttribute("x2", cx + Math.cos(rad) * (r - 4));
  needle.setAttribute("y2", cy - Math.sin(rad) * (r - 4));
  needle.setAttribute("stroke", "#58a6ff"); needle.setAttribute("stroke-width", "2.5"); needle.setAttribute("stroke-linecap", "round");
  svg.appendChild(needle);
}

function renderMarginCurveSVG(stim, activeLeadTics) {
  const svg = document.getElementById("svg-knowledge-curve");
  if (!svg) return;
  svg.innerHTML = "";

  const padLeft = 45, padRight = 25, padTop = 15, padBottom = 25;
  const w = 460 - padLeft - padRight;
  const h = 140 - padTop - padBottom;

  const minMargin = -8, maxMargin = +6;
  const minLead = 0, maxLead = 10;

  function xPos(l) { return padLeft + (l / maxLead) * w; }
  function yPos(m) { return padTop + h - ((m - minMargin) / (maxMargin - minMargin)) * h; }

  const zeroY = yPos(0);
  const redZone = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  redZone.setAttribute("x", padLeft); redZone.setAttribute("y", zeroY);
  redZone.setAttribute("width", w); redZone.setAttribute("height", yPos(minMargin) - zeroY);
  redZone.setAttribute("fill", "rgba(248, 81, 73, 0.08)");
  svg.appendChild(redZone);

  const greenZone = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  greenZone.setAttribute("x", padLeft); greenZone.setAttribute("y", padTop);
  greenZone.setAttribute("width", w); greenZone.setAttribute("height", zeroY - padTop);
  greenZone.setAttribute("fill", "rgba(63, 185, 80, 0.08)");
  svg.appendChild(greenZone);

  const zeroLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
  zeroLine.setAttribute("x1", padLeft); zeroLine.setAttribute("y1", zeroY);
  zeroLine.setAttribute("x2", padLeft + w); zeroLine.setAttribute("y2", zeroY);
  zeroLine.setAttribute("stroke", "#8b949e"); zeroLine.setAttribute("stroke-width", "1.5");
  zeroLine.setAttribute("stroke-dasharray", "3,3");
  svg.appendChild(zeroLine);

  const zeroTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
  zeroTxt.setAttribute("x", padLeft - 6); zeroTxt.setAttribute("y", zeroY + 4);
  zeroTxt.setAttribute("fill", "#8b949e"); zeroTxt.setAttribute("font-size", "10px");
  zeroTxt.setAttribute("text-anchor", "end");
  zeroTxt.textContent = "M=0";
  svg.appendChild(zeroTxt);

  const pts = [];
  stim.curve.forEach((pt, idx) => {
    const x = xPos(pt.lead_tics);
    const y = yPos(pt.tactical_margin_tics);
    if (idx > 0) {
      pts.push(`${x},${yPos(stim.curve[idx-1].tactical_margin_tics)}`);
    }
    pts.push(`${x},${y}`);
  });

  const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  polyline.setAttribute("points", pts.join(" "));
  polyline.setAttribute("fill", "none");
  polyline.setAttribute("stroke", "#58a6ff");
  polyline.setAttribute("stroke-width", "2.5");
  svg.appendChild(polyline);

  if (stim.l_star_source_tics !== null) {
    const sx = xPos(stim.l_star_source_tics);
    const sLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    sLine.setAttribute("x1", sx); sLine.setAttribute("y1", padTop);
    sLine.setAttribute("x2", sx); sLine.setAttribute("y2", padTop + h);
    sLine.setAttribute("stroke", "#58a6ff"); sLine.setAttribute("stroke-width", "1.5");
    sLine.setAttribute("stroke-dasharray", "4,4");
    svg.appendChild(sLine);
  }

  if (stim.l_star_survival_tics !== null) {
    const engX = xPos(stim.l_star_survival_tics);
    const engLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    engLine.setAttribute("x1", engX); engLine.setAttribute("y1", padTop);
    engLine.setAttribute("x2", engX); engLine.setAttribute("y2", padTop + h);
    engLine.setAttribute("stroke", "#3fb950"); engLine.setAttribute("stroke-width", "1.5");
    engLine.setAttribute("stroke-dasharray", "2,2");
    svg.appendChild(engLine);
  }

  const activePt = stim.curve[activeLeadTics] || stim.curve[0];
  const curX = xPos(activeLeadTics);
  const curY = yPos(activePt.tactical_margin_tics);

  const curDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  curDot.setAttribute("cx", curX); curDot.setAttribute("cy", curY);
  curDot.setAttribute("r", 5);
  curDot.setAttribute("fill", activePt.tactical_margin_tics >= 0 ? "#3fb950" : "#f85149");
  curDot.setAttribute("stroke", "#fff"); curDot.setAttribute("stroke-width", "2");
  svg.appendChild(curDot);

  for (let l = 0; l <= 10; l += 2) {
    const lx = xPos(l);
    const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lbl.setAttribute("x", lx); lbl.setAttribute("y", padTop + h + 18);
    lbl.setAttribute("fill", "#8b949e"); lbl.setAttribute("font-size", "10px");
    lbl.setAttribute("text-anchor", "middle");
    lbl.textContent = `${l}t (${(l * TIC_MS).toFixed(0)}ms)`;
    svg.appendChild(lbl);
  }
}

// =============================================================================
// COMPONENT 4: DECOUPLING COMPARISON (STIM_07 vs STIM_11)
// =============================================================================

function initDecouplingView() {
  const svg = document.getElementById("svg-decoupling-comparison");
  if (!svg) return;
  svg.innerHTML = "";

  const s07 = STIMULI_MAP["STIM_07"];
  const s11 = STIMULI_MAP["STIM_11"];
  if (!s07 || !s11) return;

  const padLeft = 55, padRight = 35, padTop = 20, padBottom = 30;
  const w = 940 - padLeft - padRight;
  const h = 220 - padTop - padBottom;

  const minMargin = -8, maxMargin = +6;
  const minLead = 0, maxLead = 10;

  function xPos(l) { return padLeft + (l / maxLead) * w; }
  function yPos(m) { return padTop + h - ((m - minMargin) / (maxMargin - minMargin)) * h; }

  const zeroY = yPos(0);
  const zeroLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
  zeroLine.setAttribute("x1", padLeft); zeroLine.setAttribute("y1", zeroY);
  zeroLine.setAttribute("x2", padLeft + w); zeroLine.setAttribute("y2", zeroY);
  zeroLine.setAttribute("stroke", "#8b949e"); zeroLine.setAttribute("stroke-width", "1.5");
  zeroLine.setAttribute("stroke-dasharray", "3,3");
  svg.appendChild(zeroLine);

  const zeroTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
  zeroTxt.setAttribute("x", padLeft - 8); zeroTxt.setAttribute("y", zeroY + 4);
  zeroTxt.setAttribute("fill", "#8b949e"); zeroTxt.setAttribute("font-size", "11px");
  zeroTxt.setAttribute("text-anchor", "end");
  zeroTxt.textContent = "M = 0 (Feasible)";
  svg.appendChild(zeroTxt);

  const pts07 = [];
  s07.curve.forEach((pt, idx) => {
    const x = xPos(pt.lead_tics);
    const y = yPos(pt.tactical_margin_tics);
    if (idx > 0) pts07.push(`${x},${yPos(s07.curve[idx-1].tactical_margin_tics)}`);
    pts07.push(`${x},${y}`);
  });
  const poly07 = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  poly07.setAttribute("points", pts07.join(" "));
  poly07.setAttribute("fill", "none");
  poly07.setAttribute("stroke", "#3fb950");
  poly07.setAttribute("stroke-width", "3");
  svg.appendChild(poly07);

  const pts11 = [];
  s11.curve.forEach((pt, idx) => {
    const x = xPos(pt.lead_tics);
    const y = yPos(pt.tactical_margin_tics);
    if (idx > 0) pts11.push(`${x},${yPos(s11.curve[idx-1].tactical_margin_tics)}`);
    pts11.push(`${x},${y}`);
  });
  const poly11 = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  poly11.setAttribute("points", pts11.join(" "));
  poly11.setAttribute("fill", "none");
  poly11.setAttribute("stroke", "#d29922");
  poly11.setAttribute("stroke-width", "3");
  svg.appendChild(poly11);

  const x07 = xPos(s07.l_star_source_tics);
  const l07 = document.createElementNS("http://www.w3.org/2000/svg", "line");
  l07.setAttribute("x1", x07); l07.setAttribute("y1", padTop);
  l07.setAttribute("x2", x07); l07.setAttribute("y2", padTop + h);
  l07.setAttribute("stroke", "#3fb950"); l07.setAttribute("stroke-width", "1.5");
  l07.setAttribute("stroke-dasharray", "4,4");
  svg.appendChild(l07);

  const t07 = document.createElementNS("http://www.w3.org/2000/svg", "text");
  t07.setAttribute("x", x07); t07.setAttribute("y", padTop - 5);
  t07.setAttribute("fill", "#3fb950"); t07.setAttribute("font-size", "11px"); t07.setAttribute("font-weight", "bold");
  t07.setAttribute("text-anchor", "middle");
  t07.textContent = `STIM_07: ℓ* = ${s07.l_star_source_ms.toFixed(0)} ms (4 tics)`;
  svg.appendChild(t07);

  const x11 = xPos(s11.l_star_source_tics);
  const l11 = document.createElementNS("http://www.w3.org/2000/svg", "line");
  l11.setAttribute("x1", x11); l11.setAttribute("y1", padTop);
  l11.setAttribute("x2", x11); l11.setAttribute("y2", padTop + h);
  l11.setAttribute("stroke", "#d29922"); l11.setAttribute("stroke-width", "1.5");
  l11.setAttribute("stroke-dasharray", "4,4");
  svg.appendChild(l11);

  const t11 = document.createElementNS("http://www.w3.org/2000/svg", "text");
  t11.setAttribute("x", x11); t11.setAttribute("y", padTop - 5);
  t11.setAttribute("fill", "#d29922"); t11.setAttribute("font-size", "11px"); t11.setAttribute("font-weight", "bold");
  t11.setAttribute("text-anchor", "middle");
  t11.textContent = `STIM_11: ℓ* = ${s11.l_star_source_ms.toFixed(0)} ms (6 tics)`;
  svg.appendChild(t11);

  for (let l = 0; l <= 10; l++) {
    const lx = xPos(l);
    const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lbl.setAttribute("x", lx); lbl.setAttribute("y", padTop + h + 20);
    lbl.setAttribute("fill", "#8b949e"); lbl.setAttribute("font-size", "11px");
    lbl.setAttribute("text-anchor", "middle");
    lbl.textContent = `${l}t (${(l * TIC_MS).toFixed(0)}ms)`;
    svg.appendChild(lbl);
  }
}

// =============================================================================
// COMPONENT 5: TACTICAL READABILITY ATLAS (12 CANONICAL PROGRESSIONS)
// =============================================================================

const ATLAS_DATA = {
  // --- CHAPTER 1: COUNTING FAILS ---
  corridor: {
    id: "corridor",
    num: "01",
    chapter: "ch1",
    title: "Straight Corridor (M01)",
    tag: "EASY BASELINE",
    provenance: "CANONICAL PCG MODULE",
    what_changed: "Baseline reference: Single forward threat with generous reaction window and zero required angular rotation.",
    k_static: 1,
    margin_tics: 28,
    margin_ms: 800.0,
    l_star_ms: 0,
    verdict: "CLEARABLE",
    threats: [{id: "T1", x: 380, y: 110, angle: 0, reveal_tic: 10, deadline_tic: 45}],
    obstacles: [],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 0}, {t: 50, deg: 0}],
    trace_badge: "Zero Slew (0°)"
  },
  pie: {
    id: "pie",
    num: "02",
    chapter: "ch1",
    title: "Staggered Pie Slicing (M04)",
    tag: "MANY ≠ BAD",
    provenance: "CANONICAL PCG MODULE",
    what_changed: "High threat count (3 targets) is completely clearable because obstacle geometry staggers reveals sequentially across a smooth 35° arc.",
    k_static: 3,
    margin_tics: 23,
    margin_ms: 657.1,
    l_star_ms: 0,
    verdict: "CLEARABLE",
    threats: [
      {id: "T1", x: 230, y: 55, angle: 35, reveal_tic: 8, deadline_tic: 38},
      {id: "T2", x: 320, y: 110, angle: 0, reveal_tic: 20, deadline_tic: 50},
      {id: "T3", x: 390, y: 165, angle: -35, reveal_tic: 32, deadline_tic: 62}
    ],
    obstacles: [
      {x: 140, y: 10, w: 25, h: 65},
      {x: 250, y: 145, w: 25, h: 65}
    ],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 0}, {t: 8, deg: 35}, {t: 22, deg: 0}, {t: 35, deg: -35}, {t: 55, deg: -35}],
    trace_badge: "Smooth Staircase (35° Steps)"
  },
  crossfire: {
    id: "crossfire",
    num: "03",
    chapter: "ch1",
    title: "Doorway Crossfire (M11)",
    tag: "FEW ≠ SAFE",
    provenance: "CANONICAL PCG MODULE",
    what_changed: "Low threat count (2 targets) is fatal because both unocclude simultaneously at 150° separation, causing lethal reticle slew delay.",
    k_static: 2,
    margin_tics: -4,
    margin_ms: -114.3,
    l_star_ms: null,
    verdict: "UNSERVICEABLE",
    threats: [
      {id: "T1", x: 380, y: 45, angle: 75, reveal_tic: 18, deadline_tic: 32},
      {id: "T2", x: 380, y: 175, angle: -75, reveal_tic: 18, deadline_tic: 32}
    ],
    obstacles: [
      {x: 180, y: 10, w: 25, h: 65},
      {x: 180, y: 145, w: 25, h: 65}
    ],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 0}, {t: 18, deg: 75}, {t: 33, deg: -75}, {t: 55, deg: -75}],
    trace_badge: "Violent 150° Thrash (Late)"
  },

  // --- CHAPTER 2: STATE & TRAJECTORY ---
  route: {
    id: "route",
    num: "04",
    chapter: "ch2",
    title: "Route Choice (F05)",
    tag: "PATH MATTERS",
    provenance: "FROZEN FIXTURE (compiler-certified)",
    what_changed: "The same physical room: entering the direct center creates an unserviceable crossfire (M = -13 tics), while taking the upper flank bypass is safe (M = 0 tics).",
    is_interactive: true,
    interactive_type: "route",
    active_route: "flank",
    direct: {
      k_static: 2,
      margin_tics: -13,
      margin_ms: -371.4,
      l_star_ms: null,
      verdict: "UNSERVICEABLE",
      route: [{x: 30, y: 165}, {x: 430, y: 165}],
      threats: [
        {id: "F05_T1", x: 260, y: 195, angle: -20.6, reveal_tic: 0, deadline_tic: 11},
        {id: "F05_T2", x: 360, y: 135, angle: 7.1, reveal_tic: 0, deadline_tic: 11}
      ],
      heading_pts: [{t: 0, deg: 0}, {t: 5, deg: -20.6}, {t: 18, deg: 7.1}, {t: 40, deg: 7.1}],
      trace_badge: "Dual Concurrent Slew (Infeasible)"
    },
    flank: {
      k_static: 0,
      margin_tics: 0,
      margin_ms: 0.0,
      l_star_ms: 0,
      verdict: "CLEARABLE",
      route: [{x: 30, y: 55}, {x: 430, y: 55}],
      threats: [],
      heading_pts: [{t: 0, deg: 0}, {t: 40, deg: 0}],
      trace_badge: "Isolated Corridor (Zero Exposure)"
    },
    obstacles: [
      {x: 10, y: 95, w: 360, h: 20}
    ]
  },
  wall: {
    id: "wall",
    num: "05",
    chapter: "ch2",
    title: "Move The Wall (F06)",
    tag: "TIMING MATTERS",
    provenance: "FROZEN FIXTURE (compiler-certified sweep)",
    what_changed: "Shifting the partition delays the second unocclusion at 22.2 ms per 10 cm, crossing sharply from failure (x <= 0.85m, gap 244.4ms) to feasibility (x >= 0.90m, gap 255.6ms).",
    is_interactive: true,
    interactive_type: "wall",
    cur_x: 0.85
  },
  tjunction: {
    id: "tjunction",
    num: "06",
    chapter: "ch2",
    title: "The T-Junction Baffle",
    tag: "TOPOLOGY ≠ TIMING",
    provenance: "FPS ARCHETYPE SCHEMATIC",
    what_changed: "Identical topological room: Flush junction reveals left and right arms simultaneously at entrance. Adding a 0.5m baffle delays the right arm by 280ms, converting a fatal trap into sequential clearance.",
    is_interactive: true,
    interactive_type: "tjunction",
    active_state: "baffled",
    flush: {
      k_static: 2,
      margin_tics: -4,
      margin_ms: -114.3,
      l_star_ms: null,
      verdict: "UNSERVICEABLE",
      threats: [
        {id: "Left", x: 100, y: 40, angle: 90, reveal_tic: 10, deadline_tic: 22},
        {id: "Right", x: 360, y: 40, angle: -90, reveal_tic: 10, deadline_tic: 22}
      ],
      obstacles: [
        {x: 10, y: 60, w: 160, h: 20},
        {x: 290, y: 60, w: 160, h: 20}
      ],
      route: [{x: 230, y: 190}, {x: 230, y: 40}],
      heading_pts: [{t: 0, deg: 0}, {t: 10, deg: 90}, {t: 26, deg: -90}, {t: 45, deg: -90}],
      trace_badge: "Simultaneous 180° Split (Fatal)"
    },
    baffled: {
      k_static: 2,
      margin_tics: 6,
      margin_ms: 171.4,
      l_star_ms: 0,
      verdict: "CLEARABLE",
      threats: [
        {id: "Left", x: 100, y: 40, angle: 90, reveal_tic: 10, deadline_tic: 32},
        {id: "Right", x: 360, y: 40, angle: -90, reveal_tic: 20, deadline_tic: 42}
      ],
      obstacles: [
        {x: 10, y: 60, w: 160, h: 20},
        {x: 290, y: 60, w: 160, h: 20},
        {x: 250, y: 60, w: 20, h: 50}
      ],
      route: [{x: 230, y: 190}, {x: 230, y: 40}],
      heading_pts: [{t: 0, deg: 0}, {t: 10, deg: 90}, {t: 22, deg: -90}, {t: 45, deg: -90}],
      trace_badge: "Staggered 280ms Baffle (Safe)"
    }
  },
  entrydir: {
    id: "entrydir",
    num: "07",
    chapter: "ch2",
    title: "Entry Direction",
    tag: "ENTRY STATE MATTERS",
    provenance: "FPS ARCHETYPE SCHEMATIC",
    what_changed: "Approaching from West entry arrives with reticle θ₀ = 0° (favoring Target 1). Approaching from South arrives with θ₀ = +90°, altering rotational latency and target prioritization.",
    is_interactive: true,
    interactive_type: "entrydir",
    active_entry: "west",
    west: {
      k_static: 2,
      margin_tics: 8,
      margin_ms: 228.6,
      l_star_ms: 0,
      verdict: "CLEARABLE",
      threats: [
        {id: "T1", x: 380, y: 70, angle: 25, reveal_tic: 8, deadline_tic: 35},
        {id: "T2", x: 380, y: 160, angle: -35, reveal_tic: 18, deadline_tic: 45}
      ],
      obstacles: [{x: 200, y: 10, w: 20, h: 80}],
      route: [{x: 30, y: 110}, {x: 430, y: 110}],
      heading_pts: [{t: 0, deg: 0}, {t: 8, deg: 25}, {t: 22, deg: -35}, {t: 45, deg: -35}],
      trace_badge: "Aligned Approach (θ₀ = 0°)"
    },
    south: {
      k_static: 2,
      margin_tics: -2,
      margin_ms: -57.1,
      l_star_ms: 57,
      verdict: "UNSERVICEABLE",
      threats: [
        {id: "T1", x: 380, y: 70, angle: -65, reveal_tic: 8, deadline_tic: 24},
        {id: "T2", x: 380, y: 160, angle: -125, reveal_tic: 10, deadline_tic: 26}
      ],
      obstacles: [{x: 200, y: 10, w: 20, h: 80}],
      route: [{x: 230, y: 190}, {x: 230, y: 40}],
      heading_pts: [{t: 0, deg: 90}, {t: 8, deg: -65}, {t: 25, deg: -125}, {t: 45, deg: -125}],
      trace_badge: "Misaligned Slew Deficit (θ₀ = +90°)"
    }
  },

  // --- CHAPTER 3: MAP KNOWLEDGE ---
  knowledge: {
    id: "knowledge",
    num: "08",
    chapter: "ch3",
    title: "Knowledge Rescue (STIM_07)",
    tag: "INFO MATTERS",
    provenance: "FROZEN STIMULUS (35Hz engine-verified)",
    what_changed: "Blind reveal fails (M = -4 tics). Giving 114 ms (ℓ* = 4 tics) of advance warning allows reticle pre-alignment, restoring feasibility (M = 0).",
    k_static: 2,
    margin_tics: -4,
    margin_ms: -114.3,
    l_star_ms: 114.3,
    verdict: "RESCUABLE (114ms)",
    threats: [
      {id: "T1", x: 280, y: 50, angle: 45, reveal_tic: 12, deadline_tic: 28},
      {id: "T2", x: 390, y: 170, angle: -65, reveal_tic: 22, deadline_tic: 38}
    ],
    obstacles: [
      {x: 160, y: 10, w: 25, h: 70},
      {x: 270, y: 140, w: 25, h: 70}
    ],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 45}, {t: 12, deg: 45}, {t: 22, deg: -65}, {t: 45, deg: -65}],
    trace_badge: "Pre-Aim Anticipation (Safe)"
  },
  decoupling: {
    id: "decoupling",
    num: "09",
    chapter: "ch3",
    title: "Same Gain, Different Need",
    tag: "DECOUPLING",
    provenance: "FROZEN STIMULUS (35Hz engine-verified)",
    what_changed: "Both STIM_07 and STIM_11 gain +7 tics from full pre-aim, but STIM_11 needs 50% more advance warning (171 ms vs 114 ms) due to deeper initial deficit.",
    k_static: 2,
    margin_tics: -4,
    margin_ms: -114.3,
    l_star_ms: 114.3,
    verdict: "DECOUPLED (114 vs 171ms)",
    threats: [
      {id: "S07_T", x: 280, y: 50, angle: 45, reveal_tic: 12, deadline_tic: 28},
      {id: "S11_T", x: 390, y: 170, angle: -75, reveal_tic: 12, deadline_tic: 26}
    ],
    obstacles: [
      {x: 170, y: 10, w: 25, h: 70},
      {x: 280, y: 140, w: 25, h: 70}
    ],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 0}, {t: 12, deg: 45}, {t: 25, deg: -75}, {t: 50, deg: -75}],
    trace_badge: "Deficit Dictates Urgency"
  },
  overloaded: {
    id: "overloaded",
    num: "10",
    chapter: "ch3",
    title: "Structurally Overloaded",
    tag: "INFO ISN'T MAGIC",
    provenance: "FROZEN STIMULUS (35Hz engine-verified)",
    what_changed: "Mechanically flawed layout: reaction speed and reticle slew requirements physically exceed capacity. Omniscient pre-aim still fails (M = -10 tics).",
    k_static: 2,
    margin_tics: -10,
    margin_ms: -285.7,
    l_star_ms: null,
    verdict: "OVERLOADED (ℓ* = ∞)",
    threats: [
      {id: "T1", x: 380, y: 40, angle: 85, reveal_tic: 15, deadline_tic: 23},
      {id: "T2", x: 380, y: 180, angle: -85, reveal_tic: 15, deadline_tic: 23}
    ],
    obstacles: [
      {x: 180, y: 10, w: 25, h: 75},
      {x: 180, y: 135, w: 25, h: 75}
    ],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 85}, {t: 15, deg: 85}, {t: 32, deg: -85}, {t: 50, deg: -85}],
    trace_badge: "Capacity Saturated"
  },

  // --- CHAPTER 4: COMPOSITION & TAXONOMY ---
  seam: {
    id: "seam",
    num: "11",
    chapter: "ch4",
    title: "Modular Seam Leakage",
    tag: "SEAM LEAKAGE",
    provenance: "PCG COMPOSITION CONTRACT",
    what_changed: "Two individually safe modules [A] + [B] fail when joined naively because an open sightline leaks across the seam. Adding a certified quiescent baffle interface isolates sightlines and guarantees composition.",
    is_interactive: true,
    interactive_type: "seam",
    active_seam: "certified",
    naive: {
      k_static: 2,
      margin_tics: -5,
      margin_ms: -142.9,
      l_star_ms: null,
      verdict: "UNSERVICEABLE",
      threats: [
        {id: "ModA_T", x: 160, y: 45, angle: 45, reveal_tic: 8, deadline_tic: 22},
        {id: "ModB_T", x: 390, y: 175, angle: -45, reveal_tic: 8, deadline_tic: 22}
      ],
      obstacles: [
        {x: 100, y: 10, w: 20, h: 60},
        {x: 320, y: 150, w: 20, h: 60}
      ],
      route: [{x: 30, y: 110}, {x: 430, y: 110}],
      heading_pts: [{t: 0, deg: 0}, {t: 8, deg: 45}, {t: 24, deg: -45}, {t: 45, deg: -45}],
      trace_badge: "Cross-Module Sightline Leak (Fail)"
    },
    certified: {
      k_static: 2,
      margin_tics: 12,
      margin_ms: 342.9,
      l_star_ms: 0,
      verdict: "CLEARABLE",
      threats: [
        {id: "ModA_T", x: 160, y: 45, angle: 45, reveal_tic: 8, deadline_tic: 32},
        {id: "ModB_T", x: 390, y: 175, angle: -45, reveal_tic: 28, deadline_tic: 52}
      ],
      obstacles: [
        {x: 100, y: 10, w: 20, h: 60},
        {x: 215, y: 50, w: 30, h: 120},
        {x: 320, y: 150, w: 20, h: 60}
      ],
      route: [{x: 30, y: 110}, {x: 430, y: 110}],
      heading_pts: [{t: 0, deg: 0}, {t: 8, deg: 45}, {t: 22, deg: 0}, {t: 28, deg: -45}, {t: 45, deg: -45}],
      trace_badge: "Quiescent Baffle Reset (Safe)"
    }
  },
  classes: {
    id: "classes",
    num: "12",
    chapter: "ch4",
    title: "The Three Epistemic Classes",
    tag: "TAXONOMY",
    provenance: "ACTIONABILITY TAXONOMY",
    what_changed: "For a fixed route and player model, every evaluated encounter falls into one of three epistemic classes: Blind-Clearable (ℓ* = 0ms), Knowledge-Rescuable (0 < ℓ* < ∞), or Structurally Overloaded (ℓ* = ∞).",
    k_static: "1 — 3",
    margin_tics: "+ / -",
    margin_ms: "+ / -",
    l_star_ms: "0 to ∞",
    verdict: "3 CANONICAL REGIMES",
    threats: [
      {id: "Blind", x: 220, y: 55, angle: 30, reveal_tic: 8, deadline_tic: 35},
      {id: "Rescue", x: 320, y: 110, angle: 0, reveal_tic: 18, deadline_tic: 32},
      {id: "Overload", x: 400, y: 165, angle: -75, reveal_tic: 18, deadline_tic: 25}
    ],
    obstacles: [
      {x: 140, y: 10, w: 25, h: 65},
      {x: 250, y: 145, w: 25, h: 65}
    ],
    route: [{x: 30, y: 110}, {x: 430, y: 110}],
    heading_pts: [{t: 0, deg: 30}, {t: 12, deg: 0}, {t: 25, deg: -75}, {t: 50, deg: -75}],
    trace_badge: "Epistemic Hierarchy"
  }
};

let activeAtlasCardKey = "corridor";

function initAtlas() {
  // Chapter Filter Tabs
  const tabBtns = document.querySelectorAll(".atlas-tab-btn");
  const navCards = document.querySelectorAll(".atlas-nav-card");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const ch = btn.getAttribute("data-chapter");

      navCards.forEach(c => {
        if (ch === "all" || c.getAttribute("data-ch") === ch) {
          c.style.display = "flex";
        } else {
          c.style.display = "none";
        }
      });
    });
  });

  navCards.forEach(card => {
    card.addEventListener("click", () => {
      navCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      activeAtlasCardKey = card.getAttribute("data-card");
      updateAtlasViewer();
    });
  });

  // Card 04: Route toggle buttons
  const btnDirect = document.getElementById("btn-route-direct");
  const btnFlank = document.getElementById("btn-route-flank");
  if (btnDirect && btnFlank) {
    btnDirect.addEventListener("click", () => {
      ATLAS_DATA.route.active_route = "direct";
      btnDirect.className = "btn btn-sm btn-primary";
      btnFlank.className = "btn btn-sm";
      updateAtlasViewer();
    });
    btnFlank.addEventListener("click", () => {
      ATLAS_DATA.route.active_route = "flank";
      btnFlank.className = "btn btn-sm btn-primary";
      btnDirect.className = "btn btn-sm";
      updateAtlasViewer();
    });
  }

  // Card 05: Wall slider
  const wallSlider = document.getElementById("slider-atlas-wall");
  if (wallSlider) {
    wallSlider.addEventListener("input", (e) => {
      ATLAS_DATA.wall.cur_x = parseFloat(e.target.value);
      updateAtlasViewer();
    });
  }

  // Card 06: T-Junction toggle
  const btnTFlush = document.getElementById("btn-tjunc-flush");
  const btnTBaffled = document.getElementById("btn-tjunc-baffled");
  if (btnTFlush && btnTBaffled) {
    btnTFlush.addEventListener("click", () => {
      ATLAS_DATA.tjunction.active_state = "flush";
      btnTFlush.className = "btn btn-sm btn-primary";
      btnTBaffled.className = "btn btn-sm";
      updateAtlasViewer();
    });
    btnTBaffled.addEventListener("click", () => {
      ATLAS_DATA.tjunction.active_state = "baffled";
      btnTBaffled.className = "btn btn-sm btn-primary";
      btnTFlush.className = "btn btn-sm";
      updateAtlasViewer();
    });
  }

  // Card 07: Entry Direction toggle
  const btnEntryWest = document.getElementById("btn-entry-west");
  const btnEntrySouth = document.getElementById("btn-entry-south");
  if (btnEntryWest && btnEntrySouth) {
    btnEntryWest.addEventListener("click", () => {
      ATLAS_DATA.entrydir.active_entry = "west";
      btnEntryWest.className = "btn btn-sm btn-primary";
      btnEntrySouth.className = "btn btn-sm";
      updateAtlasViewer();
    });
    btnEntrySouth.addEventListener("click", () => {
      ATLAS_DATA.entrydir.active_entry = "south";
      btnEntrySouth.className = "btn btn-sm btn-primary";
      btnEntryWest.className = "btn btn-sm";
      updateAtlasViewer();
    });
  }

  // Card 11: Modular Seam toggle
  const btnSeamNaive = document.getElementById("btn-seam-naive");
  const btnSeamCert = document.getElementById("btn-seam-certified");
  if (btnSeamNaive && btnSeamCert) {
    btnSeamNaive.addEventListener("click", () => {
      ATLAS_DATA.seam.active_seam = "naive";
      btnSeamNaive.className = "btn btn-sm btn-primary";
      btnSeamCert.className = "btn btn-sm";
      updateAtlasViewer();
    });
    btnSeamCert.addEventListener("click", () => {
      ATLAS_DATA.seam.active_seam = "certified";
      btnSeamCert.className = "btn btn-sm btn-primary";
      btnSeamNaive.className = "btn btn-sm";
      updateAtlasViewer();
    });
  }

  updateAtlasViewer();
}

function updateAtlasViewer() {
  const card = ATLAS_DATA[activeAtlasCardKey];
  if (!card) return;

  // Title, Tag & Provenance
  document.getElementById("atlas-active-title").textContent = `${card.num} · ${card.title}`;
  document.getElementById("atlas-active-tag").textContent = card.tag;
  document.getElementById("atlas-active-prov").textContent = card.provenance || "CANONICAL FIXTURE";
  document.getElementById("atlas-contrast-text").textContent = card.what_changed;

  const intBar = document.getElementById("atlas-interactive-bar");
  const ctrlRoute = document.getElementById("ctrl-route-toggle");
  const ctrlWall = document.getElementById("ctrl-wall-slider");
  const ctrlTJunc = document.getElementById("ctrl-tjunction-toggle");
  const ctrlEntry = document.getElementById("ctrl-entry-toggle");
  const ctrlSeam = document.getElementById("ctrl-seam-toggle");

  intBar.style.display = card.is_interactive ? "block" : "none";
  ctrlRoute.style.display = card.interactive_type === "route" ? "flex" : "none";
  ctrlWall.style.display = card.interactive_type === "wall" ? "flex" : "none";
  ctrlTJunc.style.display = card.interactive_type === "tjunction" ? "flex" : "none";
  ctrlEntry.style.display = card.interactive_type === "entrydir" ? "flex" : "none";
  ctrlSeam.style.display = card.interactive_type === "seam" ? "flex" : "none";

  let displayK = card.k_static !== undefined ? card.k_static : 1;
  let displayMargin = typeof card.margin_tics === "number" ? `${card.margin_tics > 0 ? "+" : ""}${card.margin_tics} tics (${card.margin_ms > 0 ? "+" : ""}${card.margin_ms.toFixed(1)} ms)` : (card.margin_tics || "0 tics");
  let displayLStar = card.l_star_ms !== null && card.l_star_ms !== undefined ? (typeof card.l_star_ms === "number" ? `ℓ* = ${card.l_star_ms.toFixed(0)} ms` : card.l_star_ms) : "ℓ* = ∞";
  let displayVerdict = card.verdict || "CLEARABLE";
  let verdictClass = "status-pass";

  let mapData = card;
  let timelineData = card.threats || [];
  let headingPts = card.heading_pts || [];
  let traceBadge = card.trace_badge || "Angular Trace";

  // Dynamic overrides for Card 04 (Route Choice)
  if (card.interactive_type === "route") {
    const rData = card[card.active_route] || card.flank;
    displayK = `K_static = ${rData.k_static}`;
    displayMargin = `${rData.margin_tics > 0 ? "+" : ""}${rData.margin_tics} tics (${rData.margin_ms > 0 ? "+" : ""}${rData.margin_ms.toFixed(1)} ms)`;
    displayLStar = rData.l_star_ms !== null ? `ℓ* = ${rData.l_star_ms} ms` : "ℓ* = ∞";
    displayVerdict = rData.verdict;

    mapData = {
      obstacles: card.obstacles,
      route: rData.route,
      threats: rData.threats
    };
    timelineData = rData.threats;
    headingPts = rData.heading_pts;
    traceBadge = rData.trace_badge;
  }

  // Dynamic overrides for Card 05 (Move the Wall - Grounded in exact compiler sweep)
  if (card.interactive_type === "wall") {
    const wxKey = (card.cur_x || 0.85).toFixed(2);
    const sweepData = (ATLAS_FIXTURES.f06 && ATLAS_FIXTURES.f06[wxKey]) ? ATLAS_FIXTURES.f06[wxKey] : {
      wall_x_m: 0.85,
      reveal_gap_ms: 244.4,
      reveal_gap_tics: 9,
      tactical_margin_tics: -1,
      tactical_margin_ms: -28.6,
      l_star_ms: 57,
      is_feasible: false
    };

    document.getElementById("wall-pos-val").textContent = `${sweepData.wall_x_m.toFixed(2)} m`;
    document.getElementById("wall-gap-val").textContent = `${sweepData.reveal_gap_ms.toFixed(1)} ms (${sweepData.reveal_gap_tics} tics)`;

    const tag = document.getElementById("wall-status-tag");
    if (sweepData.is_feasible) {
      tag.textContent = `CLEARABLE (M = +${sweepData.tactical_margin_tics} tics)`;
      tag.className = "wall-verdict-tag tag-pass";
      displayVerdict = "CLEARABLE";
    } else if (sweepData.wall_x_m === 0.85) {
      tag.textContent = "FEASIBILITY BOUNDARY (M = -1 tic)";
      tag.className = "wall-verdict-tag tag-warn";
      displayVerdict = "BOUNDARY (M = -1t)";
    } else {
      tag.textContent = `UNSERVICEABLE (M = ${sweepData.tactical_margin_tics} tics)`;
      tag.className = "wall-verdict-tag tag-fail";
      displayVerdict = "UNSERVICEABLE";
    }

    displayK = "K_static = 2";
    displayMargin = `${sweepData.tactical_margin_tics > 0 ? "+" : ""}${sweepData.tactical_margin_tics} tics (${sweepData.tactical_margin_ms > 0 ? "+" : ""}${sweepData.tactical_margin_ms.toFixed(1)} ms)`;
    displayLStar = sweepData.l_star_ms !== null ? `ℓ* = ${sweepData.l_star_ms} ms` : "ℓ* = ∞";

    const obsWallX = 140 + ((sweepData.wall_x_m - 0.70) / 0.30) * 120;
    mapData = {
      obstacles: [{x: obsWallX, y: 10, w: 25, h: 75}],
      route: [{x: 30, y: 110}, {x: 430, y: 110}],
      threats: [
        {id: "F06_T1", x: 250, y: 175, angle: -14.0, reveal_tic: 0, deadline_tic: 11},
        {id: "F06_T2", x: obsWallX + 80, y: 45, angle: 63.4, reveal_tic: sweepData.reveal_gap_tics, deadline_tic: sweepData.reveal_gap_tics + 11}
      ]
    };
    timelineData = mapData.threats;
    const r2T = sweepData.reveal_gap_tics;
    headingPts = [
      {t: 0, deg: 0},
      {t: 4, deg: -14},
      {t: Math.min(45, Math.max(12, r2T + 4)), deg: 63.4},
      {t: 50, deg: 63.4}
    ];
    traceBadge = sweepData.is_feasible ? "Sequential Sweep (Clearable)" : "Overlapping Slew (Infeasible)";
  }

  // Dynamic overrides for Card 06 (T-Junction Baffle)
  if (card.interactive_type === "tjunction") {
    const tjData = card[card.active_state] || card.baffled;
    displayK = `K_static = ${tjData.k_static}`;
    displayMargin = `${tjData.margin_tics > 0 ? "+" : ""}${tjData.margin_tics} tics (${tjData.margin_ms > 0 ? "+" : ""}${tjData.margin_ms.toFixed(1)} ms)`;
    displayLStar = tjData.l_star_ms !== null ? `ℓ* = ${tjData.l_star_ms} ms` : "ℓ* = ∞";
    displayVerdict = tjData.verdict;

    mapData = {
      obstacles: tjData.obstacles,
      route: tjData.route,
      threats: tjData.threats
    };
    timelineData = tjData.threats;
    headingPts = tjData.heading_pts;
    traceBadge = tjData.trace_badge;
  }

  // Dynamic overrides for Card 07 (Entry Direction)
  if (card.interactive_type === "entrydir") {
    const eData = card[card.active_entry] || card.west;
    displayK = `K_static = ${eData.k_static}`;
    displayMargin = `${eData.margin_tics > 0 ? "+" : ""}${eData.margin_tics} tics (${eData.margin_ms > 0 ? "+" : ""}${eData.margin_ms.toFixed(1)} ms)`;
    displayLStar = eData.l_star_ms !== null ? `ℓ* = ${eData.l_star_ms} ms` : "ℓ* = ∞";
    displayVerdict = eData.verdict;

    mapData = {
      obstacles: eData.obstacles,
      route: eData.route,
      threats: eData.threats
    };
    timelineData = eData.threats;
    headingPts = eData.heading_pts;
    traceBadge = eData.trace_badge;
  }

  // Dynamic overrides for Card 11 (Modular Seam)
  if (card.interactive_type === "seam") {
    const sData = card[card.active_seam] || card.certified;
    displayK = `K_static = ${sData.k_static}`;
    displayMargin = `${sData.margin_tics > 0 ? "+" : ""}${sData.margin_tics} tics (${sData.margin_ms > 0 ? "+" : ""}${sData.margin_ms.toFixed(1)} ms)`;
    displayLStar = sData.l_star_ms !== null ? `ℓ* = ${sData.l_star_ms} ms` : "ℓ* = ∞";
    displayVerdict = sData.verdict;

    mapData = {
      obstacles: sData.obstacles,
      route: sData.route,
      threats: sData.threats
    };
    timelineData = sData.threats;
    headingPts = sData.heading_pts;
    traceBadge = sData.trace_badge;
  }

  verdictClass = displayVerdict.includes("CLEARABLE") || displayVerdict.includes("RESCUABLE") ? "status-pass" : (displayVerdict.includes("UNSERVICEABLE") || displayVerdict.includes("OVERLOADED") ? "status-fail" : "status-warn");

  // Update Metric Chips
  document.getElementById("atlas-val-k").textContent = typeof displayK === "number" ? `K_static = ${displayK}` : displayK;
  document.getElementById("atlas-val-margin").textContent = displayMargin;
  document.getElementById("atlas-val-lstar").textContent = displayLStar;
  const verdElem = document.getElementById("atlas-val-verdict");
  verdElem.textContent = displayVerdict;
  verdElem.className = `m-val ${verdictClass}`;

  document.getElementById("atlas-trace-badge").textContent = traceBadge;

  // Render 3 Visuals
  renderAtlasMapSVG(mapData);
  renderAtlasTimelineDOM(timelineData);
  renderAtlasHeadingTraceSVG(headingPts, verdictClass);
}

function renderAtlasMapSVG(data) {
  const svg = document.getElementById("svg-atlas-map");
  if (!svg) return;
  svg.innerHTML = "";

  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", 5); bg.setAttribute("y", 5);
  bg.setAttribute("width", 450); bg.setAttribute("height", 210);
  bg.setAttribute("fill", "#0d1117"); bg.setAttribute("stroke", "#30363d"); bg.setAttribute("stroke-width", "1.5");
  bg.setAttribute("rx", 6);
  svg.appendChild(bg);

  // Obstacles
  (data.obstacles || []).forEach(o => {
    const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    r.setAttribute("x", o.x); r.setAttribute("y", o.y);
    r.setAttribute("width", o.w); r.setAttribute("height", o.h);
    r.setAttribute("fill", "#21262d"); r.setAttribute("stroke", "#58a6ff"); r.setAttribute("stroke-width", "1.2");
    r.setAttribute("rx", 3);
    svg.appendChild(r);
  });

  // Route
  if (data.route && data.route.length >= 2) {
    const rLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    rLine.setAttribute("x1", data.route[0].x); rLine.setAttribute("y1", data.route[0].y);
    rLine.setAttribute("x2", data.route[1].x); rLine.setAttribute("y2", data.route[1].y);
    rLine.setAttribute("stroke", "rgba(88, 166, 255, 0.4)"); rLine.setAttribute("stroke-dasharray", "4,4"); rLine.setAttribute("stroke-width", "2");
    svg.appendChild(rLine);

    const px = data.route[0].x + 80;
    const py = data.route[0].y;
    const pDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    pDot.setAttribute("cx", px); pDot.setAttribute("cy", py);
    pDot.setAttribute("r", 6); pDot.setAttribute("fill", "#58a6ff"); pDot.setAttribute("stroke", "#fff"); pDot.setAttribute("stroke-width", "2");
    svg.appendChild(pDot);

    // Unocclusion rays
    (data.threats || []).forEach(t => {
      const ray = document.createElementNS("http://www.w3.org/2000/svg", "line");
      ray.setAttribute("x1", px); ray.setAttribute("y1", py);
      ray.setAttribute("x2", t.x); ray.setAttribute("y2", t.y);
      ray.setAttribute("stroke", "rgba(88, 166, 255, 0.5)"); ray.setAttribute("stroke-width", "1.5");
      svg.appendChild(ray);
    });
  }

  // Threats
  (data.threats || []).forEach(t => {
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", t.x - 9); rect.setAttribute("y", t.y - 9);
    rect.setAttribute("width", 18); rect.setAttribute("height", 18);
    rect.setAttribute("fill", "#f85149"); rect.setAttribute("stroke", "#fff"); rect.setAttribute("stroke-width", "1.5"); rect.setAttribute("rx", 3);
    svg.appendChild(rect);

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", t.x); txt.setAttribute("y", t.y + 4);
    txt.setAttribute("fill", "#fff"); txt.setAttribute("font-size", "9px"); txt.setAttribute("font-weight", "bold");
    txt.setAttribute("text-anchor", "middle");
    txt.textContent = t.id;
    svg.appendChild(txt);
  });
}

function renderAtlasTimelineDOM(threats) {
  const container = document.getElementById("atlas-timeline-container");
  if (!container) return;
  container.innerHTML = "";

  if (!threats || threats.length === 0) {
    container.innerHTML = '<div style="color: #8b949e; font-size: 11px; text-align: center; padding: 20px;">Zero hostile exposure along this corridor traversal.</div>';
    return;
  }

  const totalTics = 60;
  threats.forEach(t => {
    const rTic = t.reveal_tic || 10;
    const dTic = t.deadline_tic || 35;
    const rotWidth = 8;
    const acqWidth = 10;
    const srvWidth = 8;

    const rPct = (rTic / totalTics) * 100;
    const dPct = (dTic / totalTics) * 100;

    const row = document.createElement("div");
    row.className = "t-row";
    row.innerHTML = `
      <div class="t-lbl">${t.id} (${t.angle > 0 ? "+" : ""}${t.angle || 0}°)</div>
      <div class="t-track">
        <div class="t-block t-block-rot" style="left: ${rPct}%; width: ${rotWidth}%;" title="Reticle Slew"></div>
        <div class="t-block t-block-acq" style="left: ${rPct + rotWidth}%; width: ${acqWidth}%;" title="Acquisition"></div>
        <div class="t-block t-block-srv" style="left: ${rPct + rotWidth + acqWidth}%; width: ${srvWidth}%;" title="Weapon Service"></div>
        <div class="t-bar-deadline" style="left: ${dPct}%;" title="Hostile Deadline"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderAtlasHeadingTraceSVG(headingPts, verdictClass) {
  const svg = document.getElementById("svg-atlas-heading");
  if (!svg) return;
  svg.innerHTML = "";

  const padLeft = 40, padRight = 20, padTop = 20, padBottom = 30;
  const w = 460 - padLeft - padRight;
  const h = 220 - padTop - padBottom;

  const minDeg = -90, maxDeg = +90;
  const maxT = 60;

  function xPos(t) { return padLeft + (t / maxT) * w; }
  function yPos(deg) { return padTop + h - ((deg - minDeg) / (maxDeg - minDeg)) * h; }

  // Zero heading line
  const zeroY = yPos(0);
  const zLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
  zLine.setAttribute("x1", padLeft); zLine.setAttribute("y1", zeroY);
  zLine.setAttribute("x2", padLeft + w); zLine.setAttribute("y2", zeroY);
  zLine.setAttribute("stroke", "#30363d"); zLine.setAttribute("stroke-dasharray", "3,3");
  svg.appendChild(zLine);

  const zTxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
  zTxt.setAttribute("x", padLeft - 6); zTxt.setAttribute("y", zeroY + 4);
  zTxt.setAttribute("fill", "#8b949e"); zTxt.setAttribute("font-size", "10px"); zTxt.setAttribute("text-anchor", "end");
  zTxt.textContent = "0°";
  svg.appendChild(zTxt);

  const p90Txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
  p90Txt.setAttribute("x", padLeft - 6); p90Txt.setAttribute("y", yPos(90) + 4);
  p90Txt.setAttribute("fill", "#8b949e"); p90Txt.setAttribute("font-size", "10px"); p90Txt.setAttribute("text-anchor", "end");
  p90Txt.textContent = "+90°";
  svg.appendChild(p90Txt);

  const m90Txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
  m90Txt.setAttribute("x", padLeft - 6); m90Txt.setAttribute("y", yPos(-90) + 4);
  m90Txt.setAttribute("fill", "#8b949e"); m90Txt.setAttribute("font-size", "10px"); m90Txt.setAttribute("text-anchor", "end");
  m90Txt.textContent = "-90°";
  svg.appendChild(m90Txt);

  const lineColor = verdictClass === "status-pass" ? "#3fb950" : (verdictClass === "status-fail" ? "#f85149" : "#d29922");

  if (headingPts && headingPts.length >= 2) {
    const polyPts = headingPts.map(pt => `${xPos(pt.t)},${yPos(pt.deg)}`).join(" ");
    const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    line.setAttribute("points", polyPts);
    line.setAttribute("fill", "none");
    line.setAttribute("stroke", lineColor);
    line.setAttribute("stroke-width", "2.5");
    svg.appendChild(line);

    headingPts.forEach(pt => {
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("cx", xPos(pt.t)); dot.setAttribute("cy", yPos(pt.deg));
      dot.setAttribute("r", 4); dot.setAttribute("fill", lineColor); dot.setAttribute("stroke", "#fff");
      svg.appendChild(dot);
    });
  }

  for (let t = 0; t <= maxT; t += 20) {
    const tx = xPos(t);
    const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lbl.setAttribute("x", tx); lbl.setAttribute("y", padTop + h + 18);
    lbl.setAttribute("fill", "#8b949e"); lbl.setAttribute("font-size", "10px");
    lbl.setAttribute("text-anchor", "middle");
    lbl.textContent = `${t} tics`;
    svg.appendChild(lbl);
  }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initTwoRooms();
  initPipeline();
  initKnowledgeSlider();
  initDecouplingView();
  initAtlas();
});
