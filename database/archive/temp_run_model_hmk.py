# -*- coding: utf-8 -*-
import io, json, sys
sys.path.insert(0, r'database')
import importlib

import feature_extractor as fe
import model_engine as me
import fusion_engine as fus

adapter = {
    "match_context": {
        "match_type": "normal_league",
        "match_importance": "normal",
        "data_confidence": 0.85,
        "market_efficiency": 0.7,
        "home_advantage_modifier": 1.05,
        "weight_profile": "normal",
        "derby": False,
        "is_qualifier": False,
        "season_phase": "season_opening"
    },
    "team_basic": {
        "home": {"name": "横滨水手", "rank": 5, "points": 0},
        "away": {"name": "鹿岛鹿角", "rank": 3, "points": 0}
    },
    "performance": {
        "home": {"form_score": 0.15, "trend": "stable"},
        "away": {"form_score": -0.10, "trend": "declining"}
    },
    "tactical": {"home_formation": "", "away_formation": "", "tactical_advantage": ""},
    "players": {"home": [], "away": []},
    "injury": {
        "home": {"players_out": 1, "key_player_missing": True, "impact_score": 0.15,
                 "details": ["7号前锋远野大弥-伤病"]},
        "away": {"players_out": 2, "key_player_missing": True, "impact_score": 0.20,
                 "details": ["2号后卫安西幸辉-伤病", "14号中场樋口雄太-腓骨骨折"]}
    },
    "schedule": {"home_rest_days": 6, "away_rest_days": 6, "away_travel_km": 0,
                 "home_double_week": False, "away_double_week": False},
    "environment": {"weather": {"temperature_c": 30, "rain_probability": 0.3, "wind_kmh": 0,
                                "impact_on_goals": "neutral"},
                    "pitch_type": "natural", "referee": {}},
    "odds": {"source": "titansports", "snapshots": [{"home": 3.90, "draw": 3.32, "away": 1.75}]},
    "market": {"overheating": False, "overheating_score": 0.0, "consensus_level": 0.6,
               "trend_pattern": "unknown", "odds_model_conflict": False, "conflict_gap_pp": 0.0,
               "market_efficiency_score": 0.7, "alerts": []},
    "model": {}, "prediction": {}
}

with io.open(r'database/predictions/20260807_横滨vs鹿岛_adapter.json', 'w', encoding='utf-8') as f:
    json.dump(adapter, f, ensure_ascii=False, indent=2)

features = fe.extract(adapter)['features']
print('FEATURES:', json.dumps(features, ensure_ascii=False))
model = me.predict(features)
print('LAMBDA:', model['lambda'])
print('MC:', json.dumps(model['mc'], ensure_ascii=False))
print('TOP10 SCORES:', json.dumps(model['scores'][:10], ensure_ascii=False))
print('TOP3:', model['top3_scores'])

fusion = fus.fuse(model['mc'], features, 'normal_league')
print('FUSION prediction:', json.dumps(fusion['prediction'], ensure_ascii=False))
print('FUSION scores:', json.dumps(fusion['scores'], ensure_ascii=False))
print('FUSION risks:', json.dumps(fusion.get('risks', []), ensure_ascii=False))
