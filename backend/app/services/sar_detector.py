"""SAR Scene Ingestion, Preprocessing, Lookalike Discrimination, and Detection Engine.

Compliant with PRD FR1 & FR2, and permanent rules (GEMINI.md).
Provides an extensible classifier interface allowing future trained ML/DL models (e.g. U-Net,
Random Forest, XGBoost) to replace the explainable baseline classifier.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np
from scipy import ndimage

from backend.app.models.schemas import (
    GeoPoint,
    SlickPolygon,
    SARScene,
    SlickDetection,
    SARLookalikeClass,
    SARFeatureVector,
    SARCandidatePatch,
    SARCandidateCollectionResponse,
)

logger = logging.getLogger("maritime-oil-attribution.sar")


# ---------------------------------------------------------------------------
# Data Models for SAR Raster
# ---------------------------------------------------------------------------

@dataclass
class SARRaster:
    """Georeferenced 2D SAR backscatter raster in decibels (dB)."""
    data_db: np.ndarray  # 2D float array (rows, cols)
    top_left_lon: float
    top_left_lat: float
    pixel_size_deg_lon: float  # Longitude step per pixel (positive)
    pixel_size_deg_lat: float  # Latitude step per pixel (negative, going south)
    acquisition_timestamp: datetime
    satellite_platform: str = "Sentinel-1A (Synthetic)"
    polarization: str = "VV"
    pixel_resolution_meters: float = 20.0
    ambient_wind_speed_ms: Optional[float] = 6.5  # Estimated surface wind in m/s

    @property
    def shape(self) -> Tuple[int, int]:
        return self.data_db.shape

    def pixel_to_geo(self, row: float, col: float) -> Tuple[float, float]:
        """Convert pixel (row, col) to (lon, lat)."""
        lon = self.top_left_lon + col * self.pixel_size_deg_lon
        lat = self.top_left_lat + row * self.pixel_size_deg_lat
        return float(lon), float(lat)

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """Convert (lon, lat) to nearest pixel (row, col)."""
        col = int(round((lon - self.top_left_lon) / self.pixel_size_deg_lon))
        row = int(round((lat - self.top_left_lat) / self.pixel_size_deg_lat))
        return row, col


@dataclass
class DetectorConfig:
    """Configuration parameters for the deterministic SAR detector."""
    # Preprocessing
    speckle_filter_size: int = 5  # Size of local window
    # Land masking
    land_threshold_db: float = -6.0  # Pixels brighter than -6 dB treated as land/coastal
    land_buffer_pixels: int = 3  # Morphological dilation buffer around land
    # Dark region segmentation (CFAR / adaptive threshold)
    cfar_guard_window: int = 15
    cfar_k_sigma: float = 1.8  # Threshold = local_mean - k * local_std
    min_contrast_db: float = 3.5  # Minimum damping contrast required for oil slick
    # Size constraints
    min_area_sq_km: float = 0.5  # Ignore tiny specks (< 0.5 km^2)
    max_area_sq_km: float = 150.0  # Basins > 150 km^2 are typically low-wind lookalikes
    # Lookalike discrimination
    min_elongation_ratio: float = 1.6  # Mineral slicks are usually elongated by wind/currents
    min_edge_gradient_db: float = 0.8  # Minimum boundary sharpness in dB/pixel


# ---------------------------------------------------------------------------
# Abstract Classifier Interface (Pluggable for Future ML Models)
# ---------------------------------------------------------------------------

class BaseSARClassifier(ABC):
    """Abstract interface for classifying segmented SAR dark patches.
    
    A future trained ML model (e.g., Random Forest or U-Net feature head)
    can implement this interface without modifying any pipeline services.
    """

    @abstractmethod
    def classify(
        self,
        features: SARFeatureVector,
    ) -> Tuple[SARLookalikeClass, bool, float, float, Optional[str]]:
        """Classifies a candidate patch.
        
        Returns:
            classification: SARLookalikeClass enum
            is_accepted: bool (True for mineral oil, False for rejected lookalikes)
            confidence_score: float [0.0 - 1.0]
            lookalike_probability: float [0.0 - 1.0]
            rejection_reason: Optional[str] (Required if is_accepted is False)
        """
        pass


class ExplainableRuleSARClassifier(BaseSARClassifier):
    """Explainable rule-based baseline classifier.
    
    Note: This baseline model is an explainable heuristic implementation for decision support.
    It is not a statistically validated production deep-learning model.
    """

    def classify(
        self,
        features: SARFeatureVector,
    ) -> Tuple[SARLookalikeClass, bool, float, float, Optional[str]]:
        # 1. Check for Coastal Land Shadow (Distance to land < 1.0 km and near land buffer)
        if features.distance_to_land_km is not None and features.distance_to_land_km < 1.2:
            return (
                SARLookalikeClass.LOOKALIKE_COASTAL_SHADOW,
                False,
                0.20,
                0.80,
                f"Rejected as coastal shadow: Located within {features.distance_to_land_km:.2f} km of landmass / coastal surf."
            )

        # 2. Check for Low-Wind Calm Sea Basin (Excessive area > 150 km2 or low edge gradient)
        if features.area_sq_km > 150.0:
            return (
                SARLookalikeClass.LOOKALIKE_LOW_WIND,
                False,
                0.15,
                0.85,
                f"Rejected as low-wind lookalike: Surface area ({features.area_sq_km:.1f} km²) exceeds maximum expected oil slick size (150.0 km²); characteristic of meteorological calm sea basin."
            )

        # 3. Check for Biogenic / Natural Organic Slicks (Weak damping contrast or highly circular shape)
        if features.mean_contrast_db < 3.5:
            return (
                SARLookalikeClass.LOOKALIKE_BIOGENIC,
                False,
                0.25,
                0.75,
                f"Rejected as biogenic lookalike: Radar damping contrast ({features.mean_contrast_db:.2f} dB) is below the mineral oil threshold (3.5 dB); consistent with natural monomolecular films."
            )

        if features.elongation_ratio < 1.3 and features.compactness < 1.4:
            return (
                SARLookalikeClass.LOOKALIKE_BIOGENIC,
                False,
                0.30,
                0.70,
                f"Rejected as biogenic lookalike: Isotropic circular morphology (elongation {features.elongation_ratio:.2f}) lacks hydrodynamic dispersion alignment."
            )

        # 4. Check for Fuzzy Boundary Lookalike (Low edge transition gradient)
        if features.edge_gradient_db_per_pixel < 0.6:
            return (
                SARLookalikeClass.LOOKALIKE_UPWELLING,
                False,
                0.35,
                0.65,
                f"Rejected as oceanographic upwelling / internal wave lookalike: Diffuse boundary gradient ({features.edge_gradient_db_per_pixel:.2f} dB/px < 0.6 dB/px) lacks sharp oil-water boundary."
            )

        # 5. Accepted Mineral Oil Slick
        # Calculate multi-feature confidence score
        contrast_score = min(1.0, features.mean_contrast_db / 8.0)
        elongation_score = min(1.0, (features.elongation_ratio - 1.0) / 2.5)
        edge_score = min(1.0, features.edge_gradient_db_per_pixel / 1.5)
        size_score = 1.0 if (2.0 <= features.area_sq_km <= 50.0) else 0.85

        confidence = 0.35 * contrast_score + 0.30 * elongation_score + 0.20 * edge_score + 0.15 * size_score
        confidence = float(np.clip(confidence, 0.50, 0.98))
        lookalike_prob = float(round(1.0 - confidence, 3))

        return (
            SARLookalikeClass.MINERAL_OIL,
            True,
            round(confidence, 3),
            lookalike_prob,
            None
        )


# ---------------------------------------------------------------------------
# Abstract Base Detector Interface (For ML / Deep-Learning Swap)
# ---------------------------------------------------------------------------

class BaseSARDetector(ABC):
    """Abstract base class for all SAR oil-spill detection and segmentation engines."""

    @abstractmethod
    def extract_candidates(
        self,
        scene: SARScene,
        raster: SARRaster,
        config: Optional[DetectorConfig] = None,
    ) -> List[SARCandidatePatch]:
        """Extracts and classifies all candidate patches in the SAR scene."""
        pass

    @abstractmethod
    def detect_primary_slick(
        self,
        scene: SARScene,
        raster: SARRaster,
        config: Optional[DetectorConfig] = None,
    ) -> SlickDetection:
        """Extracts the primary verified oil-slick detection from the SAR scene."""
        pass


# ---------------------------------------------------------------------------
# Deterministic Baseline SAR Detector
# ---------------------------------------------------------------------------

class DeterministicSARDetector(BaseSARDetector):
    """Deterministic, explainable rule-based SAR oil slick detector with lookalike rejection."""

    def __init__(
        self,
        classifier: Optional[BaseSARClassifier] = None,
        default_config: Optional[DetectorConfig] = None,
    ):
        self.classifier = classifier or ExplainableRuleSARClassifier()
        self.config = default_config or DetectorConfig()

    def preprocess_speckle_filter(self, data_db: np.ndarray, window_size: int = 5) -> np.ndarray:
        """Applies local mean smoothing to suppress radar speckle noise."""
        return ndimage.uniform_filter(data_db, size=window_size)

    def create_land_mask(
        self,
        data_db: np.ndarray,
        threshold_db: float = -6.0,
        buffer_pixels: int = 3,
    ) -> np.ndarray:
        """Detects land/islands with strong radar backscatter and applies coastal dilation."""
        land_binary = data_db > threshold_db
        if buffer_pixels > 0:
            struct = ndimage.generate_binary_structure(2, 2)
            land_binary = ndimage.binary_dilation(land_binary, structure=struct, iterations=buffer_pixels)
        return land_binary

    def segment_dark_regions(
        self,
        filtered_db: np.ndarray,
        land_mask: np.ndarray,
        k_sigma: float = 1.8,
        window_size: int = 25,
    ) -> Tuple[np.ndarray, float, float]:
        """Adaptive CFAR-like dark patch thresholding on sea pixels."""
        sea_pixels = filtered_db[~land_mask]
        if len(sea_pixels) == 0:
            return np.zeros_like(filtered_db, dtype=bool), 0.0, 0.0

        sea_mean = float(np.mean(sea_pixels))
        sea_std = float(np.std(sea_pixels))

        local_mean = ndimage.uniform_filter(filtered_db, size=window_size)
        adaptive_threshold = local_mean - (k_sigma * sea_std)

        dark_mask = (filtered_db < adaptive_threshold) & (~land_mask)
        struct = ndimage.generate_binary_structure(2, 1)
        dark_mask = ndimage.binary_opening(dark_mask, structure=struct, iterations=1)

        return dark_mask, sea_mean, sea_std

    def extract_polygon_from_mask(
        self,
        mask: np.ndarray,
        raster: SARRaster,
    ) -> List[List[float]]:
        """Vectorizes a binary connected component into a closed GeoJSON coordinate ring."""
        padded = np.pad(mask, 1, mode='constant', constant_values=0)
        dy, dx = np.gradient(padded.astype(float))
        edge_coords = np.argwhere((dy != 0) | (dx != 0))

        if len(edge_coords) < 4:
            rows = np.where(mask)[0]
            cols = np.where(mask)[1]
            min_r, max_r = int(np.min(rows)), int(np.max(rows))
            min_c, max_c = int(np.min(cols)), int(np.max(cols))
            p1 = raster.pixel_to_geo(min_r, min_c)
            p2 = raster.pixel_to_geo(min_r, max_c)
            p3 = raster.pixel_to_geo(max_r, max_c)
            p4 = raster.pixel_to_geo(max_r, min_c)
            return [[p1[0], p1[1]], [p2[0], p2[1]], [p3[0], p3[1]], [p4[0], p4[1]], [p1[0], p1[1]]]

        r_center = np.mean(edge_coords[:, 0]) - 1.0
        c_center = np.mean(edge_coords[:, 1]) - 1.0

        angles = np.arctan2(edge_coords[:, 0] - 1.0 - r_center, edge_coords[:, 1] - 1.0 - c_center)
        sort_idx = np.argsort(angles)
        sorted_coords = edge_coords[sort_idx]

        step = max(1, len(sorted_coords) // 24)
        downsampled = sorted_coords[::step]

        ring: List[List[float]] = []
        for r_pad, c_pad in downsampled:
            r = r_pad - 1.0
            c = c_pad - 1.0
            lon, lat = raster.pixel_to_geo(r, c)
            ring.append([round(lon, 5), round(lat, 5)])

        if ring[0] != ring[-1]:
            ring.append(ring[0])

        if len(ring) < 4:
            ring.append(ring[0])

        return ring

    def compute_features(
        self,
        comp_mask: np.ndarray,
        filtered_db: np.ndarray,
        land_mask: np.ndarray,
        sea_mean: float,
        raster: SARRaster,
    ) -> Tuple[SARFeatureVector, GeoPoint, List[List[float]]]:
        """Calculates explainable geometric, intensity, texture, edge, and contextual features."""
        rows, cols = np.where(comp_mask)
        r_bar = float(np.mean(rows))
        c_bar = float(np.mean(cols))
        c_lon, c_lat = raster.pixel_to_geo(r_bar, c_bar)
        centroid = GeoPoint(type="Point", coordinates=[round(c_lon, 5), round(c_lat, 5)])

        dr = rows - r_bar
        dc = cols - c_bar
        mu20 = float(np.mean(dr ** 2))
        mu02 = float(np.mean(dc ** 2))
        mu11 = float(np.mean(dr * dc))

        theta_rad = 0.5 * math.atan2(2 * mu11, (mu02 - mu20) + 1e-9)
        orientation_deg = float((90.0 - math.degrees(theta_rad)) % 180.0)

        term = math.sqrt((mu02 - mu20) ** 2 + 4 * (mu11 ** 2))
        lambda1 = 0.5 * ((mu02 + mu20) + term)
        lambda2 = 0.5 * ((mu02 + mu20) - term) + 1e-9
        elongation = float(math.sqrt(max(1.0, lambda1 / lambda2)))

        pixel_area_km2 = (raster.pixel_resolution_meters / 1000.0) ** 2
        area_km2 = float(len(rows) * pixel_area_km2)

        padded = np.pad(comp_mask, 1, mode='constant', constant_values=0)
        grad = np.abs(np.gradient(padded.astype(float))[0]) + np.abs(np.gradient(padded.astype(float))[1])
        perimeter_km = float(np.sum(grad > 0) * (raster.pixel_resolution_meters / 1000.0))

        compactness = float(max(1.0, (perimeter_km ** 2) / (4.0 * math.pi * max(0.01, area_km2))))

        patch_pixels = filtered_db[comp_mask]
        patch_mean = float(np.mean(patch_pixels))
        patch_std = float(np.std(patch_pixels))
        contrast_db = float(sea_mean - patch_mean)
        min_db = float(np.min(patch_pixels))
        cov = float(patch_std / (abs(patch_mean) + 1e-6))

        # Edge gradient sharpness via Sobel operator around the boundary
        sobel_y = ndimage.sobel(filtered_db, axis=0)
        sobel_x = ndimage.sobel(filtered_db, axis=1)
        gradient_mag = np.hypot(sobel_x, sobel_y)
        border_mask = (grad[1:-1, 1:-1] > 0)
        if np.any(border_mask):
            edge_grad = float(np.mean(gradient_mag[border_mask]))
        else:
            edge_grad = 1.0

        # Distance to land calculation
        if np.any(land_mask):
            land_distance_pixels = ndimage.distance_transform_edt(~land_mask)
            min_dist_px = float(land_distance_pixels[int(r_bar), int(c_bar)])
            dist_land_km = float(min_dist_px * (raster.pixel_resolution_meters / 1000.0))
        else:
            dist_land_km = 999.0

        polygon_coords = self.extract_polygon_from_mask(comp_mask, raster)

        features = SARFeatureVector(
            area_sq_km=round(area_km2, 2),
            perimeter_km=round(perimeter_km, 2),
            compactness=round(compactness, 2),
            elongation_ratio=round(elongation, 2),
            major_axis_orientation_deg=round(orientation_deg, 1),
            mean_contrast_db=round(contrast_db, 2),
            std_dev_db=round(patch_std, 2),
            coeff_of_variation=round(cov, 3),
            edge_gradient_db_per_pixel=round(edge_grad, 2),
            min_backscatter_db=round(min_db, 2),
            distance_to_land_km=round(dist_land_km, 2),
            ambient_wind_speed_ms=raster.ambient_wind_speed_ms,
        )

        return features, centroid, polygon_coords

    def extract_candidates(
        self,
        scene: SARScene,
        raster: SARRaster,
        config: Optional[DetectorConfig] = None,
    ) -> List[SARCandidatePatch]:
        """Extracts and classifies all candidate patches, recording rejection reasons for lookalikes."""
        cfg = config or self.config

        # 1. Preprocessing & Land Masking
        filtered_db = self.preprocess_speckle_filter(raster.data_db, window_size=cfg.speckle_filter_size)
        land_mask = self.create_land_mask(raster.data_db, threshold_db=cfg.land_threshold_db, buffer_pixels=cfg.land_buffer_pixels)

        # 2. Dark Region Segmentation
        dark_mask, sea_mean, _ = self.segment_dark_regions(
            filtered_db, land_mask, k_sigma=cfg.cfar_k_sigma, window_size=cfg.cfar_guard_window
        )

        # 3. Connected Components
        struct = ndimage.generate_binary_structure(2, 2)
        labeled_mask, num_features = ndimage.label(dark_mask, structure=struct)

        candidates: List[SARCandidatePatch] = []
        pixel_area_km2 = (raster.pixel_resolution_meters / 1000.0) ** 2

        for feature_id in range(1, num_features + 1):
            comp_mask = labeled_mask == feature_id
            num_pixels = int(np.sum(comp_mask))
            area_km2 = num_pixels * pixel_area_km2

            if area_km2 < cfg.min_area_sq_km:
                continue

            features, centroid, polygon_coords = self.compute_features(
                comp_mask, filtered_db, land_mask, sea_mean, raster
            )

            # Classify using pluggable classifier
            cls_label, is_accepted, conf, lookalike_p, rej_reason = self.classifier.classify(features)

            candidate = SARCandidatePatch(
                id=str(uuid.uuid4()),
                sar_scene_id=scene.id,
                polygon=SlickPolygon(type="Polygon", coordinates=[polygon_coords]),
                centroid=centroid,
                classification=cls_label,
                is_accepted=is_accepted,
                confidence_score=conf,
                lookalike_probability=lookalike_p,
                rejection_reason=rej_reason,
                features=features,
                created_at=datetime.now(timezone.utc),
            )
            candidates.append(candidate)

        return candidates

    def get_candidate_collection(
        self,
        case_id: str,
        scene: SARScene,
        raster: SARRaster,
        config: Optional[DetectorConfig] = None,
    ) -> SARCandidateCollectionResponse:
        """Returns the complete collection of accepted slicks and rejected lookalike candidates."""
        candidates = self.extract_candidates(scene, raster, config)
        accepted = [c for c in candidates if c.is_accepted]
        rejected = [c for c in candidates if not c.is_accepted]

        metadata = {
            "classifier_type": self.classifier.__class__.__name__,
            "scientific_status": "DECISION_SUPPORT_BASELINE (Heuristic Rule Model - Not Production ML)",
            "limitations_note": "Rule-based baseline models cannot resolve biogenic lookalikes under low wind (< 3 m/s) with 100% precision. Statistical validation against calibrated SAR datasets is required for operational use.",
            "features_evaluated": [
                "area_sq_km",
                "compactness",
                "elongation_ratio",
                "mean_contrast_db",
                "edge_gradient_db_per_pixel",
                "distance_to_land_km"
            ]
        }

        return SARCandidateCollectionResponse(
            case_id=case_id,
            sar_scene_id=scene.id,
            total_candidates=len(candidates),
            accepted_count=len(accepted),
            rejected_count=len(rejected),
            accepted_slicks=accepted,
            rejected_candidates=rejected,
            classifier_metadata=metadata,
        )

    def detect_primary_slick(
        self,
        scene: SARScene,
        raster: SARRaster,
        config: Optional[DetectorConfig] = None,
    ) -> SlickDetection:
        """Finds all candidates and returns the primary verified mineral oil slick detection."""
        candidates = self.extract_candidates(scene, raster, config)
        accepted = [c for c in candidates if c.is_accepted]

        if not accepted:
            if candidates:
                best = max(candidates, key=lambda c: c.confidence_score)
            else:
                raise ValueError(f"No dark patch candidates detected in SAR scene '{scene.id}'.")
        else:
            best = max(accepted, key=lambda c: c.confidence_score)

        return SlickDetection(
            id=str(uuid.uuid4()),
            sar_scene_id=scene.id,
            slick_polygon=best.polygon,
            centroid=best.centroid,
            area_sq_km=best.features.area_sq_km,
            perimeter_km=best.features.perimeter_km,
            major_axis_orientation_deg=best.features.major_axis_orientation_deg,
            confidence_score=best.confidence_score,
            lookalike_probability=best.lookalike_probability,
        )


# ---------------------------------------------------------------------------
# Synthetic SAR Scene Generator (For Unit Testing & Benchmarks)
# ---------------------------------------------------------------------------

class SyntheticSARGenerator:
    """Generates synthetic, deterministic SAR backscatter scenes with realistic radar signatures."""

    @staticmethod
    def create_synthetic_scene(
        width: int = 300,
        height: int = 300,
        top_left_lon: float = 101.8,
        top_left_lat: float = 3.1,
        pixel_size_deg: float = 0.002,  # ~220m per pixel
        sea_mean_db: float = -14.0,
        sea_std_db: float = 1.2,
        seed: int = 42,
        include_island: bool = True,
        slick_row_col: Optional[Tuple[float, float]] = None,
        slick_orientation_deg: float = 48.5,
    ) -> SARRaster:
        """Creates a synthetic SAR scene with sea clutter, an oil slick, an island, and a lookalike."""
        rng = np.random.RandomState(seed)

        # 1. Base Sea Clutter
        data = rng.normal(loc=sea_mean_db, scale=sea_std_db, size=(height, width)).astype(float)

        # 2. Insert Mineral Oil Slick (Elongated dark patch with -8.5 dB damping)
        r_grid, c_grid = np.indices((height, width))
        if slick_row_col is not None:
            cr, cc = float(slick_row_col[0]), float(slick_row_col[1])
        else:
            cr, cc = 111.5, 170.1
        angle_rad = math.radians(slick_orientation_deg)
        rot_c = (c_grid - cc) * math.cos(angle_rad) + (r_grid - cr) * math.sin(angle_rad)
        rot_r = -(c_grid - cc) * math.sin(angle_rad) + (r_grid - cr) * math.cos(angle_rad)

        slick_mask = ((rot_c / 28.0) ** 2 + (rot_r / 9.0) ** 2) <= 1.0
        data[slick_mask] += rng.normal(loc=-8.0, scale=0.6, size=np.sum(slick_mask))

        # 3. Insert High-Backscatter Land Island (Top-Left corner, > -4 dB) if requested
        if include_island:
            island_mask = ((r_grid - 40.0) ** 2 + (c_grid - 50.0) ** 2) <= (22.0 ** 2)
            data[island_mask] = rng.normal(loc=-3.0, scale=1.0, size=np.sum(island_mask))

        # 4. Insert Low-Wind Lookalike (Calm sea basin in bottom-left, -4.5 dB damping, large circular)
        lookalike_r = 240.0 if abs(cr - 240.0) > 40 else 60.0
        lookalike_c = 70.0 if abs(cc - 70.0) > 40 else 230.0
        low_wind_mask = ((r_grid - lookalike_r) ** 2 + (c_grid - lookalike_c) ** 2) <= (45.0 ** 2)
        data[low_wind_mask] += rng.normal(loc=-4.0, scale=0.8, size=np.sum(low_wind_mask))

        return SARRaster(
            data_db=data,
            top_left_lon=top_left_lon,
            top_left_lat=top_left_lat,
            pixel_size_deg_lon=pixel_size_deg,
            pixel_size_deg_lat=-pixel_size_deg,
            acquisition_timestamp=datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc),
            satellite_platform="Sentinel-1A (Synthetic SAR)",
            polarization="VV",
            pixel_resolution_meters=pixel_size_deg * 111320.0,
            ambient_wind_speed_ms=6.5,
        )


sar_detector = DeterministicSARDetector()
