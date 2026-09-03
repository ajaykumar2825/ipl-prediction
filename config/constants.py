"""Global constants — single source of truth for teams, venues, branding."""

APP_NAME = "IPL Sports Analytics Platform"
APP_SUBTITLE = "Enterprise Cricket Intelligence Dashboard"
APP_VERSION = "2.1.0"

BRAND = {
    "navy": "#0A1931",
    "royal": "#1B4FFF",
    "accent": "#FF6B1A",
    "emerald": "#00C389",
    "white": "#FFFFFF",
    "light": "#F4F6FB",
    "muted": "#8A94A6",
    "card_border": "rgba(27,79,255,0.12)",
}

TEAMS = [
    "Mumbai Indians",
    "Chennai Super Kings",
    "Royal Challengers Bengaluru",
    "Kolkata Knight Riders",
    "Delhi Capitals",
    "Punjab Kings",
    "Rajasthan Royals",
    "Sunrisers Hyderabad",
    "Gujarat Titans",
    "Lucknow Super Giants",
]

TEAM_SHORT = {
    "Mumbai Indians": "MI",
    "Chennai Super Kings": "CSK",
    "Royal Challengers Bengaluru": "RCB",
    "Kolkata Knight Riders": "KKR",
    "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS",
    "Rajasthan Royals": "RR",
    "Sunrisers Hyderabad": "SRH",
    "Gujarat Titans": "GT",
    "Lucknow Super Giants": "LSG",
}

TEAM_COLORS = {
    "Mumbai Indians": "#004BA0",
    "Chennai Super Kings": "#FFC916",
    "Royal Challengers Bengaluru": "#EC1C24",
    "Kolkata Knight Riders": "#3A225D",
    "Delhi Capitals": "#0078BC",
    "Punjab Kings": "#ED1B24",
    "Rajasthan Royals": "#EA1A85",
    "Sunrisers Hyderabad": "#F7A721",
    "Gujarat Titans": "#1B1B1B",
    "Lucknow Super Giants": "#0057E2",
}

VENUES = [
    "Wankhede Stadium, Mumbai",
    "Eden Gardens, Kolkata",
    "M. Chinnaswamy Stadium, Bengaluru",
    "MA Chidambaram Stadium, Chennai",
    "Arun Jaitley Stadium, Delhi",
    "Rajiv Gandhi Stadium, Hyderabad",
    "Sawai Mansingh Stadium, Jaipur",
    "Narendra Modi Stadium, Ahmedabad",
    "Ekana Stadium, Lucknow",
    "PCA Stadium, Mohali",
    "D Y Patil Stadium, Navi Mumbai",
    "MCA Stadium, Pune",
]

VENUE_AVG = {
    "Wankhede Stadium, Mumbai": 172,
    "Eden Gardens, Kolkata": 166,
    "M. Chinnaswamy Stadium, Bengaluru": 178,
    "MA Chidambaram Stadium, Chennai": 158,
    "Arun Jaitley Stadium, Delhi": 165,
    "Rajiv Gandhi Stadium, Hyderabad": 163,
    "Sawai Mansingh Stadium, Jaipur": 160,
    "Narendra Modi Stadium, Ahmedabad": 168,
    "Ekana Stadium, Lucknow": 155,
    "PCA Stadium, Mohali": 167,
    "D Y Patil Stadium, Navi Mumbai": 164,
    "MCA Stadium, Pune": 162,
}

SEASONS = list(range(2008, 2026))

ROLES = ["Batter", "Bowler", "All-Rounder", "Wicket-Keeper"]

REQUIRED_MATCH_COLS = [
    "match_id", "season", "date", "venue", "team1", "team2",
    "toss_winner", "toss_decision", "winner", "result",
    "win_by_runs", "win_by_wickets", "player_of_match",
    "team1_score", "team2_score", "team1_wickets", "team2_wickets",
]

REQUIRED_DELIVERY_COLS = [
    "match_id", "season", "inning", "over", "ball",
    "batter", "bowler", "batting_team", "bowling_team",
    "runs_off_bat", "extras", "total_runs", "is_wicket",
    "dismissal_kind", "venue",
]

REQUIRED_PLAYER_COLS = [
    "player_id", "player_name", "role", "batting_style",
    "bowling_style", "team", "nationality", "age",
]

REQUIRED_VENUE_COLS = [
    "venue", "matches", "avg_first_innings", "avg_second_innings",
    "highest_total", "lowest_defended", "highest_chase",
    "bat_first_win_pct", "chase_win_pct", "toss_bat_pct",
    "pitch_class",
]
