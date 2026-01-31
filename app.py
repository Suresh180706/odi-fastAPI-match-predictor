from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import joblib

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

model = joblib.load("model.pkl")
df = pd.read_csv("ODI_Match_info.csv")

known_teams = set(df["team1"]).union(set(df["team2"]))
venues = sorted(df["venue"].dropna().unique())

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "venues": venues}
    )

@app.post("/predict")
async def predict(request: Request):
    data = await request.json()

    team1 = data["team1"].strip()
    team2 = data["team2"].strip()

    if team1.lower() == team2.lower():
        return {"error": "Team 1 and Team 2 cannot be the same"}

    team1_known = team1 in known_teams
    team2_known = team2 in known_teams

    # CASE 1: BOTH KNOWN → ML
    if team1_known and team2_known:
        input_df = pd.DataFrame([{
            "team1": team1,
            "team2": team2,
            "venue": data["venue"],
            "toss_winner": data["toss_winner"],
            "toss_decision": data["toss_decision"],
            "season_type": data["season"],
            "dl_applied": 0,
            "team1_strength": 0.5,
            "team2_strength": 0.5,
            "team1_bat_strength": 1,
            "team2_bat_strength": 1,
            "team1_bowl_strength": 1,
            "team2_bowl_strength": 1,
            "venue_strength": 0.5
        }])

        probs = model.predict_proba(input_df)[0]
        classes = model.classes_

        prob_map = dict(zip(classes, probs))
        t1_prob = round(prob_map.get(team1, 0) * 100, 2)
        t2_prob = round(prob_map.get(team2, 0) * 100, 2)

        winner = team1 if t1_prob >= t2_prob else team2

        return {
            "winner": winner,
            "team1": team1,
            "team2": team2,
            "team1_confidence": t1_prob,
            "team2_confidence": t2_prob,
            "reason": "ML prediction based on head-to-head & venue stats"
        }

    # CASE 2: ONE KNOWN
    if team1_known and not team2_known:
        return {
            "winner": team1,
            "team1": team1,
            "team2": team2,
            "team1_confidence": 75,
            "team2_confidence": 25,
            "reason": "Team 1 is historically present in dataset"
        }

    if team2_known and not team1_known:
        return {
            "winner": team2,
            "team1": team1,
            "team2": team2,
            "team1_confidence": 25,
            "team2_confidence": 75,
            "reason": "Team 2 is historically present in dataset"
        }

    # CASE 3: BOTH UNKNOWN
    winner = team1 if data["toss_winner"] == "Team 1" else team2

    return {
        "winner": winner,
        "team1": team1,
        "team2": team2,
        "team1_confidence": 60 if winner == team1 else 40,
        "team2_confidence": 60 if winner == team2 else 40,
        "reason": "Rule-based prediction using toss & venue"
    }
