
# engine/policy.py

POLICIES = {
    "under_5": {
        1: "BLOCK",
        2: "BLOCK",
        3: "BLOCK"
    },
    "5_8": {
        1: "REVIEW",
        2: "BLOCK",
        3: "BLOCK"
    },
    "9_12": {
        1: "ALLOW",
        2: "REVIEW",
        3: "BLOCK"
    },
    "13_17": {
        1: "ALLOW",
        2: "REVIEW",
        3: "BLOCK"
    }
}

ACTION_PRIORITY = {
    "ALLOW": 1,
    "REVIEW": 2,
    "BLOCK": 3
}


def evaluate(matches, age_group):

    if age_group not in POLICIES:
        raise ValueError("Invalid age group")

    policy = POLICIES[age_group]

    results = []

    for match in matches:

        severity = int(match["severity"])

        action = policy[severity]

        results.append({
            **match,
            "action": action
        })

    final_action = max(
        (
            item["action"]
            for item in results
        ),
        key=lambda action: ACTION_PRIORITY[action],
        default="ALLOW"
    )

    return {
        "age_group": age_group,
        "final_action": final_action,
        "matches": results,
        "total_matches": len(results)
    }
