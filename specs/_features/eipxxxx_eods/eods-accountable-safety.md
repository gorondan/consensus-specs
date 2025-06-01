# Accountable safety in eODS

_tl;dr;
In this write-up we analise the possible introduction of Ethereum delegation at protocol level, in the context of
preserving the canonical chain's financial safety, and we point that there **is** an eODS model that checks both the
proposed functionality and the protocol's safety assumptions._

## Abstract

Enshrining the separation between Delegators and Operators would functionally add delegation in Ethereum, at protocol
level. At the moment of writing, the design is still work in progress, thus, this file might change, as eODS work
progresses.

Prerequisites

| eODS design notes                                  | Link                                  |
|----------------------------------------------------|---------------------------------------|
| Towards enshrining Delegation in Ethereum protocol | https://hackmd.io/@kboomro/rk7RTSbxgx |

---

## Financially accountable delegated balance

In the current eODS design, delegated balance is tracked by the beacon-chain-accounting gadget, but Delegators are not
directly slashable, slashing being applied only to delegated validators. The withdrawable balance of Delegators is,
however, reduced if the validator they delegated to, was slashed. Same logic applies to rewards and penalties, that will
affect delegator's withdrawable balance. This enforces accountability without introducing slashing complexity for
non-operational participants.

This design is potentially suboptimal, especially in the context of a weak subjectivity attack, due to the following
rationale:

- We assume that a rational adversary would compare value of burned stake with the value of the attack and only run the
  attack if the burned value is overcome by the gain that can be obtained from attacking.
- the delegated balance eventually gets destroyed if the delegated validator is slashed, so that counts as negative
  attack efficiency (it's counted in the burned value), but it doesn't protect the protocol from the finalization of two
  conflicting checkpoints.
  Also, the attacker could simply use validators that were not delegated, to attack the network, or undelegate prior to
  the attack.
- even though it can be an efficient deterrent until the period of attack, once the attack is initiated, delegated
  balance doesn't affect adversarial game.

By cumulating delegated balance to the validator's effective balance, the delegated balance would be added as
[PoS weight for the validator, and counted in its rewards, penalties and slashing calculation](https://hackmd.io/ZQocZMA9RyCZNlNHPGMeRg#13-Technical-and-economic-reasons-behind-using-the-effective-balance).

**An important safety condition in this case would be to make sure the delegated balance also becomes financially
accountable
for a certain number of epochs, in the context of weak subjectivity.**

## Actual and Effective Balance under this eODS model

eODS feature proposes the following beacon-chain changes, in order to manage balances (non-exclusive list):

### Actual Validators balance and Actual Delegators balance

- Delegators entities and their not-delegated actual balances, are added as parallel lists in `BeaconState`, alongside
  Validators and Validators actual balances

```python
### Modified containers
class BeaconState(Container):


# Registry
validators: List[Validator, VALIDATOR_REGISTRY_LIMIT]
balances: List[Gwei, VALIDATOR_REGISTRY_LIMIT]
...
# Delegation additions
delegators: List[Delegator, DELEGATOR_REGISTRY_LIMIT]  # [New in EIPXXXX_eODS]
delegators_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]  # [New in EIPXXXX_eODS]
delegated_validators: List[DelegatedValidator, VALIDATOR_REGISTRY_LIMIT]  # [New in EIPXXXX_eODS]
```

- Delegated Validators protocol objects are added as a list of `class DeleegatedValidator` instantiations, inside
  `BeaconState`, where
  `DelegatedValidator` is a wrapper around existing `Validator` protocol entities, that have set their `is_operator`
  attribute to `True`:

```python
### Modified container
class Validator(Container):


    ...
is_operator: boolean  # [New in EIPXXXX_eODS]
fee_quotient: uint64  # [New in EIPXXXX_eODS]
```

Each `DelegatedValidator` keep a registry of their Delegators quotas and delegated balances:

```python
### New container
class DelegatedValidator(Container):


    delegated_validator: Validator
delegated_validator_initial_balance: Gwei
delegated_validator_quota: uint64
delegators_quotas: List[Quota, DELEGATOR_REGISTRY_LIMIT]
delegated_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]
total_delegated_balance: Gwei
```

### Beacon-chain-accounting protocol gadget

Will have the role of an enshrined accounting module that intermediates delegation state transitions during
consensus-layer epoch processing. It is invoked by the protocol during consensus-layer state transitions. It will record
deposits, withdrawals, and balance movements between delegators and delegated validators.

We used the following terminology, above:

- delegators not-delegated actual balance: balance stored in `delegators_balances`. It's idle balance, not yet
  delegated, not considered as stake.
- delegators delegated actual balance: balance stored in `delegated_balances`, inside each `DelegatedValidator`'s
  records. This balance will be cumulated with that particular validator's effective balance and when active in
  consensus, will be considered slashable stake.

### Effective (Validators) balance

The validator effective balance can be modified to the following form:

```python
def process_effective_balance_updates(state: BeaconState) -> None:
    # Update effective balances with hysteresis
    for index, validator in enumerate(state.validators):
        balance = state.balances[index] + state.delegated_validators[
            index].total_delegated_balance  # [Modified in EIPXXXX_eODS]
        ...
```

## WS period calculation for this model (Based on [Electra](https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/weak-subjectivity.md))

### Electra weak subjectivity period calculus (memory refresher)

```
t = get_total_active_balance(state)
    delta = get_balance_churn_limit(state)
    epochs_for_validator_set_churn = SAFETY_DECAY * t // (2 * delta * 100)
    return MIN_VALIDATOR_WITHDRAWABILITY_DELAY + epochs_for_validator_set_churn
```

The formula in the code snippet is equivalent to

$n=\frac{D_0*S}{2d}$,

from [this calculation](https://notes.ethereum.org/@fradamt/maxeb-consolidation#Consolidations-and-churn-limit), where:

- `t` = S = total active balance (see `get_total_active_balance`)


- `SAFETY_DECAY` = $D_0 =\frac{10}{100}$

Post Electra, the per-epoch rate at which stake can enter and exit the system is not a fixed amount of stake, and
instead depends on the total stake $S$:

- churn rate = `delta` = `min(256, max(128, total_active_balance / 65536))`
  which is equivalent to:

- $d_{AE}(S)=min(256,d(S))$, where $d(S)$ is the validator activation rate limit per
  epoch $d(S)=max(128,\frac {S}{2^{16}})$, expressed in stake

### How would Delegation lifecycle affect the network's accountable safety?

For the delegated balance to be financially accountable, delegation lifecycle must preserve the current safety guarantee
that at least $\frac{1}{3} - D(n)$ of the stake will be slashed in case two conflicting checkpoints get finalised.

We're going to base the following calculations on the minimum quorum intersection equation, for two conflicting chains with a most recent common ancestor.

[The general expression is](https://notes.ethereum.org/@fradamt/maxeb-consolidation#Consolidations-and-churn-limit): $min.quorum.intersection = 2 * \frac{2}{3}(S+D)$

#### DELEGATE
A delegation of D stake towards an active validator, implies transferring D amount of a certain delegator's not-yet-delegated actual balance to it's delegated actual balance and cumulating that D stake to the `target` validator's effective balance. 

**Safety implications of Delegate : A delegation of D stake, introduces a safety loss of $\frac{1}{3} * D$, equivalent to an
activation**, since it introduces stake that is free to vote on whatever it wants, and it increases the required voting quorum by $\frac{2}{3} * D$, just like an activation.

Let's see if the math checks out:

The total stake in case of an WS attack becomes $S + 2D$, since the adversary would need to vote on both chains.

The accountable safety equation for a Delegation, becomes:

$min.quorum.intersection - total.stake = 2 * \frac{2}{3}(S+D) - (S + 2D) = \frac{1}{3} * S = \frac{1}{3} * S - \frac{2}{3}*D$,
which is equivalent with the safety loss of an activation (doubled in value because there are two branches). 

#### UNDELEGATE
An Undelegation of U stake from an active validator, implies withdrawing U amount of a certain delegator's delegated actual balance to it's not-yet-delegated actual balance and deducing that U stake from the `target` validator's effective balance. 

**Safety implications of Undelegate : An undelegation of U stake, introduces a safety loss of $\frac{2}{3} * U$, equivalent to an
exit**, since it lowers the required voting quorum on each conflicting branch by $\frac{2}{3} * U$, just like an exit.

Let's see if the math checks out:

The total stake in case of an WS attack remains $S$, since all validators are still active on at least one of the two branches.

The accountable safety equation for an Undelegation, becomes:

$min.quorum.intersection - total.stake = 2 * \frac{2}{3}(S - U) - S  = \frac{1}{3} * S = \frac{1}{3} * S - \frac{4}{3}*U$,
which is equivalent with the safety loss of an exit (doubled in value because there are two branches). 

#### REDELEGATE
A Redelegation of R stake from one active validator towards another active validator, implies deducing an R amount of stake from the `source` validator's effective balance and cumulating that R stake to the `target` validator's effective balance, bypassing the . 

**Safety implications of Delegate : A delegation of D stake, introduces a safety loss of $\frac{1}{3} * D$, equivalent to an
activation**, since it introduces stake that is free to vote on whatever it wants, and it increases the required voting quorum by $\frac{2}{3} * D$, just like an activation.

Let's see if the math checks out:

The total stake in case of an WS attack becomes $S + 2D$, since the adversary would need to vote on both chains.

The accountable safety equation for a Delegation, becomes:

$min.quorum.intersection - total.stake = 2 * \frac{2}{3}(S+D) - (S + 2D) = \frac{1}{3} * S = \frac{1}{3} * S - \frac{2}{3}*D$,
which is equivalent with the safety loss of an activation (doubled in value because there are two branches).
### Delegation churn limit
In Electra, the Churn limit for consolidations is set to $d_C = d(S) - d_{AE}(S)$, which preserves the WS period so that:
$\frac{D_0*S}{2d(S)} = \frac{D_0*S}{2(d_{AE}(S)+d_C(S))}$, reestablishing the symetry between the rate of limitation for exits and activations.

 