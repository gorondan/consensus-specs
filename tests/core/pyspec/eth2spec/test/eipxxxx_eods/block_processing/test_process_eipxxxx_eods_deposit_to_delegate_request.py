from eth2spec.test.context import spec_state_test, expect_assertion_error, \
    with_eipxxxx_eods_and_later
from eth2spec.test.helpers.delegation_deposits import prepare_deposit_to_delegate_request


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_has_valid_signature(spec, state):
    delegator_index = len(state.delegators)
    amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT

    withdrawal_credentials = (
            spec.COMPOUNDING_WITHDRAWAL_PREFIX
            + b'\x00' * 11  # specified 0s
            + b'\x59' * 20  # a 20-byte eth1 address
    )

    deposit_to_delegate = prepare_deposit_to_delegate_request(spec, delegator_index, amount,
                            index=None,
                            pubkey=None,
                            privkey=None,
                            withdrawal_credentials=withdrawal_credentials,
                            signed=True)


    assert spec.is_valid_deposit_to_delegate_signature(
        deposit_to_delegate.pubkey,
        deposit_to_delegate.withdrawal_credentials,
        deposit_to_delegate.amount,
        deposit_to_delegate.signature
    )


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_creates_delegator_if_needed(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_does_top_up_if_needed(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_uses_minimum_deposit_amount(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_uses_minimum_deposit_amount(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_increases_topup_delegator_balance(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_increases_new_delegator_balance(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_respects_churn_value(spec, state):
    assert 1 > 1

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_rolls_over_to_new_epoch_when_over_churn_value(spec, state):
    assert 1 > 1