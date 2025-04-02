# Delegator Extensions for Enhanced eODS

This file defines advanced delegator logic used in Enhanced eODS, such as dynamic re-delegation and liquidity-driven 
priority exits.

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
    fee: Gwei
) -> Withdrawal:
    """
    Allows a validator to receive early liquidity by borrowing undelegated balance from a delegator.
    The delegator sends a withdrawal to the validator’s withdrawal credentials and receives the fee.

    Preconditions:
    - Delegator has sufficient undelegated balance.
    - Validator is registered and has a pending exit or reduced liquidity.
    """
    assert state.delegators_balances[delegator_index] >= fee

    delegator = state.delegators[delegator_index]
    state.delegators_balances[delegator_index] -= fee

    validator = state.validators[validator_index]
    return Withdrawal(
        index=state.next_withdrawal_index,
        validator_index=validator_index,
        address=validator.withdrawal_credentials,
        amount=fee,
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
