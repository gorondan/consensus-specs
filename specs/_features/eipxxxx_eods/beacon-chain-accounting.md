# EIP-XXX_eODS -- Beacon Chain Accounting

## Introduction

*Note:* This specification is built upon [Electra](../../electra/beacon_chain.md) and is under active development.  
This specification defines the accounting logic for eODS (Enshrined Operator-Delegator Separation), responsible for enshrined delegation balances, withdrawal processing, and reward preview computation in the Beacon Chain.

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

### withdraw_to_wallet

```python
def withdraw_to_wallet(state: BeaconState, delegator_index: DelegatorIndex) -> Withdrawal:
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
        delegation_entry_epoch=compute_epoch_at_slot(state.slot),
    )
    state.delegators.append(delegator)
    state.delegators_balances.append(Gwei(0))
    return DelegatorIndex(len(state.delegators) - 1)
```
