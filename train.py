import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from pathlib import Path
import numpy as np
from sqlmodel import Session, select
from models import engine, PlayerStats, TeamStats


class OtterspredictionNet(nn.Module):
    """Neural network for predicting Otters game outcomes and player performance"""
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()  # For binary classification (win/loss)
        )

    def forward(self, x):
        return self.net(x)


def load_training_data():
    """Load player stats and team stats for training"""
    with Session(engine) as session:
        player_stats = session.exec(select(PlayerStats)).all()
        team_stats = session.exec(select(TeamStats)).all()

    features = []
    labels = []

    for stat in player_stats:
        # Features: games_played, goals, assists, plus_minus
        feature = [
            stat.games_played,
            stat.goals,
            stat.assists,
            stat.plus_minus,
            stat.penalty_minutes
        ]
        features.append(feature)
        # Label: total points (simple regression target)
        labels.append(stat.points)

    return np.array(features, dtype=np.float32), np.array(labels, dtype=np.float32)


def train_model(epochs: int = 100, batch_size: int = 32, learning_rate: float = 0.001):
    """Train the prediction model"""
    print("Loading training data...")
    X, y = load_training_data()

    if len(X) == 0:
        print("No training data available. Please populate the database first.")
        return

    print(f"Training on {len(X)} samples with {X.shape[1]} features")

    # Normalize features
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1  # Avoid division by zero
    X_normalized = (X - X_mean) / X_std

    # Normalize labels
    y_mean = y.mean()
    y_std = y.std()
    y_normalized = (y - y_mean) / y_std

    # Create dataset and dataloader
    dataset = TensorDataset(
        torch.FloatTensor(X_normalized),
        torch.FloatTensor(y_normalized)
    )
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = OtterspredictionNet(X.shape[1]).to(device)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    # Training loop
    print(f"Training on {device}...")
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in dataloader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs.squeeze(), batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.6f}")

    # Save model
    model_path = Path("models")
    model_path.mkdir(exist_ok=True)
    torch.save(model.state_dict(), model_path / "otters_prediction.pth")
    print(f"Model saved to {model_path / 'otters_prediction.pth'}")

    return model


if __name__ == "__main__":
    train_model(epochs=100, batch_size=16)
