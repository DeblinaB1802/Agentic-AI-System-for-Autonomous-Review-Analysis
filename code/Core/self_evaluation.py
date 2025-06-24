# Self-Evaluation
import json

def self_evaluate(result, execution_time):
    retry = False
    confidence = result.get('model_confidence', 0.0) 
    if execution_time < 10:
        confidence += 0.1
    elif execution_time > 30:
        confidence -= 0.1
    try:
        json.loads(result)
        confidence += 0.2
    except:
        confidence -= 0.2 
    confidence = max(0.0, min(1.0, confidence))
    if confidence < 0.75:
        retry = True
    return retry