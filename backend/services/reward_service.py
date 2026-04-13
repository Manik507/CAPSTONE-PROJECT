from datetime import datetime, timezone
from database.db import db
from models.event import Event
from models.leaderboard import Leaderboard
from models.participant import Participant
from models.reward_history import RewardHistory


def _get_or_create_leaderboard(user_id):
    entry = Leaderboard.query.filter_by(user_id=user_id).first()
    if not entry:
        entry = Leaderboard(user_id=user_id, xp=0, trophies=0, badge="Wood")
        db.session.add(entry)
    return entry


def award_finalization_rewards(event_id, winner_uids):
    """
    Called when an event is finalized.
    Winners receive 100 XP, 1 Trophy.
    All other PAID participants receive 50 XP, 0 Trophies.
    """
    event = Event.query.get(event_id)
    if not event:
        return

    # Get all PAID participants
    participants = Participant.query.filter_by(event_id=event_id, payment_status="PAID").all()
    
    for p in participants:
        is_winner = p.user_id in winner_uids
        xp = 100 if is_winner else 50
        trophies = 1 if is_winner else 0
        reward_type = "WINNING" if is_winner else "PARTICIPATION"
        
        # Check if already awarded for this event (avoid double rewarding if finalist update happens)
        existing = RewardHistory.query.filter_by(user_id=p.user_id, event_id=event_id, reward_type=reward_type).first()
        if existing:
            continue
            
        entry = _get_or_create_leaderboard(p.user_id)
        entry.xp += xp
        entry.trophies += trophies
        
        # Simple badge upgrade logic
        if entry.trophies >= 20: entry.badge = "Platinum"
        elif entry.trophies >= 10: entry.badge = "Gold"
        elif entry.trophies >= 5: entry.badge = "Silver"
        elif entry.trophies >= 2: entry.badge = "Bronze"

        desc = f"🏆 Winner: {event.title}" if is_winner else f"🎉 Participation: {event.title}"
        
        reward = RewardHistory(
            user_id=p.user_id,
            event_id=event_id,
            reward_type=reward_type,
            xp_awarded=xp,
            trophies_awarded=trophies,
            description=desc
        )
        db.session.add(reward)

    db.session.commit()

def award_winner_reward(user_id, event_id, rank, prize_name):
    """Legacy: Award 100 XP and 1 Trophy for winning a prize (if PAID). Only used if called individually."""
    # (Existing logic but with badge update)
    existing = RewardHistory.query.filter_by(user_id=user_id, event_id=event_id, reward_type="WINNING").first()
    if existing: return None
    participant = Participant.query.filter_by(user_id=user_id, event_id=event_id).first()
    if not participant or participant.payment_status != "PAID": return None
    
    entry = _get_or_create_leaderboard(user_id)
    entry.xp += 100
    entry.trophies += 1
    
    # Badge upgrade
    if entry.trophies >= 20: entry.badge = "Platinum"
    elif entry.trophies >= 10: entry.badge = "Gold"
    elif entry.trophies >= 5: entry.badge = "Silver"
    elif entry.trophies >= 2: entry.badge = "Bronze"

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
