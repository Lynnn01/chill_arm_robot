"""
agent/scoring.py — Robotic Arm Scoring System
Non-mission tasks (gestures, single actions, dance) = 1 point
Mission tasks (stacking towers, unstacking, sorting) = 10 points
"""

_CURRENT_SCORE = 0
_SCORE_LISTENERS = []

MISSION_KEYWORDS = {
    "stack", "unstack", "tower", "sort", "ซ้อน", "หอคอย",
    "แกะกล่อง", "แยกสี", "สร้างหอคอย", "ต่อยอด", "จัดเก็บเข้ามุม"
}


def get_score() -> int:
    """Returns current total score."""
    return _CURRENT_SCORE


def reset_score() -> int:
    """Resets total score to 0 and notifies listeners."""
    global _CURRENT_SCORE
    _CURRENT_SCORE = 0
    _notify_listeners()
    return _CURRENT_SCORE


def register_score_listener(callback):
    """Registers a listener function to be called when score updates: callback(new_score)."""
    if callback not in _SCORE_LISTENERS:
        _SCORE_LISTENERS.append(callback)


def _notify_listeners():
    for cb in _SCORE_LISTENERS:
        try:
            cb(_CURRENT_SCORE)
        except Exception:
            pass


def add_score(points: int, reason: str = "") -> int:
    """Adds points to current score and notifies listeners."""
    global _CURRENT_SCORE
    if points > 0:
        _CURRENT_SCORE += points
        try:
            print(f"🏆 <SYSTEM>: [Score] +{points} แต้ม ({reason}) | คะแนนรวม: {_CURRENT_SCORE} แต้ม")
        except UnicodeEncodeError:
            print(f"[Score] +{points} pts ({reason}) | Total: {_CURRENT_SCORE} pts")
        _notify_listeners()
    return _CURRENT_SCORE


def evaluate_task_points(tasks: list, plan_summary: str = "") -> tuple:
    """
    Evaluates completed tasks:
    - Mission (+10 pts): Tower Stacking, Unstacking, Sorting by Color, Multi-step Stacking
    - Non-Mission (+1 pt): Single Grab/Show, Dance, Gesture, Rock-Paper-Scissors, Scan, Move
    """
    if not tasks:
        return 0, "No tasks"

    summary_lower = (plan_summary or "").lower()
    tool_names = [str(t.get("tool", "")).strip().replace("()", "").rstrip("()").strip() for t in tasks]

    # Check for Mission conditions
    has_mission_keyword = any(kw in summary_lower for kw in MISSION_KEYWORDS)
    has_sort = "sort_by_color" in tool_names or "clean_desk" in tool_names
    has_unstack = "unstack_and_grab" in tool_names
    
    # Stacking intent: grab_object followed by move_to with target or multiple actions
    has_stack_action = False
    for t in tasks:
        args = t.get("args") or {}
        target_name = str(args.get("target_name", "")).lower()
        if args.get("smart_place") or any(k in target_name for k in ["cube", "block", "stack", "กล่อง", "ซ้อน", "red", "green", "blue", "yellow"]):
            has_stack_action = True
            break

    is_mission = has_mission_keyword or has_sort or has_unstack or has_stack_action

    if is_mission:
        return 10, "Mission Complete"
    return 1, "Task Complete"
