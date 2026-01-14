"""
Sentiment analysis using VADER and FinBERT.
"""

from typing import Any, Dict, List, Optional

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer:
    """
    Base sentiment analyzer interface.
    """

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores
        """
        raise NotImplementedError


class VADERSentimentAnalyzer(SentimentAnalyzer):
    """
    VADER (Valence Aware Dictionary and sEntiment Reasoner) sentiment analyzer.
    Fast, rule-based, good for general sentiment.
    """

    def __init__(self):
        """Initialize VADER analyzer."""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

            self.analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except ImportError as e:
            logger.error(f"Failed to import VADER: {e}")
            raise

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using VADER.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with VADER scores:
                - compound: Overall sentiment (-1 to +1)
                - pos: Positive score (0 to 1)
                - neu: Neutral score (0 to 1)
                - neg: Negative score (0 to 1)
                - label: Categorical label (positive/negative/neutral)
        """
        if not text:
            return self._empty_result()

        try:
            # Get VADER scores
            scores = self.analyzer.polarity_scores(text)

            # Determine categorical label
            compound = scores["compound"]
            if compound >= 0.05:
                label = "positive"
            elif compound <= -0.05:
                label = "negative"
            else:
                label = "neutral"

            return {
                "model": "vader",
                "compound": scores["compound"],
                "positive": scores["pos"],
                "neutral": scores["neu"],
                "negative": scores["neg"],
                "label": label,
                "confidence": abs(compound),  # Use absolute compound as confidence
            }

        except Exception as e:
            logger.error(f"VADER analysis failed: {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result for errors."""
        return {
            "model": "vader",
            "compound": 0.0,
            "positive": 0.0,
            "neutral": 1.0,
            "negative": 0.0,
            "label": "neutral",
            "confidence": 0.0,
        }

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment results
        """
        return [self.analyze(text) for text in texts]


class FinBERTSentimentAnalyzer(SentimentAnalyzer):
    """
    FinBERT sentiment analyzer.
    Transformer model fine-tuned on financial text.
    Better accuracy for earnings/financial context.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert", use_gpu: bool = False):
        """
        Initialize FinBERT analyzer.

        Args:
            model_name: HuggingFace model name
            use_gpu: Whether to use GPU
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        self.tokenizer = None

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch

            logger.info(f"Loading FinBERT model: {model_name}")

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

            # Move to GPU if requested and available
            if use_gpu and torch.cuda.is_available():
                self.model = self.model.cuda()
                self.device = "cuda"
                logger.info("FinBERT using GPU")
            else:
                self.device = "cpu"
                logger.info("FinBERT using CPU")

            self.model.eval()  # Set to evaluation mode
            logger.info("FinBERT sentiment analyzer initialized")

        except ImportError as e:
            logger.error(f"Failed to import transformers/torch: {e}")
            logger.info("FinBERT requires: pip install transformers torch")
            raise

    def analyze(self, text: str, max_length: int = 512) -> Dict[str, Any]:
        """
        Analyze sentiment using FinBERT.

        Args:
            text: Text to analyze
            max_length: Maximum sequence length

        Returns:
            Dictionary with FinBERT scores:
                - positive: Probability of positive (0 to 1)
                - negative: Probability of negative (0 to 1)
                - neutral: Probability of neutral (0 to 1)
                - label: Predicted label
                - confidence: Confidence score
        """
        if not text:
            return self._empty_result()

        try:
            import torch

            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True,
            )

            # Move to device
            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # Convert to probabilities
            probs = predictions[0].cpu().numpy()

            # FinBERT labels: [positive, negative, neutral]
            positive_prob = float(probs[0])
            negative_prob = float(probs[1])
            neutral_prob = float(probs[2])

            # Determine label
            max_prob = max(positive_prob, negative_prob, neutral_prob)
            if positive_prob == max_prob:
                label = "positive"
            elif negative_prob == max_prob:
                label = "negative"
            else:
                label = "neutral"

            return {
                "model": "finbert",
                "positive": positive_prob,
                "negative": negative_prob,
                "neutral": neutral_prob,
                "label": label,
                "confidence": max_prob,
            }

        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result for errors."""
        return {
            "model": "finbert",
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0,
            "label": "neutral",
            "confidence": 0.0,
        }

    def analyze_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts in batches.

        Args:
            texts: List of texts
            batch_size: Batch size for processing

        Returns:
            List of sentiment results
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = [self.analyze(text) for text in batch]
            results.extend(batch_results)

        return results


class MultiModelSentimentAnalyzer(SentimentAnalyzer):
    """
    Uses multiple sentiment models and combines results.
    """

    def __init__(self, models: List[str] = None, use_gpu: bool = False):
        """
        Initialize multi-model analyzer.

        Args:
            models: List of model names ('vader', 'finbert')
            use_gpu: Whether to use GPU for FinBERT
        """
        settings = get_settings()
        self.models = models or [settings.sentiment_model]
        self.use_gpu = use_gpu

        self.analyzers: Dict[str, SentimentAnalyzer] = {}

        # Initialize requested models
        for model_name in self.models:
            if model_name == "vader":
                try:
                    self.analyzers["vader"] = VADERSentimentAnalyzer()
                except Exception as e:
                    logger.error(f"Failed to initialize VADER: {e}")

            elif model_name == "finbert":
                try:
                    self.analyzers["finbert"] = FinBERTSentimentAnalyzer(use_gpu=use_gpu)
                except Exception as e:
                    logger.error(f"Failed to initialize FinBERT: {e}")
                    logger.info("Skipping FinBERT (install: pip install transformers torch)")

        if not self.analyzers:
            raise ValueError("No sentiment models initialized")

        logger.info(f"MultiModel analyzer initialized with: {list(self.analyzers.keys())}")

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment with all models.

        Args:
            text: Text to analyze

        Returns:
            Combined sentiment results
        """
        results = {}

        for model_name, analyzer in self.analyzers.items():
            results[model_name] = analyzer.analyze(text)

        # If multiple models, compute consensus
        if len(self.analyzers) > 1:
            results["consensus"] = self._compute_consensus(results)

        return results

    def _compute_consensus(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute consensus from multiple models.

        Args:
            results: Results from each model

        Returns:
            Consensus sentiment
        """
        # Simple voting: majority label wins
        labels = [r["label"] for r in results.values() if "label" in r]

        if not labels:
            return {"label": "neutral", "confidence": 0.0}

        # Count votes
        from collections import Counter

        label_counts = Counter(labels)
        consensus_label = label_counts.most_common(1)[0][0]

        # Average confidence from agreeing models
        agreeing_confidences = [
            r["confidence"]
            for r in results.values()
            if r.get("label") == consensus_label
        ]

        consensus_confidence = (
            sum(agreeing_confidences) / len(agreeing_confidences)
            if agreeing_confidences
            else 0.0
        )

        return {
            "label": consensus_label,
            "confidence": consensus_confidence,
            "agreement": len(agreeing_confidences) / len(labels),
        }


def get_sentiment_analyzer(
    model: str = None, use_gpu: bool = False
) -> SentimentAnalyzer:
    """
    Factory function to get sentiment analyzer.

    Args:
        model: Model name ('vader', 'finbert', 'both')
        use_gpu: Whether to use GPU

    Returns:
        Sentiment analyzer instance
    """
    settings = get_settings()
    model = model or settings.sentiment_model

    if model == "vader":
        return VADERSentimentAnalyzer()
    elif model == "finbert":
        return FinBERTSentimentAnalyzer(use_gpu=use_gpu)
    elif model == "both":
        return MultiModelSentimentAnalyzer(models=["vader", "finbert"], use_gpu=use_gpu)
    else:
        logger.warning(f"Unknown model '{model}', defaulting to VADER")
        return VADERSentimentAnalyzer()
