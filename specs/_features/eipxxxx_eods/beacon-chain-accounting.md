from build.lib.eth2spec.test.helpers.state import get_validator_index_by_pubkeyfrom build.lib.eth2spec.eipxxxx_eods.mainnet import decrease_balancefrom build.lib.eth2spec.fulu.mainnet import BLSPubkeyfrom eth2spec.eipxxxx_eods.mainnet import DelegatorIndex

# EIP-XXX_eODS -- Beacon Chain Accounting

## Introduction

*Note:* This specification is built upon [Electra](../../electra/beacon_chain.md) and is under active development.  
This specification defines the accounting logic for eODS (Enshrined Operator-Delegator Separation), responsible for 
enshrined delegation balances, withdrawal processing, and reward preview computation in the Beacon Chain.

## Delegation Lifecycle Functions

### delegate_to_validator

```python
def delegate_to_validator(state: BeaconState, delegator_index: DelegatorIndex, validator_pubkey: BLSPubkey, delegated_amount: Gwei) -> None:
    # state, delegator_index, validator.pubkey, delegated_amount
    decrease_delegator_balance(state, delegator_index, delegated_amount)
    
    delegated_validator = get_delegated_validator(state, validator_pubkey)

    num_delegated_balances = len(delegated_validator.delegated_balances)

    if(delegator_index > num_delegated_balances):
        for _ in range(delegator_index - num_delegated_balances):
            delegated_validator.delegated_balances.append(0)
            delegated_validator.delegated_quotas.append(0)
    
    delegated_validator.delegated_balances[delegator_index] += delegated_amount
    delegated_validator.total_delegated_balance += delegated_amount

    recalculate_delegators_quotas(state, delegated_validator)

```

### Accounting helper functions

#### New `recalculate_delegators_quotas`
```python
def recalculate_delegators_quotas(state: BeaconState, delegated_validator: DelegatedValidator) -> None:
    validator_index = get_validator_index_by_pubkey(delegated_validator.validator.pubkey)
    
    if delegated_validator.total_delegated_balance == 0:
        delegated_validator.delegated_validator_quota = 1
    else :
        delegated_validator.delegated_validator_quota = (state.balances[validator_index] /  (delegated_validator.total_delegated_balance + state.balances[validator_index]))
        for index in range(len(delegated_validator.delegators_quotas)):
            delegated_validator.delegators_quotas[index] = delegated_validator.delegated_balances[index] / delegated_validator.total_delegated_balance * (1-delegated_validator.delegated_validator_quota)
```

### withdraw_from_validator

```python
def withdraw_from_validator(state: BeaconState, delegator_index: DelegatorIndex, validator_index: ValidatorIndex) -> None:
    delegator = state.delegators[delegator_index]
    delegated_validator = state.delegated_validators[validator_index]

    subindex = delegator_index  # parallel index assumption
    principal = delegated_validator.delegated_balances[subindex]
    validator_balance = state.balances[validator_index]

    delegator_quota = Gwei(0) if validator_balance == 0 else delegated_validator.delegators_quotas[subindex]
    payout = validator_balance * delegator_quota

    fee = payout * delegated_validator.delegated_validator.fee_percentage // 1_000_000
    net_amount = payout - fee

    state.delegators_balances[delegator_index] += net_amount

    delegated_validator.delegated_balances[subindex] = Gwei(0)
    delegated_validator.total_delegated_balance -= principal
    delegator.effective_delegated_balance = Gwei(0)
```
## Advanced Delegation Lifecycle

### fast_redelegate

```python
def fast_redelegate(
    state: BeaconState,
    from_validator_index: ValidatorIndex,
    to_validator_index: ValidatorIndex,
    delegator_index: DelegatorIndex,
    amount: Gwei
) -> None:
    """
    Transfers a portion of delegated stake from one delegated validator to another,
    without requiring full withdrawal to the delegator balance.

    Preconditions:
    - The delegator has sufficient effective_delegated_balance with the `from_validator_index`.
    - Both validators are registered delegated validators.
    - Quotas and delegated_balances are updated in-place.
    - No fees are applied.

    Postconditions:
    - Quotas and balances are adjusted in both validators.
    - Delegator’s effective_delegated_balance remains unchanged.
    """
    assert from_validator_index != to_validator_index
    assert amount > 0

    from_validator = state.delegated_validators[from_validator_index]
    to_validator = state.delegated_validators[to_validator_index]

    # Assume index alignment
    subindex = delegator_index

    assert from_validator.delegated_balances[subindex] >= amount
    from_validator.delegated_balances[subindex] -= amount
    from_validator.total_delegated_balance -= amount

    to_validator.delegated_balances[subindex] += amount
    to_validator.total_delegated_balance += amount

    # Update quota proportionally based on validator's current balance
    to_balance = state.balances[to_validator_index]
    updated_quota = Gwei(0) if to_balance == 0 else amount / to_balance
    to_validator.delegators_quotas[subindex] += updated_quota
```

### fast_withdrawal

```python
def fast_withdrawal(
    state: BeaconState,
    delegator_index: DelegatorIndex,
    validator_index: ValidatorIndex,
    fast_withdrawal_fee: Gwei
) -> Withdrawal:
    """
    Allows a validator to receive early liquidity by borrowing undelegated balance from a delegator.
    The delegator sends a withdrawal to the validator’s withdrawal credentials and receives the fee.

    Preconditions:
    - Delegator has sufficient undelegated balance.
    - Validator is registered and has a pending exit or reduced liquidity.
    """
    assert state.delegators_balances[delegator_index] >= fast_withdrawal_fee

    delegator = state.delegators[delegator_index]
    state.delegators_balances[delegator_index] -= fast_withdrawal_fee

    validator = state.validators[validator_index]
    return Withdrawal(
        index=state.next_withdrawal_index,
        validator_index=validator_index,
        address=validator.withdrawal_credentials,
        amount=fast_withdrawal_fee,
    )
```

### Beacon state mutators

#### New `decrease_delegator_balance`

```python
def decrease_delegator_balance(state: BeaconState, delegator_index: DelegatorIndex, delta: Gwei) -> None:
    """
    Decrease the delegator balance at index ``delegator_index`` by ``delta``.
    """
    state.delegators_balances[delegator_index] -= delta
```
#### New `increase_delegator_balance`

```python
def increase_delegator_balance(state: BeaconState, delegator_index: DelegatorIndex, delta: Gwei) -> None:
    """
    Increase the delegator balance at index ``delegator_index`` by ``delta``.
    """
    state.delegators_balances[delegator_index] += delta
```
