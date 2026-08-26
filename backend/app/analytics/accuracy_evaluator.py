import numpy as np
import pandas as pd

def evaluate_accuracy_and_reliability(predicted_positions: list, actual_positions: list) -> dict:
    """
    ကွန်ပျူတာ၏ SGP4 ခန့်မှန်းချက် (Prediction) နှင့် မြေပြင် တကယ့် တိုင်းတာချက် (Actual) များကို
    တိုက်ဆိုင် စစ်ဆေး၍ RMSE (Root Mean Square Error) နှင့် Reliability ကို တွက်ချက်ပေးသည်။
    """
    if not predicted_positions or not actual_positions:
        return {"error": "Insufficient data for accuracy evaluation."}

    pred_arr = np.array(predicted_positions)
    act_arr = np.array(actual_positions)

    # Position Error (Euclidean Distance in degrees, multiplied by approx meters per degree)
    errors = np.sqrt(np.sum((pred_arr - act_arr) ** 2, axis=1))

    # RMSE တွက်ချက်ခြင်း
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    mean_error = float(np.mean(errors))
    max_error = float(np.max(errors))

    # Reliability စစ်ဆေးခြင်း (Error က 5.0 မီတာ အောက် နည်းလျှင် ယုံကြည်ရမှု မြင့်သည် ဟု ယူဆရန်)
    # Approx 1 degree = 111320 meters, so 5 meters is approx 0.000045 degrees
    threshold = 5.0 / 111320 
    reliability_score = float(np.sum(errors < threshold) / len(errors) * 100)

    return {
        "status": "success",
        "metrics": {
            "rmse_meters": round(rmse * 111320, 2),  # Convert to meters approximately
            "mean_error_meters": round(mean_error * 111320, 2),
            "max_error_meters": round(max_error * 111320, 2),
            "reliability_percentage": round(reliability_score, 2)
        },
        "evaluation": "Reliable" if reliability_score >= 80.0 else "Degraded Accuracy"
    }