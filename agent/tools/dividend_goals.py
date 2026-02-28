"""Tool: CRUD management for dividend income goals."""

import asyncio
import time

from langchain_core.tools import tool

from agent.database import create_goal, delete_goal, get_goals, update_goal


@tool
async def dividend_goal_manager(
    action: str = "list",
    target_monthly: float = 0.0,
    target_annual: float = 0.0,
    currency: str = "USD",
    deadline: str = "",
    notes: str = "",
    goal_id: str = "",
) -> dict:
    """Manage dividend income goals. Create, view, update, or delete income targets.
    Use this when the user wants to set a dividend income goal, check their goals,
    update a target, or remove a goal.

    Args:
        action: The operation — "create", "list", "update", or "delete".
        target_monthly: Monthly income target (e.g. 2000.0). Used with create/update.
        target_annual: Annual income target. If omitted, computed from monthly × 12.
        currency: Currency code (default "USD"). Used with create.
        deadline: Target date in YYYY-MM-DD format. Used with create/update.
        notes: Free-text notes. Used with create/update.
        goal_id: ID of the goal to update or delete.
    """
    start = time.time()

    try:
        if action == "create":
            if target_monthly <= 0 and target_annual <= 0:
                return {
                    "status": "error",
                    "data": None,
                    "message": "Please provide a target_monthly or target_annual amount greater than zero.",
                    "execution_time": round(time.time() - start, 3),
                }
            goal = await asyncio.to_thread(
                create_goal,
                target_monthly=target_monthly,
                target_annual=target_annual,
                currency=currency,
                deadline=deadline,
                notes=notes,
            )
            return {
                "status": "success",
                "data": {"action": "created", "goal": goal},
                "message": f"Goal created: ${goal['target_monthly']:,.0f}/month (${goal['target_annual']:,.0f}/year) in {goal['currency']}",
                "execution_time": round(time.time() - start, 3),
            }

        elif action == "list":
            goals = await asyncio.to_thread(get_goals)
            return {
                "status": "success",
                "data": {"action": "list", "goals": goals, "count": len(goals)},
                "message": f"You have {len(goals)} dividend income goal(s)." if goals else "No dividend goals set yet.",
                "execution_time": round(time.time() - start, 3),
            }

        elif action == "update":
            if not goal_id:
                # If no goal_id, try updating the most recent goal
                goals = await asyncio.to_thread(get_goals)
                if not goals:
                    return {
                        "status": "error",
                        "data": None,
                        "message": "No goals found to update. Create one first.",
                        "execution_time": round(time.time() - start, 3),
                    }
                goal_id = goals[0]["id"]

            kwargs = {}
            if target_monthly > 0:
                kwargs["target_monthly"] = target_monthly
                if target_annual <= 0:
                    kwargs["target_annual"] = target_monthly * 12
            if target_annual > 0:
                kwargs["target_annual"] = target_annual
                if target_monthly <= 0:
                    kwargs["target_monthly"] = target_annual / 12
            if deadline:
                kwargs["deadline"] = deadline
            if notes:
                kwargs["notes"] = notes

            updated = await asyncio.to_thread(update_goal, goal_id, **kwargs)
            if not updated:
                return {
                    "status": "error",
                    "data": None,
                    "message": f"Goal with ID {goal_id} not found.",
                    "execution_time": round(time.time() - start, 3),
                }
            return {
                "status": "success",
                "data": {"action": "updated", "goal": updated},
                "message": f"Goal updated: ${updated['target_monthly']:,.0f}/month",
                "execution_time": round(time.time() - start, 3),
            }

        elif action == "delete":
            if not goal_id:
                goals = await asyncio.to_thread(get_goals)
                if not goals:
                    return {
                        "status": "error",
                        "data": None,
                        "message": "No goals found to delete.",
                        "execution_time": round(time.time() - start, 3),
                    }
                goal_id = goals[0]["id"]

            deleted = await asyncio.to_thread(delete_goal, goal_id)
            if not deleted:
                return {
                    "status": "error",
                    "data": None,
                    "message": f"Goal with ID {goal_id} not found.",
                    "execution_time": round(time.time() - start, 3),
                }
            return {
                "status": "success",
                "data": {"action": "deleted", "goal_id": goal_id},
                "message": f"Goal {goal_id} deleted successfully.",
                "execution_time": round(time.time() - start, 3),
            }

        else:
            return {
                "status": "error",
                "data": None,
                "message": f"Unknown action '{action}'. Use create, list, update, or delete.",
                "execution_time": round(time.time() - start, 3),
            }

    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Goal manager error: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
