# Experience Curve Calculations

## Mathematical Foundation

The experience curve follows a power function:

```
C_n = C_1 × n^(-b)
```

Where:
- C_n = Cost of nth unit
- C_1 = Cost of first unit
- n = Cumulative production
- b = Learning coefficient = -log₂(1 - experience rate)

## Common Experience Rates by Industry

| Industry | Typical Rate | Notes |
|----------|-------------|-------|
| Semiconductors | 25-30% | Rapid process innovation |
| Aircraft assembly | 15-20% | Complex, labor-intensive |
| Chemicals | 10-15% | Capital-intensive, continuous |
| Automotive | 15-25% | Mixed automation levels |
| Electronics assembly | 20-25% | High modularity |

## Detailed Calculation Example

**Given:** First unit costs $10,000, experience rate = 20%

Find cost of 1,000,000th unit:

1. Calculate b: b = -log₂(0.80) = 0.3219
2. C_1,000,000 = $10,000 × 1,000,000^(-0.3219)
3. C_1,000,000 = $10,000 × 0.0064 = $64

## Cost Gap Analysis

Compare competitor positions:

| Firm | Cumulative Units | Cost Position | Cost Gap vs Leader |
|------|-----------------|---------------|-------------------|
| Leader | 10M | $64 (base) | — |
| Follower A | 5M | $80 | +25% |
| Follower B | 2.5M | $100 | +56% |
| New Entrant | 100K | $400 | +525% |

## Strategic Pricing Thresholds

**Maximum Aggressive Price:** Set price at your projected cost when competitor reaches same cumulative volume. This prices them out permanently.

Example: If competitor is at 5M units ($80 cost) and you project $50 cost at 10M units, you can price at $55-60 to block their expansion.

## Limitations and Edge Cases

### When Experience Curves Fail

1. **Technology discontinuities:** New processes reset experience to zero
2. **Input cost volatility:** Commodity spikes overwhelm learning effects
3. **Product customization:** Fragmented production dilutes experience
4. **Union work rules:** Prevent efficiency improvements
5. **Regulatory changes:** Compliance costs offset learning

### Experience Curve vs. Economies of Scale

| Factor | Experience Curve | Economies of Scale |
|--------|---------------|-------------------|
| Driver | Cumulative production | Rate of production |
| Timeframe | Long-term strategic | Short-term operational |
| Reversibility | Irreversible learning | Reversible capacity |
| Competitive implication | Sustainable advantage | Contestable advantage |

### Combining Multiple Products

When products share components or processes, calculate **weighted average experience**:

```
Shared Experience = Σ (Component_i × Shared Volume_i) / Total Component Volume
```

This enables faster cost reduction in product families than single products alone.