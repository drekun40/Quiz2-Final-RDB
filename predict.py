import torch
import torch.nn as nn
from pathlib import Path
import numpy as np
from train import OtterspredictionNet


class PredictionEngine:
    """Engine for making predictions using the trained model"""

    def __init__(self, model_path: str = "models/otters_prediction.pth", input_dim: int = 5):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = OtterspredictionNet(input_dim).to(self.device)

        if Path(model_path).exists():
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print(f"Model loaded from {model_path}")
        else:
            print(f"Warning: Model not found at {model_path}")

        # Placeholder for training normalization stats (should be saved during training)
        self.X_mean = None
        self.X_std = None

    def predict_player_points(self, features: np.ndarray) -> float:
        """
        Predict player points given features
        Features: [games_played, goals, assists, plus_minus, penalty_minutes]
        """
        if features.shape[0] != 5:
            raise ValueError("Expected 5 features")

        # Normalize if stats available
        if self.X_mean is not None:
            features = (features - self.X_mean) / (self.X_std + 1e-8)

        with torch.no_grad():
            X_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            prediction = self.model(X_tensor).item()

        return prediction

    def predict_game_outcome(self, home_stats: np.ndarray, away_stats: np.ndarray) -> dict:
        """
        Predict game outcome based on team statistics
        Returns probability of home team winning
        """
        # Combine stats for prediction
        combined_features = np.concatenate([home_stats, away_stats])

        with torch.no_grad():
            X_tensor = torch.FloatTensor(combined_features).unsqueeze(0).to(self.device)
            home_win_probability = self.model(X_tensor).item()

        return {
            "home_win_probability": home_win_probability,
            "away_win_probability": 1 - home_win_probability,
            "predicted_winner": "Home" if home_win_probability > 0.5 else "Away"
        }


def predict_player_stats(games_played: int, goals: int, assists: int, plus_minus: int, pim: int):
    """
    Convenience function to predict player points
    """
    engine = PredictionEngine()
    features = np.array([games_played, goals, assists, plus_minus, pim], dtype=np.float32)
    prediction = engine.predict_player_points(features)
    return {
        "input": {
            "games_played": games_played,
            "goals": goals,
            "assists": assists,
            "plus_minus": plus_minus,
            "penalty_minutes": pim
        },
        "predicted_points": prediction
    }


if __name__ == "__main__":
    # Example usage
    result = predict_player_stats(
        games_played=60,
        goals=25,
        assists=30,
        plus_minus=5,
        pim=45
    )
    print(result)
