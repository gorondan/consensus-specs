# EIP-XXX_eODS -- Beacon Chain Accounting

## Introduction

*Note:* This specification is built upon [Electra](../../electra/beacon_chain.md) and is under active development.  
This specification defines the accounting logic for eODS (Enshrined Operator-Delegator Separation), responsible for 
enshrined delegation balances, withdrawal processing, and reward preview computation in the Beacon Chain.

## Delegation Lifecycle Functions

### deposit_to_delegator_balance

```python
def deposit_to_delegator_balance(state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32, amount: Gwei) -> None:
    delegator_index = get_delegator_index(state, pubkey)
    if delegator_index is None:
        delegator_index = register_new_delegator(state, pubkey, withdrawal_credentials)
    state.delegators_balances[delegator_index] += amount
```

### compute_pending_rewards

```python
def compute_pending_rewards(state: BeaconState, delegator_index: DelegatorIndex, validator_index: ValidatorIndex) -> Gwei:
    delegated_validator = state.delegated_validators[validator_index]
    validator_balance = state.balances[validator_index]
    quota = delegated_validator.delegators_quotas[delegator_index] if validator_balance > 0 else Gwei(0)

    reward = validator_balance * quota
    fee = reward * delegated_validator.delegated_validator.fee_percentage // 1_000_000

    return reward - fee
```

### withdraw_from_delegator

```python
def withdraw_from_delegator(state: BeaconState, delegator_index: DelegatorIndex) -> Withdrawal:
    amount = state.delegators_balances[delegator_index]
    assert amount > 0

    state.delegators_balances[delegator_index] = Gwei(0)
    delegator = state.delegators[delegator_index]

    return Withdrawal(
        index=state.next_withdrawal_index,
        validator_index=ValidatorIndex(0),  # Placeholder: delegator withdrawal context
        address=delegator.withdrawal_credentials,
        amount=amount,
    )
```

---

## Delegation Helper Functions

```python
def get_delegator_index(state: BeaconState, pubkey: BLSPubkey) -> Optional[DelegatorIndex]:
    for i, d in enumerate(state.delegators):
        if d.pubkey == pubkey:
            return DelegatorIndex(i)
    return None

def register_new_delegator(state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32) -> DelegatorIndex:
    delegator = Delegator(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        effective_delegated_balance=Gwei(0),
        delegator_entry_epoch=compute_epoch_at_slot(state.slot),
    )
    state.delegators.append(delegator)
    state.delegators_balances.append(Gwei(0))
    return DelegatorIndex(len(state.delegators) - 1)
```

## Delegator Extensions for Enhanced eODS

---
This section defines advanced delegator logic used in dynamic re-delegation and validator early-liquidity exits.

### delegate_to_validator

```python
def delegate_to_validator(state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32, validator_index: ValidatorIndex, amount: Gwei) -> None:
    assert amount > 0
    assert validator_index < len(state.delegated_validators)

    delegated_validator = state.delegated_validators[validator_index]
    validator_balance = state.balances[validator_index]

    delegator_index = get_delegator_index(state, pubkey)
    if delegator_index is None:
        delegator_index = register_new_delegator(state, pubkey, withdrawal_credentials)

    assert state.delegators_balances[delegator_index] >= amount
    # balance deduction is already handled in deposit_to_delegator_balance

    delegator = state.delegators[delegator_index]
    delegator.effective_delegated_balance += amount
    delegator.delegation_entry_epoch = compute_epoch_at_slot(state.slot)

    delegated_validator.total_delegated_balance += amount
    delegated_validator.delegated_balances.append(amount)

    quota = Gwei(0) if validator_balance == 0 else amount / validator_balance
    delegated_validator.delegators_quotas.append(quota)
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