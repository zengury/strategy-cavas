---
name: Competitive Game Theory Analysis
description: Analyze competitive scenarios between rational actors who cannot communicate or form binding agreements. Use when modeling non-cooperative behavior in business competition, pricing wars, or strategic interactions where trust is absent and individual rationality leads to collectively suboptimal outcomes.
---

# Competitive Game Theory Analysis

Apply the Prisoner's Dilemma framework to predict strategic behavior in competitive scenarios with communication barriers.

## When to Use

- Two or more competitors must make simultaneous decisions without coordination
- Binding agreements are impossible or unenforceable
- Individual incentives conflict with collective optimal outcomes
- Analyzing price wars, market entry decisions, or resource competition

## Execution Steps

### 1. Setup the Payoff Matrix

Define outcomes for each actor based on their choices:

|  | Partner Cooperates | Partner Defects |
|--|--|--|
| **You Cooperate** | Mutual cooperation payoff | Sucker payoff (worst) |
| **You Defect** | Temptation payoff (best individual) | Mutual defection payoff |

### 2. Identify the Dominant Strategy

For each actor, determine the choice that maximizes payoff regardless of the other's action:
- If partner cooperates: Does defecting yield higher payoff?
- If partner defects: Does defecting yield higher payoff?
- If yes to both: Defection is the dominant strategy

### 3. Predict the Nash Equilibrium

When both actors follow dominant strategies, the resulting outcome is the equilibrium prediction—even if collectively suboptimal.

### 4. Assess Business Implications

Document why cooperation fails without external mechanisms:
- Lack of enforcement for agreements
- Incentive to free-ride on others' cooperation
- Short-term individual gain vs. long-term collective benefit

## Key Insight

Rational individual behavior systematically produces worse collective outcomes. Cooperation requires either repeated interaction (future consequences) or binding external enforcement.

## References

See `prisoners-dilemma-payoffs.md` for detailed payoff structures and business applications.