import matplotlib.pyplot as plt

# ---------- ВСПОМОГАТЕЛЬНОЕ ----------
def extract_xy(results_block):
    """
    results_block: список словарей (точки одной кривой)
    Возвращает X=cam_detect_prob, Y=total_prob
    """
    x = [p["cam_detect_prob"] for p in results_block]
    y = [p["total_prob"] for p in results_block]
    return x, y


# ---------- ДАННЫЕ ----------
# ВАЖНО: сюда вставь ровно список словарей из твоего JSON:
# "Results": [ [ {..}, {..}, ... ] ]
# то есть возьми inner list: Results[0][0]

results_23 = [
      {
        "cam_detect_prob": 1.0,
        "rfid_detect_without_collision_prob": 0.0,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 1.0,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9789633333333333,
        "rfid_detect_without_collision_prob": 0.00548,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9844433333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9582833333333334,
        "rfid_detect_without_collision_prob": 0.011343333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9696266666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9377633333333333,
        "rfid_detect_without_collision_prob": 0.01668,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9544433333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9165933333333334,
        "rfid_detect_without_collision_prob": 0.022233333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9388266666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8961166666666667,
        "rfid_detect_without_collision_prob": 0.02843,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9245466666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.87518,
        "rfid_detect_without_collision_prob": 0.03297666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9081566666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8542366666666666,
        "rfid_detect_without_collision_prob": 0.038283333333333336,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.89252,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.83298,
        "rfid_detect_without_collision_prob": 0.04475333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8777333333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8125533333333333,
        "rfid_detect_without_collision_prob": 0.049433333333333336,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8619866666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7915733333333334,
        "rfid_detect_without_collision_prob": 0.056516666666666666,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.84809,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.77069,
        "rfid_detect_without_collision_prob": 0.06127666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8319666666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7507866666666667,
        "rfid_detect_without_collision_prob": 0.06671666666666666,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8175033333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.72682,
        "rfid_detect_without_collision_prob": 0.07336333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8001833333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7084666666666667,
        "rfid_detect_without_collision_prob": 0.07795,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7864166666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6873333333333334,
        "rfid_detect_without_collision_prob": 0.08346333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7707966666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.66667,
        "rfid_detect_without_collision_prob": 0.08884333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7555133333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6450966666666667,
        "rfid_detect_without_collision_prob": 0.09515,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7402466666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6266,
        "rfid_detect_without_collision_prob": 0.10088666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7274866666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6034233333333333,
        "rfid_detect_without_collision_prob": 0.10634666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.70977,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.58396,
        "rfid_detect_without_collision_prob": 0.11164666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.6956066666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5619066666666667,
        "rfid_detect_without_collision_prob": 0.11770333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.67961,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5418566666666667,
        "rfid_detect_without_collision_prob": 0.12272666666666666,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.6645833333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.51908,
        "rfid_detect_without_collision_prob": 0.12881,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.64789,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.50082,
        "rfid_detect_without_collision_prob": 0.13313,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.63395,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      }
]

results_12 = [
      {
        "cam_detect_prob": 1.0,
        "rfid_detect_without_collision_prob": 0.0,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 1.0,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9789433333333334,
        "rfid_detect_without_collision_prob": 0.008553333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9874966666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9581933333333333,
        "rfid_detect_without_collision_prob": 0.016833333333333332,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9750266666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9386833333333333,
        "rfid_detect_without_collision_prob": 0.02448,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9631633333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9152666666666667,
        "rfid_detect_without_collision_prob": 0.03388666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9491533333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8957166666666667,
        "rfid_detect_without_collision_prob": 0.042236666666666665,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9379533333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8746233333333333,
        "rfid_detect_without_collision_prob": 0.05041,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9250333333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8544766666666667,
        "rfid_detect_without_collision_prob": 0.058673333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.91315,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8329266666666667,
        "rfid_detect_without_collision_prob": 0.06729,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9002166666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.81317,
        "rfid_detect_without_collision_prob": 0.07599666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8891666666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7923133333333333,
        "rfid_detect_without_collision_prob": 0.08405333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8763666666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.76966,
        "rfid_detect_without_collision_prob": 0.09388333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8635433333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7508966666666667,
        "rfid_detect_without_collision_prob": 0.10093333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.85183,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7294333333333334,
        "rfid_detect_without_collision_prob": 0.10965,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8390833333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7074566666666666,
        "rfid_detect_without_collision_prob": 0.11761333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.82507,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.68646,
        "rfid_detect_without_collision_prob": 0.12699666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8134566666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6671233333333333,
        "rfid_detect_without_collision_prob": 0.13426,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8013833333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6457233333333333,
        "rfid_detect_without_collision_prob": 0.14325333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7889766666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6254733333333333,
        "rfid_detect_without_collision_prob": 0.15192,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7773933333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6025266666666667,
        "rfid_detect_without_collision_prob": 0.16039333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.76292,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5852866666666666,
        "rfid_detect_without_collision_prob": 0.16733333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.75262,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5616666666666666,
        "rfid_detect_without_collision_prob": 0.17734333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.73901,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.54153,
        "rfid_detect_without_collision_prob": 0.18489333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7264233333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5197133333333334,
        "rfid_detect_without_collision_prob": 0.19427666666666665,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.71399,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.4990366666666667,
        "rfid_detect_without_collision_prob": 0.20224666666666666,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7012833333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      }
]

results_13 = [
      {
        "cam_detect_prob": 1.0,
        "rfid_detect_without_collision_prob": 0.0,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 1.0,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9792066666666667,
        "rfid_detect_without_collision_prob": 0.011073333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.99028,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9584966666666667,
        "rfid_detect_without_collision_prob": 0.022606666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9811033333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9378866666666666,
        "rfid_detect_without_collision_prob": 0.03342666666666667,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9713133333333334,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.9163666666666667,
        "rfid_detect_without_collision_prob": 0.04567,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9620366666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8959933333333333,
        "rfid_detect_without_collision_prob": 0.05649,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9524833333333333,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8749333333333333,
        "rfid_detect_without_collision_prob": 0.06792333333333334,
        "rfid_detect_with_collision_prob": 3.3333333333333333e-06,
        "total_prob": 0.94286,
        "total_collisions": 1,
        "collision_amount_to_nums": 3.3333333333333333e-06,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8548766666666666,
        "rfid_detect_without_collision_prob": 0.07833333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.93321,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.83299,
        "rfid_detect_without_collision_prob": 0.09004,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.92303,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.8112233333333333,
        "rfid_detect_without_collision_prob": 0.10286333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9140866666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7902233333333334,
        "rfid_detect_without_collision_prob": 0.11394333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.9041666666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7713233333333334,
        "rfid_detect_without_collision_prob": 0.12401666666666666,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.89534,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7503433333333334,
        "rfid_detect_without_collision_prob": 0.13583333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8861766666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7285233333333333,
        "rfid_detect_without_collision_prob": 0.14713333333333334,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8756566666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.7077633333333333,
        "rfid_detect_without_collision_prob": 0.15836333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8661266666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6867833333333333,
        "rfid_detect_without_collision_prob": 0.16971666666666665,
        "rfid_detect_with_collision_prob": 3.3333333333333333e-06,
        "total_prob": 0.8565033333333333,
        "total_collisions": 1,
        "collision_amount_to_nums": 3.3333333333333333e-06,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.66803,
        "rfid_detect_without_collision_prob": 0.17996666666666666,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8479966666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.6446033333333333,
        "rfid_detect_without_collision_prob": 0.19323,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8378333333333333,
        "total_collisions": 1,
        "collision_amount_to_nums": 3.3333333333333333e-06,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 3.3333333333333333e-06
      },
      {
        "cam_detect_prob": 0.6245266666666667,
        "rfid_detect_without_collision_prob": 0.20382333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.82835,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.60399,
        "rfid_detect_without_collision_prob": 0.21417666666666665,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.8181666666666667,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.58331,
        "rfid_detect_without_collision_prob": 0.22617,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.80948,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5632933333333333,
        "rfid_detect_without_collision_prob": 0.23632333333333333,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7996166666666666,
        "total_collisions": 0,
        "collision_amount_to_nums": 0.0,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5413066666666667,
        "rfid_detect_without_collision_prob": 0.24908333333333332,
        "rfid_detect_with_collision_prob": 3.3333333333333333e-06,
        "total_prob": 0.7903933333333334,
        "total_collisions": 1,
        "collision_amount_to_nums": 3.3333333333333333e-06,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.5210133333333333,
        "rfid_detect_without_collision_prob": 0.2601266666666667,
        "rfid_detect_with_collision_prob": 3.3333333333333333e-06,
        "total_prob": 0.7811433333333333,
        "total_collisions": 1,
        "collision_amount_to_nums": 3.3333333333333333e-06,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 0.0
      },
      {
        "cam_detect_prob": 0.50001,
        "rfid_detect_without_collision_prob": 0.27082,
        "rfid_detect_with_collision_prob": 0.0,
        "total_prob": 0.7708299999999999,
        "total_collisions": 1,
        "collision_amount_to_nums": 3.3333333333333333e-06,
        "error_collision_resolve_amount": 0.0,
        "unresolved_collision_prob": 3.3333333333333333e-06
      }
]


# ---------- ПОСТРОЕНИЕ ----------
x_23, y_23 = extract_xy(results_23)
x_12, y_12 = extract_xy(results_12)
x_13, y_13 = extract_xy(results_13)

plt.figure(figsize=(10, 6))

plt.plot(x_13, y_13, marker="o", linewidth=2, label="Proportion of license plates with ≥ 4 unrecognized characters 33%")
plt.plot(x_12, y_12, marker="s", linewidth=2,label="Proportion of license plates with ≥ 4 unrecognized characters 50%")
plt.plot(x_23, y_23, marker="^", linewidth=2, label="Proportion of license plates with ≥ 4 unrecognized characters 67%")

plt.xlabel("Probability of successful identification of a vehicle by a camera", fontsize=15)
plt.ylabel("Probability of vehicle identification\nby the HANPR system", fontsize=15)

plt.ylim(0.5, 1.0)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=14)
# plt.title("Вероятность распознавания автомобиля гибридной системой", fontsize=18)

plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

plt.tight_layout()
plt.show()