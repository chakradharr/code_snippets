import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

def get_classification_metrics(y_true, y_pred, y_proba=None):
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='binary'),  # PPV
        'recall': recall_score(y_true, y_pred, average='binary'),  # Sensitivity
        'f1_score': f1_score(y_true, y_pred, average='binary'),
        'specificity': tn / (tn + fp) if (tn + fp) > 0 else 0,
        'npv': tn / (tn + fn) if (tn + fn) > 0 else 0,  # NPV
        'ppv': tp / (tp + fp) if (tp + fp) > 0 else 0,  # PPV
        'tn': tn,
        'fp': fp,
        'fn': fn,
        'tp': tp
    }
    
    if y_proba is not None:
        metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
        
        # Calculate lift
        # Assuming the positive class is represented by 1
        positive_class_proba = y_proba[y_true == 1]
        if len(positive_class_proba) > 0:
            metrics['lift'] = positive_class_proba.mean() / (y_true.mean())
        else:
            metrics['lift'] = 0
    else:
        metrics['lift'] = None

    return metrics

def evaluate_sub_segments(df, segment_column, true_label_column, pred_label_column, proba_column=None):
    sub_segments = df[segment_column].unique()
    rows = []

    for segment in sub_segments:
        sub_segment_df = df[df[segment_column] == segment]
        y_true = sub_segment_df[true_label_column]
        y_pred = sub_segment_df[pred_label_column]
        y_proba = sub_segment_df[proba_column] if proba_column else None

        metrics = get_classification_metrics(y_true, y_pred, y_proba)
        metrics['segment'] = segment
        rows.append(metrics)
    
    metrics_df = pd.DataFrame(rows)
    return metrics_df

# Example usage
# Assuming you have a DataFrame `df` with the necessary columns:
# df = pd.read_csv('your_data.csv')
# 'segment' is the column with sub-segments
# 'true_label' is the column with the true labels
# 'pred_label' is the column with the predicted labels
# 'proba' is the column with predicted probabilities (if available)

segment_metrics_df = evaluate_sub_segments(df, segment_column='segment', true_label_column='true_label', pred_label_column='pred_label', proba_column='proba')

# Display the DataFrame with metrics for each sub-segment
print(segment_metrics_df)
