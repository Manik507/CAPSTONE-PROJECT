from datetime import datetime, timezone
from database.db import db
from models.event import Event
from models.leaderboard import Leaderboard
from models.participant import Participant
from models.reward_history import RewardHistory


def _get_or_create_leaderboard(user_id):
    entry = Leaderboard.query.filter_by(user_id=user_id).first()
    if not entry:
        entry = Leaderboard(user_id=user_id, xp=0, trophies=0)
        db.session.add(entry)
    return entry


def award_winner_reward(user_id, event_id, rank, prize_name):
    """Award 100 XP and 1 Trophy for winning a prize (if PAID)."""
    # Check if already awarded
    existing = RewardHistory.query.filter_by(user_id=user_id, event_id=event_id, reward_type="WINNING").first()
    if existing:
        return None

    participant = Participant.query.filter_by(user_id=user_id, event_id=event_id).first()
    if not participant or participant.payment_status != "PAID":
        return None

    entry = _get_or_create_leaderboard(user_id)
    entry.xp += 100
    entry.trophies += 1

    reward = RewardHistory(
        user_id=user_id,
        event_id=event_id,
        reward_type="WINNING",
        xp_awarded=100,
        trophies_awarded=1,
        description=f"🏆 Winner: {prize_name} (Rank {rank})"
    )
    db.session.add(reward)
    db.session.commit()
    return reward


def check_participation_rewards(user_id):
    """Check for ended events where the user was a PAID participant but hasn't received 30 XP."""
    now = datetime.now(timezone.utc)
    
    # Events where user participated and PAID
    participations = Participant.query.filter_by(user_id=user_id, payment_status="PAID").all()
    
    new_rewards = []
    for p in participations:
        event = p.event
        if not event or event.end_date > now:
            continue
        
        # Check if already rewarded for participation
        existing = RewardHistory.query.filter_by(user_id=user_id, event_id=event.id, reward_type="PARTICIPATION").first()
        if existing:
            continue
        
        # Award 30 XP
        entry = _get_or_create_leaderboard(user_id)
        entry.xp += 30
        
        reward = RewardHistory(
            user_id=user_id,
            event_id=event.id,
            reward_type="PARTICIPATION",
            xp_awarded=30,
            trophies_awarded=0,
            description=f"🎉 Participation Reward: {event.title}"
        )
        db.session.add(reward)
        new_rewards.append(reward)
    
    if new_rewards:
        db.session.commit()
    
    return new_rewards
