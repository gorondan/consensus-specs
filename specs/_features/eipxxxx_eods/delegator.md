# Delegator Extensions for Enhanced eODS

This file defines basic delegator logic used in deposit and withdrawal
and advanced delegator logic used in dynamic re-delegation and validator early-liquidity exits.

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

### priority_exit

```python
def priority_exit(
    state: BeaconState,
    delegator_index: DelegatorIndex,
    validator_index: ValidatorIndex,
    priority_exit_fee: Gwei
) -> Withdrawal:
    """
    Allows a validator to receive early liquidity by borrowing undelegated balance from a delegator.
    The delegator sends a withdrawal to the validator’s withdrawal credentials and receives the fee.

    Preconditions:
    - Delegator has sufficient undelegated balance.
    - Validator is registered and has a pending exit or reduced liquidity.
    """
    assert state.delegators_balances[delegator_index] >= priority_exit_fee

    delegator = state.delegators[delegator_index]
    state.delegators_balances[delegator_index] -= priority_exit_fee

    validator = state.validators[validator_index]
    return Withdrawal(
        index=state.next_withdrawal_index,
        validator_index=validator_index,
        address=validator.withdrawal_credentials,
        amount=priority_exit_fee,
    )
```

### receive_partial_withdrawal

```python
def receive_partial_withdrawal(
    state: BeaconState,
    validator_index: ValidatorIndex,
    amount: Gwei
) -> None:
    """
    Validator-side logic to repay the delegator from its own partial withdrawal stream.

    Preconditions:
    - The validator has exited and is receiving sweepable partial withdrawals.
    - The amount corresponds to a previous `priority_exit`.
    """
    # Logic assumes off-chain tracking or coordination has established repayment terms.
    # The validator’s withdrawal mechanism (e.g., EIP-7002) triggers this on replay.
    pass
```
