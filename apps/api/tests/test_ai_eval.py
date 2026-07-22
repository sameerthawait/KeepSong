import pytest
from app.ai.classifier import classify_transcript

# Labeled benchmark test dataset of 12 transcripts with ground-truth theme and decade labels
BENCHMARK_DATASET = [
    {
        "id": "sample-01",
        "transcript": "I had a black retriever named Buster when I was ten years old. He would walk me to the bus stop every morning.",
        "expected_theme": "childhood",
        "expected_decade": "1960s"
    },
    {
        "id": "sample-02",
        "transcript": "My first job was at the local bakery in 1972. I used to get up at five in the morning to bake fresh sourdough bread.",
        "expected_theme": "career",
        "expected_decade": "1970s"
    },
    {
        "id": "sample-03",
        "transcript": "We got married at St. Mary's church in June 1968. It was a beautiful sunny afternoon and Sarah was our flower girl.",
        "expected_theme": "romance/wedding",
        "expected_decade": "1960s"
    },
    {
        "id": "sample-04",
        "transcript": "Our daughter Sarah was born in 1975. The whole family gathered at the hospital to welcome her home.",
        "expected_theme": "family",
        "expected_decade": "1970s"
    },
    {
        "id": "sample-05",
        "transcript": "We bought our first home in Springfield in 1980. The house had a big porch where we sat every evening.",
        "expected_theme": "place/home",
        "expected_decade": "1980s"
    },
    {
        "id": "sample-06",
        "transcript": "I remember playing kickball in the alley behind our elementary school during summer recess.",
        "expected_theme": "childhood",
        "expected_decade": "1960s"
    },
    {
        "id": "sample-07",
        "transcript": "I worked as an accountant for thirty years at the downtown firm starting in 1985.",
        "expected_theme": "career",
        "expected_decade": "1980s"
    },
    {
        "id": "sample-08",
        "transcript": "We tied the knot during a quiet ceremony on the beach during our vacation in 1970.",
        "expected_theme": "romance/wedding",
        "expected_decade": "1970s"
    },
    {
        "id": "sample-09",
        "transcript": "Every Sunday my grandmother would cook a giant dinner for all fifteen grandchildren.",
        "expected_theme": "family",
        "expected_decade": "1960s"
    },
    {
        "id": "sample-10",
        "transcript": "The old cabin by Lake Tahoe was my favorite place to spend winters in the nineties.",
        "expected_theme": "place/home",
        "expected_decade": "1990s"
    },
    {
        "id": "sample-11",
        "transcript": "I won a blue ribbon at the county fair for my apple pie in 1978.",
        "expected_theme": "other",
        "expected_decade": "1970s"
    },
    {
        "id": "sample-12",
        "transcript": "I remember when we got our very first black and white television set in the living room.",
        "expected_theme": "place/home",
        "expected_decade": "1950s"
    }
]

def test_ai_classification_benchmark_eval():
    """
    Evaluates AI classification accuracy, precision, recall, and F1 score against labeled benchmark dataset.
    """
    total_samples = len(BENCHMARK_DATASET)
    correct_theme_matches = 0
    correct_decade_matches = 0

    results = []
    
    for item in BENCHMARK_DATASET:
        output = classify_transcript(item["transcript"])
        theme_pred = output["theme"].lower()
        decade_pred = output["estimated_decade"]

        theme_correct = (theme_pred == item["expected_theme"].lower())
        decade_correct = (decade_pred == item["expected_decade"])

        if theme_correct:
            correct_theme_matches += 1
        if decade_correct:
            correct_decade_matches += 1

        results.append({
            "id": item["id"],
            "expected_theme": item["expected_theme"],
            "pred_theme": theme_pred,
            "theme_correct": theme_correct,
            "confidence": output["classification_confidence"],
            "rationale": output["classification_rationale"]
        })

    # Compute quantitative metrics
    accuracy = (correct_theme_matches / total_samples) * 100.0
    precision = correct_theme_matches / total_samples
    recall = correct_theme_matches / total_samples
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("\n" + "=" * 70)
    print("      KEEPSONG AI CLASSIFICATION EVALUATION METRICS REPORT")
    print("=" * 70)
    print(f" Total Benchmark Samples Evaluated : {total_samples}")
    print(f" Correct Theme Classifications     : {correct_theme_matches} / {total_samples}")
    print(f" Theme Classification Accuracy     : {accuracy:.1f}%")
    print(f" Precision                         : {precision:.3f}")
    print(f" Recall                            : {recall:.3f}")
    print(f" F1 Score                          : {f1_score:.3f}")
    print("=" * 70)

    for r in results:
        status_icon = "[OK]" if r["theme_correct"] else "[FAIL]"
        print(f" {status_icon} {r['id']}: Expected='{r['expected_theme']}', Pred='{r['pred_theme']}' (Conf: {r['confidence']:.2f})")
    print("=" * 70 + "\n")

    # Assert accuracy threshold (must exceed 80% accuracy)
    assert accuracy >= 80.0, f"AI Classification accuracy {accuracy:.1f}% fell below the 80% benchmark target."
