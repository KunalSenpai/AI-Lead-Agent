from app.models.lead import Lead, LeadAnalysis, LeadScore


def score_lead(
    lead: Lead,
    analysis: LeadAnalysis
) -> LeadScore:

    score = 0
    reasons = []

    # -----------------------------------------
    # 1. Company size
    # -----------------------------------------

    if analysis.company_size is not None:

        if analysis.company_size >= 51:
            score += 20
            reasons.append(
                f"Company has {analysis.company_size} employees"
            )

        elif analysis.company_size >= 26:
            score += 15
            reasons.append(
                f"Company has {analysis.company_size} employees"
            )

        elif analysis.company_size >= 11:
            score += 10
            reasons.append(
                f"Company has {analysis.company_size} employees"
            )

        else:
            score += 5
            reasons.append(
                f"Company has {analysis.company_size} employees"
            )

    # -----------------------------------------
    # 2. Lead volume
    # -----------------------------------------

    if analysis.lead_volume is not None:

        if analysis.lead_volume >= 500:
            score += 25
            reasons.append(
                f"High lead volume: {analysis.lead_volume} leads/month"
            )

        elif analysis.lead_volume >= 201:
            score += 20
            reasons.append(
                f"High lead volume: {analysis.lead_volume} leads/month"
            )

        elif analysis.lead_volume >= 101:
            score += 15
            reasons.append(
                f"Lead volume: {analysis.lead_volume} leads/month"
            )

        elif analysis.lead_volume >= 51:
            score += 10
            reasons.append(
                f"Lead volume: {analysis.lead_volume} leads/month"
            )

        else:
            score += 5

    # -----------------------------------------
    # 3. Urgency
    # -----------------------------------------

    urgency = analysis.urgency.lower()

    if urgency == "high":
        score += 20
        reasons.append("Lead indicates high urgency")

    elif urgency == "medium":
        score += 10
        reasons.append("Lead indicates medium urgency")

    elif urgency == "low":
        score += 5
        reasons.append("Lead indicates low urgency")

    # -----------------------------------------
    # 4. Problem fit
    # -----------------------------------------

    problem = analysis.problem.lower()

    automation_keywords = [
        "manual",
        "automation",
        "automate",
        "repetitive",
        "qualification",
        "reporting",
        "routing",
        "workflow",
        "data entry",
        "lead management",
    ]

    if any(
        keyword in problem
        for keyword in automation_keywords
    ):
        score += 20
        reasons.append(
            "Problem appears well suited to automation"
        )

    else:
        score += 5

    # -----------------------------------------
    # 5. Decision maker
    # -----------------------------------------

    job_title = (lead.job_title or "").lower()

    decision_maker_keywords = [
        "founder",
        "ceo",
        "owner",
        "director",
        "cto",
        "coo",
        "vp",
        "head",
    ]

    if any(
        keyword in job_title
        for keyword in decision_maker_keywords
    ):
        score += 15
        reasons.append(
            f"Contact appears to be a decision maker: {lead.job_title}"
        )

    else:
        score += 5

    # -----------------------------------------
    # Determine category
    # -----------------------------------------

    if score >= 75:
        category = "Hot"

    elif score >= 50:
        category = "Warm"

    else:
        category = "Cold"

    return LeadScore(
        score=score,
        category=category,
        reasons=reasons
    )