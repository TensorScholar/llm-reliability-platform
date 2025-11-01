 from __future__ import annotations

 import asyncio
 from datetime import datetime, timedelta
 from typing import Dict, List, Optional

 import numpy as np
 from scipy.spatial.distance import cosine
 from scipy.stats import entropy
 import structlog

 from ....domain.models.drift import (
     DistributionMetrics,
     DriftAlert,
     DriftDetectionConfig,
     DriftMetric,
     DriftSeverity,
     DriftType,
     DriftWindow,
 )
 from ....infrastructure.database.timescale.repositories import CaptureRepository
 from ....infrastructure.llm.embeddings import EmbeddingService


 logger = structlog.get_logger()


 class DriftDetectionService:
     """Service for detecting drift in LLM behavior."""

     def __init__(
         self,
         capture_repo: CaptureRepository,
         embedding_service: EmbeddingService,
         config: DriftDetectionConfig,
     ) -> None:
         self.capture_repo = capture_repo
         self.embedding_service = embedding_service
         self.config = config

     async def detect_drift(
         self,
         application_name: str,
         comparison_window: Optional[DriftWindow] = None,
         baseline_window: Optional[DriftWindow] = None,
     ) -> List[DriftMetric]:
         logger.info("detecting_drift", application=application_name)

         now = datetime.utcnow()
         if not comparison_window:
             comparison_window = DriftWindow(
                 start=now - timedelta(hours=self.config.comparison_window_hours),
                 end=now,
                 label="current",
             )
         if not baseline_window:
             baseline_window = DriftWindow(
                 start=now - timedelta(hours=self.config.baseline_window_hours + self.config.comparison_window_hours),
                 end=now - timedelta(hours=self.config.comparison_window_hours),
                 label="baseline",
             )

         baseline_data = await self.capture_repo.get_captures_in_window(
             application_name=application_name,
             start=baseline_window.start,
             end=baseline_window.end,
         )
         comparison_data = await self.capture_repo.get_captures_in_window(
             application_name=application_name,
             start=comparison_window.start,
             end=comparison_window.end,
         )

         if len(baseline_data) < self.config.min_samples_required:
             logger.warning(
                 "insufficient_baseline_samples",
                 baseline_count=len(baseline_data),
                 required=self.config.min_samples_required,
             )
             return []
         if len(comparison_data) < self.config.min_samples_required:
             logger.warning(
                 "insufficient_comparison_samples",
                 comparison_count=len(comparison_data),
                 required=self.config.min_samples_required,
             )
             return []

         metrics: list[DriftMetric] = []
         metrics.extend(
             await self._detect_statistical_drift(
                 baseline_data, comparison_data, baseline_window, comparison_window
             )
         )
         metrics.extend(
             await self._detect_semantic_drift(
                 baseline_data, comparison_data, baseline_window, comparison_window
             )
         )
         metrics.extend(
             await self._detect_behavioral_drift(
                 baseline_data, comparison_data, baseline_window, comparison_window
             )
         )
         metrics.extend(
             await self._detect_performance_drift(
                 baseline_data, comparison_data, baseline_window, comparison_window
             )
         )

         logger.info(
             "drift_detection_complete",
             application=application_name,
             total_metrics=len(metrics),
             drifting_metrics=sum(1 for m in metrics if m.is_drifting),
         )
         return metrics

     async def _detect_statistical_drift(self, baseline_data, comparison_data, baseline_window, comparison_window) -> List[DriftMetric]:
         metrics: list[DriftMetric] = []
         baseline_lengths = [len(d.response_text) for d in baseline_data]
         comparison_lengths = [len(d.response_text) for d in comparison_data]

         kl_div = self._calculate_kl_divergence(baseline_lengths, comparison_lengths)
         js_div = self._calculate_js_divergence(baseline_lengths, comparison_lengths)

         metrics.append(
             DriftMetric(
                 drift_type=DriftType.STATISTICAL,
                 metric_name="kl_divergence_response_length",
                 value=kl_div,
                 threshold=self.config.kl_divergence_threshold,
                 severity=self._determine_severity(kl_div, self.config.kl_divergence_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
                 metadata={
                     "baseline_samples": len(baseline_lengths),
                     "comparison_samples": len(comparison_lengths),
                 },
             )
         )
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.STATISTICAL,
                 metric_name="js_divergence_response_length",
                 value=js_div,
                 threshold=self.config.js_divergence_threshold,
                 severity=self._determine_severity(js_div, self.config.js_divergence_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
             )
         )

         baseline_tokens = [d.tokens_total or 0 for d in baseline_data]
         comparison_tokens = [d.tokens_total or 0 for d in comparison_data]
         token_kl = self._calculate_kl_divergence(baseline_tokens, comparison_tokens)
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.STATISTICAL,
                 metric_name="kl_divergence_token_usage",
                 value=token_kl,
                 threshold=self.config.kl_divergence_threshold,
                 severity=self._determine_severity(token_kl, self.config.kl_divergence_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
             )
         )
         return metrics

     async def _detect_semantic_drift(self, baseline_data, comparison_data, baseline_window, comparison_window) -> List[DriftMetric]:
         metrics: list[DriftMetric] = []
         sample_size = min(100, len(baseline_data), len(comparison_data))
         baseline_sample = np.random.choice(baseline_data, sample_size, replace=False)
         comparison_sample = np.random.choice(comparison_data, sample_size, replace=False)

         baseline_texts = [d.response_text for d in baseline_sample]
         comparison_texts = [d.response_text for d in comparison_sample]
         baseline_embeddings = await self.embedding_service.embed_batch(baseline_texts)
         comparison_embeddings = await self.embedding_service.embed_batch(comparison_texts)

         baseline_centroid = np.mean(baseline_embeddings, axis=0)
         comparison_centroid = np.mean(comparison_embeddings, axis=0)
         cosine_dist = float(cosine(baseline_centroid, comparison_centroid))
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.SEMANTIC,
                 metric_name="cosine_distance_centroid",
                 value=cosine_dist,
                 threshold=self.config.cosine_distance_threshold,
                 severity=self._determine_severity(cosine_dist, self.config.cosine_distance_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
                 metadata={"sample_size": sample_size},
             )
         )

         baseline_avg_dist = self._calculate_avg_pairwise_distance(baseline_embeddings)
         comparison_avg_dist = self._calculate_avg_pairwise_distance(comparison_embeddings)
         distance_change = abs(comparison_avg_dist - baseline_avg_dist) / max(baseline_avg_dist, 1e-9)
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.SEMANTIC,
                 metric_name="pairwise_distance_change",
                 value=float(distance_change),
                 threshold=self.config.cosine_distance_threshold,
                 severity=self._determine_severity(float(distance_change), self.config.cosine_distance_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
             )
         )
         return metrics

     async def _detect_behavioral_drift(self, baseline_data, comparison_data, baseline_window, comparison_window) -> List[DriftMetric]:
         metrics: list[DriftMetric] = []
         baseline_avg_length = float(np.mean([len(d.response_text) for d in baseline_data]))
         comparison_avg_length = float(np.mean([len(d.response_text) for d in comparison_data]))
         length_change = abs(comparison_avg_length - baseline_avg_length) / max(baseline_avg_length, 1e-9)
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.BEHAVIORAL,
                 metric_name="response_length_change",
                 value=float(length_change),
                 threshold=self.config.response_length_change_threshold,
                 severity=self._determine_severity(float(length_change), self.config.response_length_change_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
                 metadata={
                     "baseline_avg": baseline_avg_length,
                     "comparison_avg": comparison_avg_length,
                 },
             )
         )

         baseline_avg_sentences = float(
             np.mean([len([s for s in d.response_text.split(".") if s.strip()]) for d in baseline_data])
         )
         comparison_avg_sentences = float(
             np.mean([len([s for s in d.response_text.split(".") if s.strip()]) for d in comparison_data])
         )
         sentence_change = abs(comparison_avg_sentences - baseline_avg_sentences) / max(
             baseline_avg_sentences, 1e-9
         )
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.BEHAVIORAL,
                 metric_name="sentence_count_change",
                 value=float(sentence_change),
                 threshold=self.config.response_length_change_threshold,
                 severity=self._determine_severity(float(sentence_change), self.config.response_length_change_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
             )
         )
         return metrics

     async def _detect_performance_drift(self, baseline_data, comparison_data, baseline_window, comparison_window) -> List[DriftMetric]:
         metrics: list[DriftMetric] = []
         baseline_latencies = [d.latency_ms or 0 for d in baseline_data]
         comparison_latencies = [d.latency_ms or 0 for d in comparison_data]
         baseline_p95 = float(np.percentile(baseline_latencies, 95))
         comparison_p95 = float(np.percentile(comparison_latencies, 95))
         latency_change = (comparison_p95 - baseline_p95) / max(baseline_p95, 1e-9)
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.PERFORMANCE,
                 metric_name="latency_p95_change",
                 value=float(latency_change),
                 threshold=self.config.latency_change_threshold,
                 severity=self._determine_severity(float(abs(latency_change)), self.config.latency_change_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
                 metadata={"baseline_p95_ms": baseline_p95, "comparison_p95_ms": comparison_p95},
             )
         )

         baseline_costs = [float(d.cost_usd or 0.0) for d in baseline_data]
         comparison_costs = [float(d.cost_usd or 0.0) for d in comparison_data]
         baseline_avg_cost = float(np.mean(baseline_costs))
         comparison_avg_cost = float(np.mean(comparison_costs))
         cost_change = (comparison_avg_cost - baseline_avg_cost) / max(baseline_avg_cost, 1e-9)
         metrics.append(
             DriftMetric(
                 drift_type=DriftType.PERFORMANCE,
                 metric_name="cost_per_request_change",
                 value=float(cost_change),
                 threshold=self.config.cost_change_threshold,
                 severity=self._determine_severity(float(abs(cost_change)), self.config.cost_change_threshold),
                 baseline_window=baseline_window,
                 comparison_window=comparison_window,
                 metadata={
                     "baseline_avg_cost": baseline_avg_cost,
                     "comparison_avg_cost": comparison_avg_cost,
                 },
             )
         )
         return metrics

     def _calculate_kl_divergence(self, baseline: List[float], comparison: List[float], bins: int = 20) -> float:
         min_val = min(min(baseline), min(comparison))
         max_val = max(max(baseline), max(comparison))
         baseline_hist, _ = np.histogram(baseline, bins=bins, range=(min_val, max_val))
         comparison_hist, _ = np.histogram(comparison, bins=bins, range=(min_val, max_val))
         baseline_prob = (baseline_hist + 1e-10) / (baseline_hist.sum() + bins * 1e-10)
         comparison_prob = (comparison_hist + 1e-10) / (comparison_hist.sum() + bins * 1e-10)
         return float(entropy(comparison_prob, baseline_prob))

     def _calculate_js_divergence(self, baseline: List[float], comparison: List[float], bins: int = 20) -> float:
         min_val = min(min(baseline), min(comparison))
         max_val = max(max(baseline), max(comparison))
         baseline_hist, _ = np.histogram(baseline, bins=bins, range=(min_val, max_val))
         comparison_hist, _ = np.histogram(comparison, bins=bins, range=(min_val, max_val))
         baseline_prob = (baseline_hist + 1e-10) / (baseline_hist.sum() + bins * 1e-10)
         comparison_prob = (comparison_hist + 1e-10) / (comparison_hist.sum() + bins * 1e-10)
         m = (baseline_prob + comparison_prob) / 2
         js_div = (entropy(baseline_prob, m) + entropy(comparison_prob, m)) / 2
         return float(js_div)

     def _calculate_avg_pairwise_distance(self, embeddings: np.ndarray) -> float:
         n = len(embeddings)
         if n < 2:
             return 0.0
         total = 0.0
         count = 0
         sample = min(50, n)
         idx = np.random.choice(n, sample, replace=False)
         for i in range(len(idx)):
             for j in range(i + 1, len(idx)):
                 total += float(cosine(embeddings[idx[i]], embeddings[idx[j]]))
                 count += 1
         return total / count if count else 0.0

     def _determine_severity(self, value: float, threshold: float) -> DriftSeverity:
         if value < threshold:
             return DriftSeverity.NONE
         if value < threshold * 1.5:
             return DriftSeverity.LOW
         if value < threshold * 2.0:
             return DriftSeverity.MEDIUM
         if value < threshold * 3.0:
             return DriftSeverity.HIGH
         return DriftSeverity.CRITICAL


